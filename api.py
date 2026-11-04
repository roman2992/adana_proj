from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from database import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Dish, Category, Order, Client, OrderStatus, OrderLine

app = FastAPI()

# Используем Decimal для точной работы с ценами
from decimal import Decimal


class DishIn(BaseModel):
    name: str
    description: str
    price: Decimal  # Изменено с float на Decimal
    mass: float
    category_id: int

class CategoryIn(BaseModel):
    name: str

class CategoryOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class DishOut(BaseModel):
    id: int
    name: str
    description: str
    price: Decimal
    mass: float
    category_id: int

    class Config:
        from_attributes = True


@app.get("/")
async def welcome() -> dict:
    return {"message": "Hello, Adana!"}


@app.get("/dishes/", response_model=list[DishOut])
async def dishes(db: AsyncSession = Depends(get_db)):
    # ИСПРАВЛЕНО: Правильный метод для получения списка объектов в SQLAlchemy 2.0
    result = await db.execute(select(Dish))
    dishes_list = result.scalars().all()

    if not dishes_list:
        raise HTTPException(status_code=404, detail="Dishes not found")

    return dishes_list

@app.get("/categories/", response_model=list[CategoryOut])
async def dishes(db: AsyncSession = Depends(get_db)):
    # ИСПРАВЛЕНО: Правильный метод для получения списка объектов в SQLAlchemy 2.0
    result = await db.execute(select(Category))
    categories_list = result.scalars().all()

    if not categories_list:
        raise HTTPException(status_code=404, detail="Categories not found")

    return categories_list


@app.post("/dishes/", response_model=DishOut)
async def add_dish(
        data: DishIn,
        db: AsyncSession = Depends(get_db)
):
    new_dish = Dish(**data.model_dump())

    db.add(new_dish)
    await db.commit()
    await db.refresh(new_dish)
    return new_dish


@app.post("/categories/", response_model=CategoryOut)
async def add_category(
        data: CategoryIn,
        db: AsyncSession = Depends(get_db)
):
    new_category = Category(**data.model_dump())
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category  # Возвращаем созданный объект обратно клиенту

class ClientIn(BaseModel):
    name: str
    phone: str
    class Config:
        from_attributes = True

class ClientOut(BaseModel):
    id: int
    name: str
    phone: str
    class Config:
        from_attributes = True

@app.post("/clients/", response_model=ClientOut)
async def add_client(
    data: ClientIn,
    db: AsyncSession = Depends(get_db)
):
    new_client = Client(**data.model_dump())
    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)
    return new_client


@app.get("/clients/", response_model=list[ClientOut])
async def clients(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Client))
    clients_list = result.scalars().all()
    return clients_list

class OrderLineIn(BaseModel):
    dish_id: int
    amount: int = Field(gt=0)


class OrderIn(BaseModel):
    address: str
    order_phone_number: str
    client_id: int
    order_lines: list[OrderLineIn] = Field(min_length=1)

@app.post("/orders/", status_code=201)
async def add_order(
        data:OrderIn,
        db:AsyncSession = Depends(get_db)
):
    # 1. Проверяем клиента
    client_result = await db.execute(
        select(Client).where(Client.id == data.client_id)
    )
    client = client_result.scalar_one_or_none()

    if client is None:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    # 2. Получаем статус "Новый"
    status_result = await db.execute(
        select(OrderStatus).where(OrderStatus.name == "Новый")
    )
    new_status = status_result.scalar_one_or_none()

    if new_status is None:
        raise HTTPException(
            status_code=500,
            detail="Order status 'Новый' not found"
        )

    # 3. Получаем блюда из базы
    dish_ids = [line.dish_id for line in data.order_lines]

    dishes_result = await db.execute(
        select(Dish).where(Dish.id.in_(dish_ids))
    )
    dishes = {
        dish.id: dish
        for dish in dishes_result.scalars().all()
    }

    # 4. Проверяем, что все блюда существуют
    for line in data.order_lines:
        if line.dish_id not in dishes:
            raise HTTPException(
                status_code=404,
                detail=f"Dish {line.dish_id} not found"
            )
    # 5. Создаём заказ
    new_order = Order(
        address=data.address,
        order_phone_number=data.order_phone_number,
        client_id=data.client_id,
        created_at=datetime.now(timezone.utc),
        status_id=new_status.id,
        total_price=Decimal("0.00")
    )
    try:
        db.add(new_order)

        # Получаем ID заказа, чтобы записать его в OrderLine
        await db.flush()
        # flush() отправляет SQL-команды в БД и позволяет получить new_order.id,
        # но не завершает транзакцию.

        total_price = Decimal("0.00")

        # 6. Создаём позиции заказа
        for line in data.order_lines:
            dish = dishes[line.dish_id]

            # Сохраняем стоимость всей позиции на момент оформления заказа
            line_price = Decimal(str(dish.price)) * line.amount

            order_line = OrderLine(
                order_id=new_order.id,
                dish_id=dish.id,
                amount=line.amount,
                price=line_price
            )

            db.add(order_line)

            total_price += line_price

        # 7. Сохраняем итоговую сумму
        new_order.total_price = total_price

        await db.commit()
        await db.refresh(new_order)

    except Exception:
        await db.rollback()
        raise

    return new_order


# docker compose logs api --tail 100
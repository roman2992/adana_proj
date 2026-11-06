from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field
from database import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Role, Dish, Category, Order, User, OrderStatus, OrderLine
from security import hash_password, verify_password, create_access_token
from dependencies import current_user

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


class AuthIn(BaseModel):
    phone: str
    password:str = Field(min_length=7)
    role:Role = Role.CUSTOMER
    name: str


@app.post("/auth/register")
async def register(data:AuthIn, db:AsyncSession = Depends(get_db)):
    if await db.scalar(select(User).where(User.phone==data.phone)):
        raise HTTPException(409, "Phone already registered")
    user = User(phone=data.phone,
                password_hash=hash_password(data.password),
                name=data.name,
                role = data.role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {
        "access_token":create_access_token(str(user.id),user.role),
        "user_id":user.id,
        "role":user.role
    }

@app.post("/auth/login")
async def login(data:AuthIn, db:AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.phone==data.phone))
    if not user or not verify_password(data.password,user.password_hash):
        raise HTTPException(401,"Invalid credentials")
    return {
        "access_token": create_access_token(str(user.id), user.role),
        "user_id": user.id,
        "role": user.role
    }

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
    new_client = User(**data.model_dump())
    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)
    return new_client


@app.get("/clients/", response_model=list[ClientOut])
async def clients(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User))
    clients_list = result.scalars().all()
    return clients_list

class OrderLineIn(BaseModel):
    dish_id: int
    amount: int = Field(gt=0)


class OrderIn(BaseModel):
    address: str
    order_phone_number: str
    # client_id: int
    order_lines: list[OrderLineIn] = Field(min_length=1)

@app.post("/orders/", status_code=201)
async def create_order(
    data: OrderIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(current_user),
):
    # Общая стоимость заказа
    total_price = Decimal("0.00")

    # Создаём заказ
    order = Order(
        total_price=total_price,
        address=data.address,
        order_phone_number=data.order_phone_number,
        client_id=user.id,
        status_id=1,
    )

    db.add(order)

    # Получаем ID созданного заказа
    await db.flush()

    # Создаём позиции заказа
    for item in data.order_lines:

        # Находим блюдо
        dish = await db.scalar(
            select(Dish).where(Dish.id == item.dish_id)
        )

        if dish is None:
            raise HTTPException(
                status_code=404,
                detail=f"Dish with id {item.dish_id} not found",
            )

        # Цена одной позиции
        line_total = dish.price * item.amount

        # Добавляем стоимость к общей сумме
        total_price += line_total

        # Создаём OrderLine
        order_line = OrderLine(
            order_id=order.id,
            dish_id=dish.id,
            amount=item.amount,
            price=dish.price,
        )

        db.add(order_line)

    # Записываем итоговую сумму в заказ
    order.total_price = total_price

    # Сохраняем заказ и позиции
    await db.commit()

    # Обновляем данные заказа
    await db.refresh(order)

    return {
        "order_id": order.id,
        "total_price": order.total_price,
        "status_id": order.status_id,
        "message": "Order created successfully",
    }


# docker compose logs api --tail 100
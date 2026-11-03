from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from database import get_db
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Dish, Category, Order

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
    # ИСПРАВЛЕНО: Создаем объект модели SQLAlchemy (Dish), а не Pydantic (DishIn)
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

# @app.post("/orders/", response_model=OrderOut):
#     new_order = Order(OrderOut.model_dump())
#     await db.commit()
#     await db.refresh(new_order)
#     return new_order

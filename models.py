from sqlalchemy import String, ForeignKey, Numeric, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from decimal import Decimal
from typing import List


class Base(DeclarativeBase):
    pass


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    # Связь с блюдами
    dishes: Mapped[List["Dish"]] = relationship(back_populates="category", cascade="all, delete-orphan")


class Dish(Base):
    __tablename__ = "dishes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(String(260))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    mass: Mapped[float] = mapped_column(Float)

    # ВОЗВРАЩАЕМ И СВЯЗЫВАЕМ:
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    category: Mapped["Category"] = relationship(back_populates="dishes")

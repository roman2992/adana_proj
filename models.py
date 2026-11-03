from sqlalchemy import String, ForeignKey, Numeric, Float, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from decimal import Decimal
from typing import List
from datetime import datetime

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

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    adress: Mapped[str] = mapped_column(String(160))
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("status.id"))

class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(100))

class OrderLine(Base):
    __tablename__ = "order_lines"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    amount: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

class OrderStatus(Base):
    __tablename__ = "status"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(55))

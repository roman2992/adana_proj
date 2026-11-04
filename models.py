from sqlalchemy import String, ForeignKey, Numeric, Float, Integer, DateTime, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from decimal import Decimal
from typing import List
from datetime import datetime, timezone

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

    address: Mapped[str] = mapped_column(String(160))
    order_phone_number: Mapped[str] = mapped_column(String(100))

    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                        default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("status.id"))

    client: Mapped["Client"] = relationship(back_populates="orders")
    order_lines: Mapped[List["OrderLine"]] = relationship(back_populates="order")
    order_status: Mapped["OrderStatus"] = relationship()

class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(100))

    orders: Mapped[List["Order"]] = relationship(back_populates="client")

class OrderLine(Base):
    __tablename__ = "order_lines"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    amount: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    dish_id: Mapped[int] = mapped_column(
        ForeignKey("dishes.id")
    )

    dish: Mapped["Dish"] = relationship()
    order: Mapped["Order"] = relationship(back_populates="order_lines")

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_order_line_amount_positive"),
    )

class OrderStatus(Base):
    __tablename__ = "status"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(55))


# создание новой миграции
# docker compose exec api alembic revision --autogenerate -m "add new tables"
# docker compose exec api alembic upgrade head
# docker compose exec api alembic current
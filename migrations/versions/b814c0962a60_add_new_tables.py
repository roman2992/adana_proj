"""add new tables

Revision ID: b814c0962a60
Revises: 8a6859b503e1
Create Date: 2026-11-05 19:04:31.217366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b814c0962a60'
down_revision: Union[str, Sequence[str], None] = '8a6859b503e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Удаляем старый внешний ключ orders -> clients
    op.drop_constraint(
        'orders_client_id_fkey',
        'orders',
        type_='foreignkey'
    )

    # Переименовываем существующую таблицу.
    # Все записи и id сохраняются.
    op.rename_table('clients', 'users')

    # Создаём внешний ключ orders -> users
    op.create_foreign_key(
        'orders_user_id_fkey',
        'orders',
        'users',
        ['client_id'],
        ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Удаляем внешний ключ orders -> users
    op.drop_constraint(
        'orders_user_id_fkey',
        'orders',
        type_='foreignkey'
    )

    # Возвращаем старое имя таблицы
    op.rename_table('users', 'clients')

    # Восстанавливаем старый внешний ключ
    op.create_foreign_key(
        'orders_client_id_fkey',
        'orders',
        'clients',
        ['client_id'],
        ['id']
    )
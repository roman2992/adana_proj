from alembic import op
import sqlalchemy as sa


revision = "4705f106d69a"
down_revision = "b814c0962a60"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_hash", sa.Text(), nullable=True),
    )

    op.add_column(
        "users",
        sa.Column("role", sa.String(length=16), nullable=True),
    )

    # Назначаем существующему тестовому пользователю роль
    op.execute(
        "UPDATE users SET role = 'customer' WHERE role IS NULL"
    )


def downgrade() -> None:
    op.drop_column("users", "role")
    op.drop_column("users", "password_hash")
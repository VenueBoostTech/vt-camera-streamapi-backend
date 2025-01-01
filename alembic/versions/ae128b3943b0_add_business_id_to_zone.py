"""Add business_id to zone

Revision ID: ae128b3943b0
Revises: bb32b88230e1
Create Date: 2025-01-01 17:51:04.675844
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = 'ae128b3943b0'
down_revision: Union[str, None] = 'bb32b88230e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("zones", schema=None) as batch_op:
        batch_op.add_column(sa.Column("business_id", sa.String(), nullable=True))
        batch_op.create_foreign_key(
            "fk_zones_business_id",  # Foreign key name
            "businesses",  # Referenced table
            ["business_id"],  # Local column
            ["id"],  # Referenced column
        )
    # Set `business_id` to NOT NULL after adding the column and foreign key
    op.execute("UPDATE zones SET business_id = 'default_business_id' WHERE business_id IS NULL")  # Replace with your logic
    with op.batch_alter_table("zones", schema=None) as batch_op:
        batch_op.alter_column("business_id", nullable=False)


def downgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("zones", schema=None) as batch_op:
        batch_op.drop_constraint("fk_zones_business_id", type_="foreignkey")
        batch_op.drop_column("business_id")

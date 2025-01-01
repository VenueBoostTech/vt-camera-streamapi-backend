"""Add business_id to properties

Revision ID: 91d3c9f6e4d8
Revises: ae128b3943b0
Create Date: 2025-01-01 18:29:03.203786
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = "91d3c9f6e4d8"
down_revision: Union[str, None] = "ae128b3943b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add the column with a default value (temporary)
    with op.batch_alter_table("properties") as batch_op:
        batch_op.add_column(sa.Column("business_id", sa.String(), nullable=True))

    # Step 2: Set a default value for existing rows
    op.execute("UPDATE properties SET business_id = 'default_business_id' WHERE business_id IS NULL")

    # Step 3: Alter the column to make it NOT NULL
    with op.batch_alter_table("properties") as batch_op:
        batch_op.alter_column("business_id", nullable=False)

    # Step 4: Add the foreign key constraint
    with op.batch_alter_table("properties") as batch_op:
        batch_op.create_foreign_key(
            "fk_properties_business_id",
            "businesses",
            ["business_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    # Reverse the changes
    with op.batch_alter_table("properties") as batch_op:
        batch_op.drop_constraint("fk_properties_business_id", type_="foreignkey")
        batch_op.drop_column("business_id")

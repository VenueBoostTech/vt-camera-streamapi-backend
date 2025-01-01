"""Add business_id to building

Revision ID: 333ec2898a87
Revises: 91d3c9f6e4d8
Create Date: 2025-01-01 19:05:03.539729

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '333ec2898a87'
down_revision = '91d3c9f6e4d8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if the column already exists
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    columns = [column['name'] for column in inspector.get_columns('buildings')]
    if 'business_id' not in columns:
        # Add the business_id column with a default value temporarily
        op.add_column('buildings', sa.Column('business_id', sa.String(), nullable=False, server_default='default-business-id'))
        
        # Drop the default value after the column is added
        with op.batch_alter_table('buildings') as batch_op:
            batch_op.alter_column('business_id', server_default=None)

        # Add the foreign key constraint
        op.create_foreign_key(
            'fk_buildings_business_id',
            'buildings',
            'businesses',
            ['business_id'],
            ['id'],
            ondelete='CASCADE'
        )


def downgrade() -> None:
    # Drop the foreign key constraint
    op.drop_constraint('fk_buildings_business_id', 'buildings', type_='foreignkey')
    
    # Drop the business_id column
    op.drop_column('buildings', 'business_id')

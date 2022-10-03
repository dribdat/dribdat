"""Add user hashword

Revision ID: be2e25e12e69
Revises: 84d8ce8453f3
Create Date: 2022-10-03 23:36:42.867078

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'be2e25e12e69'
down_revision = '84d8ce8453f3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('hashword', sa.String(length=128), nullable=True))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'hashword')

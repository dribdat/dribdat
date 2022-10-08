"""Add hashtags to events and users

Revision ID: 84d8ce8453f3
Revises: 0c5ae11e7666
Create Date: 2022-09-17 08:04:21.745061

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '84d8ce8453f3'
down_revision = '0c5ae11e7666'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('events', sa.Column('hashtags', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('hashword', sa.String(length=128), nullable=True))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('events', 'hashtags')
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'hashword')

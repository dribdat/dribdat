"""Add hashtags to events

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
    op.drop_column('users', 'carddata') # clear card data column
    op.add_column('users', sa.Column('carddata', sa.String(length=255), nullable=True))
    # use socialize command to rebuild image index

def downgrade():
    op.drop_column('events', 'hashtags')

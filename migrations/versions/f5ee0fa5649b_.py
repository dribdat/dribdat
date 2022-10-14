"""empty message

Revision ID: f5ee0fa5649b
Revises: be2e25e12e69
Create Date: 2022-10-14 22:34:24.913193

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5ee0fa5649b'
down_revision = 'be2e25e12e69'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('events', sa.Column('gallery_url', sa.String(length=2048), nullable=True))

def downgrade():
    op.drop_column('events', 'gallery_url')

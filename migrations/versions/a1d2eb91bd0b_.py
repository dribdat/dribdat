"""Removes the Resources table

Revision ID: a1d2eb91bd0b
Revises: 47bfc29a47b4
Create Date: 2024-09-18 12:40:23.269995

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1d2eb91bd0b'
down_revision = '47bfc29a47b4'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('resources')


def downgrade():
    pass

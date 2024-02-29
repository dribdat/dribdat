"""add wishes

Revision ID: 66da53eca449
Revises: 2b948713686c
Create Date: 2024-02-28 19:47:47.043359

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '66da53eca449'
down_revision = '2b948713686c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('my_wishes', sa.UnicodeText(), nullable=True))


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('my_wishes')

"""Add wishes and skills fields

Revision ID: 66da53eca449
Revises: 2e16efec66e4
Create Date: 2025-01-29 23:12:00.00000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '66da53eca449'
down_revision = '2e16efec66e4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('_my_wishes', sa.UnicodeText(), nullable=True))
        batch_op.add_column(sa.Column('_my_skills', sa.UnicodeText(), nullable=True))


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('_my_wishes')
        batch_op.drop_column('_my_skills')

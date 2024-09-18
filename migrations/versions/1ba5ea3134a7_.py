"""Event instructions and resources

Revision ID: 1ba5ea3134a7
Revises: 7c3929047190
Create Date: 2021-05-16 02:00:41.801003

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ba5ea3134a7'
down_revision = '7c3929047190'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('events') as batch_op:
        batch_op.alter_column(
            'resources', new_column_name='instruction'
        )


def downgrade():
    with op.batch_alter_table('events') as batch_op:
        batch_op.alter_column(
            'instruction', new_column_name='resources'
        )

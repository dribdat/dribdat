"""Connect Resources to project instead of user

Revision ID: f8d682598e82
Revises: 0884a8accfad
Create Date: 2021-06-27 21:51:51.861672

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8d682598e82'
down_revision = '0884a8accfad'
branch_labels = None
depends_on = None

new_type = sa.Enum(
                'review',
                'boost',
                'create',
                'update',
                'star',
                name='activity_type')

def upgrade():
    with op.batch_alter_table('activities') as batch_op:
        batch_op.alter_column('name', type_=new_type)


def downgrade():
    pass
    # ### end Alembic commands ##

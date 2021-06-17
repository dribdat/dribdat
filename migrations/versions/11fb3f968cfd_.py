"""empty message

Revision ID: 11fb3f968cfd
Revises: 0884a8accfad
Create Date: 2021-06-17 15:35:47.449119

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '11fb3f968cfd'
down_revision = '0884a8accfad'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('activities') as batch_op:
        # batch_op.drop_constraint('resources', type_='foreignkey')
        batch_op.drop_column('resource_id')


def downgrade():
    with op.batch_alter_table('activities') as batch_op:
        batch_op.add_column(sa.Column('resource_id', sa.INTEGER(), nullable=True))
        batch_op.create_foreign_key('resources', ['resource_id'], ['id'])

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


def upgrade():
    with op.batch_alter_table('activities') as batch_op:
        batch_op.drop_column('resource_id')
    with op.batch_alter_table('resources') as batch_op:
        batch_op.add_column(sa.Column('project_id', sa.Integer(), nullable=True))
        batch_op.drop_constraint('resources', type_='foreignkey')
        batch_op.create_foreign_key('resources', 'projects', ['project_id'], ['id'])
        batch_op.drop_column('summary')
        batch_op.drop_column('event_id')
        batch_op.drop_column('download_url')
        batch_op.drop_column('user_id')


def downgrade():
    with op.batch_alter_table('resources') as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('download_url', sa.VARCHAR(length=2048), nullable=True))
        batch_op.add_column(sa.Column('event_id', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('summary', sa.VARCHAR(length=140), nullable=True))
        batch_op.create_foreign_key('resources', 'events', ['event_id'], ['id'])
        batch_op.create_foreign_key('resources', 'users', ['user_id'], ['id'])
        batch_op.drop_column('project_id')
    with op.batch_alter_table('activities') as batch_op:
        batch_op.add_column(sa.Column('resource_id', sa.INTEGER(), nullable=True))
        batch_op.create_foreign_key('activities', 'resources', ['resource_id'], ['id'])
    # ### end Alembic commands ##

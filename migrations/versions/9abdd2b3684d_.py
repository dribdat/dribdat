"""Users as event managers, add vitae

Revision ID: 9abdd2b3684d
Revises: 47bfc29a47b4
Create Date: 2024-11-10 01:08:45.140917

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9abdd2b3684d'
down_revision = '47bfc29a47b4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('eventuser', 'users', ['user_id'], ['id'])

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('vitae', sa.UnicodeText(), nullable=True))
        batch_op.alter_column('carddata',
            existing_type=sa.VARCHAR(length=255),
            type_=sa.String(length=1024),
            existing_nullable=True)


def downgrade():
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_constraint('eventuser', type_='foreignkey')
        batch_op.drop_column('user_id')

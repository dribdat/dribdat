"""Activity users and project nullable

Revision ID: 30e6fbf01833
Revises: 1ba5ea3134a7
Create Date: 2021-05-25 22:45:17.387052

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '30e6fbf01833'
down_revision = '1ba5ea3134a7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('activities') as batch_op:
        batch_op.add_column(sa.Column('ref_url', sa.String(length=2048), nullable=True))
        batch_op.alter_column('user_id', nullable=True)
        batch_op.alter_column('project_id', nullable=True)


def downgrade():
    with op.batch_alter_table('activities') as batch_op:
        batch_op.alter_column('user_id', nullable=False)
        batch_op.alter_column('project_id', nullable=False)
        batch_op.drop_column('ref_url')

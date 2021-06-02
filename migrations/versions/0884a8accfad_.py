"""Project download URL and field sizes, Event summary field

Revision ID: 0884a8accfad
Revises: 30e6fbf01833
Create Date: 2021-06-02 16:38:43.455112

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0884a8accfad'
down_revision = '30e6fbf01833'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('events') as batch_op:
        batch_op.add_column(sa.Column('summary', sa.String(length=140), nullable=True))
    with op.batch_alter_table('projects') as batch_op:
        batch_op.add_column(sa.Column('download_url', sa.String(length=2048), nullable=True))
        batch_op.alter_column('summary', type_=sa.String(length=140))
        batch_op.alter_column('image_url', type_=sa.String(length=2048))
        batch_op.alter_column('source_url', type_=sa.String(length=2048))
        batch_op.alter_column('contact_url', type_=sa.String(length=2048))


def downgrade():
    with op.batch_alter_table('events') as batch_op:
        batch_op.drop_column('download_url')
    with op.batch_alter_table('projects') as batch_op:
        batch_op.drop_column('summary')

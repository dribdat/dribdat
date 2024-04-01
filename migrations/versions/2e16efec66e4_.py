"""Event aftersubmit, increased hashtag, summary

Revision ID: 2e16efec66e4
Revises: 66da53eca449
Create Date: 2024-03-11 17:00:00.739345

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e16efec66e4'
down_revision = '66da53eca449'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('aftersubmit', sa.UnicodeText(), nullable=True))

    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ident', sa.String(length=10), nullable=True))
        batch_op.alter_column('hashtag',
               existing_type=sa.VARCHAR(length=40),
               type_=sa.String(length=140),
               existing_nullable=True)
        batch_op.alter_column('summary',
               existing_type=sa.VARCHAR(length=140),
               type_=sa.String(length=2048),
               existing_nullable=True)

    with op.batch_alter_table('projects_version', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ident', sa.String(length=10), autoincrement=False, nullable=True))
        batch_op.alter_column('hashtag',
               existing_type=sa.VARCHAR(length=40),
               type_=sa.String(length=140),
               existing_nullable=True,
               autoincrement=False)
        batch_op.alter_column('summary',
               existing_type=sa.VARCHAR(length=140),
               type_=sa.String(length=2048),
               existing_nullable=True,
               autoincrement=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('projects_version', schema=None) as batch_op:
        batch_op.alter_column('summary',
               existing_type=sa.String(length=2048),
               type_=sa.VARCHAR(length=140),
               existing_nullable=True,
               autoincrement=False)
        batch_op.alter_column('hashtag',
               existing_type=sa.String(length=140),
               type_=sa.VARCHAR(length=40),
               existing_nullable=True,
               autoincrement=False)
        batch_op.drop_column('ident')

    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.alter_column('summary',
               existing_type=sa.String(length=2048),
               type_=sa.VARCHAR(length=140),
               existing_nullable=True)
        batch_op.alter_column('hashtag',
               existing_type=sa.String(length=140),
               type_=sa.VARCHAR(length=40),
               existing_nullable=True)
        batch_op.drop_column('ident')

    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_column('aftersubmit')

    # ### end Alembic commands ###

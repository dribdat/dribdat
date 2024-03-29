"""SQLAlchemy Continuum for Projects

Revision ID: 0c5ae11e7666
Revises: f8d682598e82
Create Date: 2022-03-06 21:25:02.136016

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c5ae11e7666'
down_revision = 'f8d682598e82'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('projects_version',
    sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
    sa.Column('name', sa.String(length=80), autoincrement=False, nullable=True),
    sa.Column('summary', sa.String(length=140), autoincrement=False, nullable=True),
    sa.Column('hashtag', sa.String(length=40), autoincrement=False, nullable=True),
    sa.Column('image_url', sa.String(length=2048), autoincrement=False, nullable=True),
    sa.Column('source_url', sa.String(length=2048), autoincrement=False, nullable=True),
    sa.Column('webpage_url', sa.String(length=2048), autoincrement=False, nullable=True),
    sa.Column('contact_url', sa.String(length=2048), autoincrement=False, nullable=True),
    sa.Column('autotext_url', sa.String(length=2048), autoincrement=False, nullable=True),
    sa.Column('download_url', sa.String(length=2048), autoincrement=False, nullable=True),
    sa.Column('is_hidden', sa.Boolean(), autoincrement=False, nullable=True),
    sa.Column('is_webembed', sa.Boolean(), autoincrement=False, nullable=True),
    sa.Column('is_autoupdate', sa.Boolean(), autoincrement=False, nullable=True),
    sa.Column('autotext', sa.UnicodeText(), autoincrement=False, nullable=True),
    sa.Column('longtext', sa.UnicodeText(), autoincrement=False, nullable=True),
    sa.Column('logo_color', sa.String(length=7), autoincrement=False, nullable=True),
    sa.Column('logo_icon', sa.String(length=40), autoincrement=False, nullable=True),
    sa.Column('created_at', sa.DateTime(), autoincrement=False, nullable=True),
    sa.Column('updated_at', sa.DateTime(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.Integer(), autoincrement=False, nullable=True),
    sa.Column('event_id', sa.Integer(), autoincrement=False, nullable=True),
    sa.Column('category_id', sa.Integer(), autoincrement=False, nullable=True),
    sa.Column('progress', sa.Integer(), autoincrement=False, nullable=True),
    sa.Column('score', sa.Integer(), autoincrement=False, nullable=True),
    sa.Column('transaction_id', sa.BigInteger(), autoincrement=False, nullable=False),
    sa.Column('end_transaction_id', sa.BigInteger(), nullable=True),
    sa.Column('operation_type', sa.SmallInteger(), nullable=False),
    sa.PrimaryKeyConstraint('id', 'transaction_id')
    )
    op.create_index(op.f('ix_projects_version_end_transaction_id'), 'projects_version', ['end_transaction_id'], unique=False)
    op.create_index(op.f('ix_projects_version_operation_type'), 'projects_version', ['operation_type'], unique=False)
    op.create_index(op.f('ix_projects_version_transaction_id'), 'projects_version', ['transaction_id'], unique=False)
    op.create_table('transaction',
    sa.Column('issued_at', sa.DateTime(), nullable=True),
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('remote_addr', sa.String(length=50), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transaction_user_id'), 'transaction', ['user_id'], unique=False)
    op.add_column('activities', sa.Column('project_version', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('activities', 'project_version')
    op.drop_index(op.f('ix_transaction_user_id'), table_name='transaction')
    op.drop_table('transaction')
    op.drop_index(op.f('ix_projects_version_transaction_id'), table_name='projects_version')
    op.drop_index(op.f('ix_projects_version_operation_type'), table_name='projects_version')
    op.drop_index(op.f('ix_projects_version_end_transaction_id'), table_name='projects_version')
    op.drop_table('projects_version')
    # ### end Alembic commands ###

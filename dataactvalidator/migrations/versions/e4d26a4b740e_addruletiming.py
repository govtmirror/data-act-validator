"""addRuleTiming

Revision ID: e4d26a4b740e
Revises: 77ce67003a95
Create Date: 2016-03-24 14:24:55.778000

"""

# revision identifiers, used by Alembic.
revision = 'e4d26a4b740e'
down_revision = '77ce67003a95'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_validation():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('rule_timing',
    sa.Column('rule_timing_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('rule_timing_id')
    )
    op.add_column(u'rule', sa.Column('rule_timing_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'rule', 'rule_timing', ['rule_timing_id'], ['rule_timing_id'])
    ### end Alembic commands ###


def downgrade_validation():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'rule', type_='foreignkey')
    op.drop_column(u'rule', 'rule_timing_id')
    op.drop_table('rule_timing')
    ### end Alembic commands ###

"""Minimal voluntary support order ledger; no student account required."""
from alembic import op
import sqlalchemy as sa

revision='7a22cc001010'
down_revision='6e1d86bd1109'
branch_labels=None
depends_on=None

def upgrade():
    op.create_table('support_order',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('order_id',sa.String(80),nullable=False,unique=True),
        sa.Column('receipt',sa.String(40),nullable=False,unique=True),
        sa.Column('guest_hash',sa.String(64),nullable=False),
        sa.Column('key_id',sa.String(80),nullable=False),
        sa.Column('amount',sa.Integer(),nullable=False),
        sa.Column('currency',sa.String(3),nullable=False),
        sa.Column('status',sa.String(16),nullable=False),
        sa.Column('payment_id',sa.String(80),unique=True),
        sa.Column('created_at',sa.Float(),nullable=False))

def downgrade():op.drop_table('support_order')

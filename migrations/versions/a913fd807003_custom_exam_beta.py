"""Track public custom exam quota and cooldowns."""
from datetime import date

from alembic import op
import sqlalchemy as sa

revision = 'a913fd807003'
down_revision = '8b33dd001011'


def upgrade():
    quota = op.create_table(
        'custom_exam_quota',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('questions_used', sa.Integer(), nullable=False),
        sa.Column('starts', sa.Integer(), nullable=False),
        sa.Column('paused', sa.Boolean(), nullable=False),
    )
    op.bulk_insert(quota, [dict(id=1, day=date(1970, 1, 1), questions_used=0, starts=0, paused=False)])
    op.create_table(
        'custom_exam_browser',
        sa.Column('guest_hash', sa.String(64), primary_key=True),
        sa.Column('started_at', sa.Float(), nullable=False),
    )


def downgrade():
    op.drop_table('custom_exam_browser')
    op.drop_table('custom_exam_quota')

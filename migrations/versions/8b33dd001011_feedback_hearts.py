"""Browser-scoped feedback receipts and idempotent review hearts."""
from alembic import op
import sqlalchemy as sa
revision='8b33dd001011'
down_revision='7a22cc001010'
branch_labels=None
depends_on=None

def upgrade():
    op.add_column('contact_message',sa.Column('guest_hash',sa.String(64),nullable=True))
    op.create_index('ix_contact_message_guest_hash','contact_message',['guest_hash'])
    op.create_table('feedback_like',
        sa.Column('feedback_id',sa.Integer(),sa.ForeignKey('contact_message.id',ondelete='CASCADE'),primary_key=True),
        sa.Column('guest_hash',sa.String(64),primary_key=True))
    op.create_index('ix_feedback_like_guest_hash','feedback_like',['guest_hash'])
    if op.get_bind().dialect.name=='postgresql':
        op.execute('ALTER TABLE feedback_like ENABLE ROW LEVEL SECURITY')
        op.execute('REVOKE ALL ON feedback_like FROM PUBLIC')

def downgrade():
    op.drop_table('feedback_like')
    op.drop_index('ix_contact_message_guest_hash',table_name='contact_message')
    op.drop_column('contact_message','guest_hash')

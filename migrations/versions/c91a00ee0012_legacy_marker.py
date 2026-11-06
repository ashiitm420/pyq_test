"""Compatibility marker for a retired feature.

Keep the revision identity so deployed databases can still upgrade. New installs
need no schema for the retired feature. Existing data is left untouched.
"""
revision = 'c91a00ee0012'
down_revision = 'b81deeed0011'
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass

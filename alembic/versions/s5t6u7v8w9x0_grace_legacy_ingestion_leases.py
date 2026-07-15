"""give legacy in-flight ingestion a rollout grace lease

Revision ID: s5t6u7v8w9x0
Revises: r4s5t6u7v8w9
Create Date: 2026-07-15 16:15:00.000000

The previous worker version had no lease columns. During a rolling deploy it
may still be processing a document while the new worker comes online. Give
those rows one hour to complete; if the old worker died, the new worker will
recover the job after that lease expires.
"""

from alembic import op


revision = "s5t6u7v8w9x0"
down_revision = "r4s5t6u7v8w9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        UPDATE document
           SET processing_owner = COALESCE(processing_owner, 'legacy-rollout'),
               lease_expires_at = now() + interval '1 hour',
               last_heartbeat_at = now()
         WHERE status = 'PROCESSING'
           AND lease_expires_at IS NULL
    """)


def downgrade() -> None:
    # Do not clear active lease data on downgrade; it is harmless metadata.
    pass

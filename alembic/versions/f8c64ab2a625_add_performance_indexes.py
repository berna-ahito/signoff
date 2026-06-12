"""add_performance_indexes

Revision ID: f8c64ab2a625
Revises: c466af68377b
Create Date: 2026-06-12 11:34:34.589613

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8c64ab2a625'
down_revision: Union[str, Sequence[str], None] = 'c466af68377b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('idx_requests_requester_id', 'purchase_requests', ['requester_id'])
    op.create_index('idx_requests_status', 'purchase_requests', ['status'])
    op.create_index('idx_requests_created_at', 'purchase_requests', ['created_at'])
    op.create_index('idx_audit_logs_request_id', 'audit_logs', ['request_id'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_refresh_tokens_user_id', table_name='refresh_tokens')
    op.drop_index('idx_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('idx_audit_logs_request_id', table_name='audit_logs')
    op.drop_index('idx_requests_created_at', table_name='purchase_requests')
    op.drop_index('idx_requests_status', table_name='purchase_requests')
    op.drop_index('idx_requests_requester_id', table_name='purchase_requests')

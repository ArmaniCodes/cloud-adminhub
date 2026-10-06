"""make user_id and actor_user_id nullifiable

Revision ID: 7fd04a2937e7
Revises: 81ff1c79c551
Create Date: 2026-10-05 21:38:06.522963

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7fd04a2937e7'
down_revision: Union[str, Sequence[str], None] = '81ff1c79c551'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'audit_logs',
        'actor_user_id',
        existing_type=sa.INTEGER(),
        nullable=True
    )

    op.drop_constraint(
        op.f('audit_logs_actor_user_id_fkey'),
        'audit_logs',
        type_='foreignkey'
    )

    op.create_foreign_key(
        'fk_audit_logs_actor_user_id',
        'audit_logs',
        'users',
        ['actor_user_id'],
        ['id'],
        ondelete='SET NULL'
    )

    op.drop_constraint(
        op.f('refresh_tokens_user_id_fkey'),
        'refresh_tokens',
        type_='foreignkey'
    )

    op.create_foreign_key(
        'fk_refresh_tokens_user_id',
        'refresh_tokens',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'fk_refresh_tokens_user_id',
        'refresh_tokens',
        type_='foreignkey'
    )

    op.create_foreign_key(
        'refresh_tokens_user_id_fkey',
        'refresh_tokens',
        'users',
        ['user_id'],
        ['id']
    )

    op.drop_constraint(
        'fk_audit_logs_actor_user_id',
        'audit_logs',
        type_='foreignkey'
    )

    op.create_foreign_key(
        'audit_logs_actor_user_id_fkey',
        'audit_logs',
        'users',
        ['actor_user_id'],
        ['id']
    )

    op.alter_column(
        'audit_logs',
        'actor_user_id',
        existing_type=sa.INTEGER(),
        nullable=False
    )

"""add target_role and seniority to resume_analysis

Revision ID: 004_add_review_context_columns
Revises: 003_add_chat_sessions
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "004_add_review_context_columns"
down_revision = "003_add_chat_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable: existing reviews were general reviews with no role or level.
    op.add_column("resume_analysis", sa.Column("target_role", sa.String(100), nullable=True))
    op.add_column("resume_analysis", sa.Column("seniority", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("resume_analysis", "seniority")
    op.drop_column("resume_analysis", "target_role")

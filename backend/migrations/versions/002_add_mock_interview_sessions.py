"""add mock_interview_sessions table

Revision ID: 002_add_mock_interview_sessions
Revises: 001_add_oauth_columns
Create Date: 2026-06-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "002_add_mock_interview_sessions"
down_revision = "001_add_oauth_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mock_interview_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("resume_id", sa.Integer(), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("questions", JSONB(), nullable=False, server_default="[]"),
        sa.Column("turns", JSONB(), nullable=False, server_default="[]"),
        sa.Column("current_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_mock_interview_sessions_user_id", "mock_interview_sessions", ["user_id"])
    op.create_index("ix_mock_interview_sessions_resume_id", "mock_interview_sessions", ["resume_id"])


def downgrade() -> None:
    op.drop_index("ix_mock_interview_sessions_resume_id", table_name="mock_interview_sessions")
    op.drop_index("ix_mock_interview_sessions_user_id", table_name="mock_interview_sessions")
    op.drop_table("mock_interview_sessions")

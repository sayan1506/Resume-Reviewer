"""Add OAuth columns to users table

Revision ID: 001_add_oauth_columns
Revises: None
Create Date: 2024-01-01 00:00:00.000000

This migration adds Google OAuth support columns to the users table:
- google_id: VARCHAR(255), UNIQUE, nullable, indexed
- avatar_url: TEXT, nullable
- auth_provider: VARCHAR(50), default 'email'
- Alters password column to nullable=True
- Sets existing rows to have auth_provider='email'
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_add_oauth_columns'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add google_id column: VARCHAR(255), UNIQUE, nullable, indexed
    op.add_column('users', sa.Column('google_id', sa.String(255), nullable=True))
    op.create_unique_constraint('uq_users_google_id', 'users', ['google_id'])
    op.create_index('ix_users_google_id', 'users', ['google_id'])

    # Add avatar_url column: TEXT, nullable
    op.add_column('users', sa.Column('avatar_url', sa.Text(), nullable=True))

    # Add auth_provider column: VARCHAR(50), default 'email'
    op.add_column('users', sa.Column('auth_provider', sa.String(50), nullable=False, server_default='email'))

    # Alter password column to allow NULL (for OAuth-only users)
    op.alter_column('users', 'password',
                    existing_type=sa.String(),
                    nullable=True)

    # Set default auth_provider='email' for existing rows
    op.execute("UPDATE users SET auth_provider = 'email' WHERE auth_provider IS NULL")


def downgrade() -> None:
    # Revert password column to NOT NULL
    # Note: This will fail if any OAuth-only users exist with NULL passwords
    op.alter_column('users', 'password',
                    existing_type=sa.String(),
                    nullable=False)

    # Remove auth_provider column
    op.drop_column('users', 'auth_provider')

    # Remove avatar_url column
    op.drop_column('users', 'avatar_url')

    # Remove google_id column (index and constraint are dropped automatically)
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_constraint('uq_users_google_id', 'users', type_='unique')
    op.drop_column('users', 'google_id')

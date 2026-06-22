"""add conversation sessions

Revision ID: 9d2f0ac9d4c1
Revises: 0b7fc4eea262
Create Date: 2026-06-21 18:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9d2f0ac9d4c1"
down_revision: str | Sequence[str] | None = "0b7fc4eea262"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversation_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversation_sessions_workspace_updated",
        "conversation_sessions",
        ["workspace_id", "updated_at"],
        unique=False,
    )
    with op.batch_alter_table("conversation_messages") as batch_op:
        batch_op.add_column(sa.Column("session_id", sa.String(length=36), nullable=True))
        batch_op.add_column(
            sa.Column(
                "attached_document_ids",
                sa.JSON(),
                server_default="[]",
                nullable=False,
            )
        )
        batch_op.create_foreign_key(
            "fk_conversation_messages_session",
            "conversation_sessions",
            ["session_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_conversation_messages_session",
            ["session_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("conversation_messages") as batch_op:
        batch_op.drop_index("ix_conversation_messages_session")
        batch_op.drop_constraint(
            "fk_conversation_messages_session",
            type_="foreignkey",
        )
        batch_op.drop_column("attached_document_ids")
        batch_op.drop_column("session_id")
    op.drop_index(
        "ix_conversation_sessions_workspace_updated",
        table_name="conversation_sessions",
    )
    op.drop_table("conversation_sessions")

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=500), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refresh_tokens_id"), "refresh_tokens", ["id"], unique=False)
    op.create_index(op.f("ix_refresh_tokens_token"), "refresh_tokens", ["token"], unique=True)
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)

    op.drop_index(op.f("ix_rsvps_email"), table_name="rsvps")
    op.drop_constraint("uq_rsvp_event_email", "rsvps", type_="unique")

    op.drop_column("rsvps", "name")
    op.drop_column("rsvps", "email")

    op.add_column("rsvps", sa.Column("user_id", sa.Integer(), nullable=False))
    op.add_column("rsvps", sa.Column("status", sa.String(length=20), nullable=False, server_default="going"))
    op.add_column("rsvps", sa.Column("checked_in", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("rsvps", sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "rsvps",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_foreign_key("fk_rsvps_user_id", "rsvps", "users", ["user_id"], ["id"], ondelete="CASCADE")
    op.create_unique_constraint("uq_rsvp_event_user", "rsvps", ["event_id", "user_id"])
    op.create_index(op.f("ix_rsvps_user_id"), "rsvps", ["user_id"], unique=False)

    op.add_column("events", sa.Column("organizer_id", sa.Integer(), nullable=False))
    op.add_column("events", sa.Column("capacity", sa.Integer(), nullable=True))
    op.add_column("events", sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"))

    op.create_foreign_key("fk_events_organizer_id", "events", "users", ["organizer_id"], ["id"], ondelete="CASCADE")
    op.create_index(op.f("ix_events_organizer_id"), "events", ["organizer_id"], unique=False)

    op.create_table(
        "event_invitations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("invited_by", sa.Integer(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "email", name="uq_invitation_event_email"),
    )
    op.create_index(op.f("ix_event_invitations_id"), "event_invitations", ["id"], unique=False)
    op.create_index(op.f("ix_event_invitations_email"), "event_invitations", ["email"], unique=False)
    op.create_index(op.f("ix_event_invitations_event_id"), "event_invitations", ["event_id"], unique=False)
    op.create_index(op.f("ix_event_invitations_invited_by"), "event_invitations", ["invited_by"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_event_invitations_invited_by"), table_name="event_invitations")
    op.drop_index(op.f("ix_event_invitations_event_id"), table_name="event_invitations")
    op.drop_index(op.f("ix_event_invitations_email"), table_name="event_invitations")
    op.drop_index(op.f("ix_event_invitations_id"), table_name="event_invitations")
    op.drop_table("event_invitations")

    op.drop_index(op.f("ix_events_organizer_id"), table_name="events")
    op.drop_constraint("fk_events_organizer_id", "events", type_="foreignkey")
    op.drop_column("events", "is_public")
    op.drop_column("events", "capacity")
    op.drop_column("events", "organizer_id")

    op.drop_index(op.f("ix_rsvps_user_id"), table_name="rsvps")
    op.drop_constraint("uq_rsvp_event_user", "rsvps", type_="unique")
    op.drop_constraint("fk_rsvps_user_id", "rsvps", type_="foreignkey")
    op.drop_column("rsvps", "updated_at")
    op.drop_column("rsvps", "checked_in_at")
    op.drop_column("rsvps", "checked_in")
    op.drop_column("rsvps", "status")
    op.drop_column("rsvps", "user_id")

    op.add_column("rsvps", sa.Column("name", sa.String(length=255), nullable=False))
    op.add_column("rsvps", sa.Column("email", sa.String(length=320), nullable=False))
    op.create_unique_constraint("uq_rsvp_event_email", "rsvps", ["event_id", "email"])
    op.create_index(op.f("ix_rsvps_email"), "rsvps", ["email"], unique=False)

    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_token"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

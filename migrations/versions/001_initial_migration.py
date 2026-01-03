from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(length=500), nullable=False),
        sa.Column("flyer_filename", sa.String(length=255), nullable=True),
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
    op.create_index(op.f("ix_events_id"), "events", ["id"], unique=False)

    op.create_table(
        "rsvps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "email", name="uq_rsvp_event_email"),
    )
    op.create_index(op.f("ix_rsvps_email"), "rsvps", ["email"], unique=False)
    op.create_index(op.f("ix_rsvps_event_id"), "rsvps", ["event_id"], unique=False)
    op.create_index(op.f("ix_rsvps_id"), "rsvps", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_rsvps_id"), table_name="rsvps")
    op.drop_index(op.f("ix_rsvps_event_id"), table_name="rsvps")
    op.drop_index(op.f("ix_rsvps_email"), table_name="rsvps")
    op.drop_table("rsvps")
    op.drop_index(op.f("ix_events_id"), table_name="events")
    op.drop_table("events")

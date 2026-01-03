from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from application.utilities.database import Base

if TYPE_CHECKING:
    from application.models.event import Event
    from application.models.user import User


class EventInvitation(Base):
    __tablename__ = "event_invitations"
    __table_args__ = (
        UniqueConstraint("event_id", "email", name="uq_invitation_event_email"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    invited_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    event: Mapped["Event"] = relationship("Event", back_populates="invitations")
    inviter: Mapped["User"] = relationship("User", back_populates="invitations_sent")

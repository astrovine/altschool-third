from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from application.utilities.database import Base

if TYPE_CHECKING:
    from application.models.event import Event
    from application.models.user import User


class RSVPStatus(str, Enum):
    GOING = "going"
    MAYBE = "maybe"
    NOT_GOING = "not_going"


class RSVP(Base):
    __tablename__ = "rsvps"
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_rsvp_event_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[RSVPStatus] = mapped_column(
        String(20),
        default=RSVPStatus.GOING,
        nullable=False,
    )
    checked_in: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    event: Mapped["Event"] = relationship("Event", back_populates="rsvps")
    user: Mapped["User"] = relationship("User", back_populates="rsvps")

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from application.utilities.database import Base

if TYPE_CHECKING:
    from application.models.invitation import EventInvitation
    from application.models.rsvp import RSVP
    from application.models.user import User


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    organizer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str] = mapped_column(String(500), nullable=False)
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    flyer_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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

    organizer: Mapped["User"] = relationship("User", back_populates="events")
    rsvps: Mapped[List["RSVP"]] = relationship(
        "RSVP",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invitations: Mapped[List["EventInvitation"]] = relationship(
        "EventInvitation",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def going_count(self) -> int:
        from application.models.rsvp import RSVPStatus
        return sum(1 for rsvp in self.rsvps if rsvp.status == RSVPStatus.GOING)

    @property
    def is_at_capacity(self) -> bool:
        if self.capacity is None:
            return False
        return self.going_count >= self.capacity

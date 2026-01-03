from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from application.utilities.database import Base

if TYPE_CHECKING:
    from application.models.event import Event
    from application.models.invitation import EventInvitation
    from application.models.refresh_token import RefreshToken
    from application.models.rsvp import RSVP


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        String(20),
        default=UserRole.USER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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

    events: Mapped[List["Event"]] = relationship(
        "Event",
        back_populates="organizer",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    rsvps: Mapped[List["RSVP"]] = relationship(
        "RSVP",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invitations_sent: Mapped[List["EventInvitation"]] = relationship(
        "EventInvitation",
        back_populates="inviter",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

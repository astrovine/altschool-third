from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from application.schemas.user import UserResponse


class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    date: datetime
    location: str = Field(..., min_length=1, max_length=500)


class EventCreate(EventBase):
    capacity: Optional[int] = Field(None, ge=1)
    is_public: bool = True


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    date: Optional[datetime] = None
    location: Optional[str] = Field(None, min_length=1, max_length=500)
    capacity: Optional[int] = Field(None, ge=1)
    is_public: Optional[bool] = None


class EventResponse(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organizer_id: int
    capacity: Optional[int] = None
    flyer_filename: Optional[str] = None
    flyer_url: Optional[str] = None
    is_public: bool
    created_at: datetime
    updated_at: datetime
    going_count: int = 0
    rsvp_count: int = 0


class EventDetailResponse(EventResponse):
    organizer: UserResponse


class EventListResponse(BaseModel):
    events: List[EventResponse]
    total: int
    page: int
    per_page: int
    pages: int


class EventSearchParams(BaseModel):
    q: Optional[str] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    location: Optional[str] = None
    is_public: Optional[bool] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
    sort_by: str = Field("date", pattern="^(date|title|created_at)$")
    order: str = Field("desc", pattern="^(asc|desc)$")

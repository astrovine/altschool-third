from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from application.models.rsvp import RSVPStatus
from application.schemas.user import UserResponse


class RSVPCreate(BaseModel):
    status: RSVPStatus = RSVPStatus.GOING


class RSVPUpdate(BaseModel):
    status: RSVPStatus


class RSVPResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    user_id: int
    status: RSVPStatus
    checked_in: bool
    checked_in_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class RSVPDetailResponse(RSVPResponse):
    user: UserResponse


class RSVPListResponse(BaseModel):
    rsvps: List[RSVPDetailResponse]
    total: int
    event_id: int
    page: int
    per_page: int


class CheckInRequest(BaseModel):
    user_id: int = Field(..., gt=0)

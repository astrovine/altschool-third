from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class InvitationCreate(BaseModel):
    emails: List[EmailStr] = Field(..., min_length=1, max_length=100)


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    email: str
    invited_by: int
    accepted_at: Optional[datetime] = None
    created_at: datetime


class InvitationListResponse(BaseModel):
    invitations: List[InvitationResponse]
    total: int
    event_id: int

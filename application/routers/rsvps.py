from typing import Annotated

from fastapi import APIRouter, Depends, Form, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.schemas.rsvp import RSVPCreate, RSVPListResponse, RSVPResponse
from application.services.rsvp_service import rsvp_service
from application.utilities.database import get_db


router = APIRouter(prefix="/events", tags=["RSVPs"])


@router.post(
    "/{event_id}/rsvp",
    response_model=RSVPResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_rsvp(
    event_id: Annotated[int, Path(gt=0)],
    name: Annotated[str, Form(...)],
    email: Annotated[str, Form(...)],
    db: AsyncSession = Depends(get_db),
) -> RSVPResponse:
    rsvp_data = RSVPCreate(name=name, email=email)
    rsvp = await rsvp_service.create_rsvp(db, event_id, rsvp_data)

    return RSVPResponse(
        id=rsvp.id,
        event_id=rsvp.event_id,
        name=rsvp.name,
        email=rsvp.email,
        created_at=rsvp.created_at,
    )


@router.get(
    "/{event_id}/rsvps",
    response_model=RSVPListResponse,
)
async def list_event_rsvps(
    event_id: Annotated[int, Path(gt=0)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    db: AsyncSession = Depends(get_db),
) -> RSVPListResponse:
    rsvps, total = await rsvp_service.get_rsvps_by_event(db, event_id, skip, limit)

    return RSVPListResponse(
        rsvps=[
            RSVPResponse(
                id=rsvp.id,
                event_id=rsvp.event_id,
                name=rsvp.name,
                email=rsvp.email,
                created_at=rsvp.created_at,
            )
            for rsvp in rsvps
        ],
        total=total,
        event_id=event_id,
    )

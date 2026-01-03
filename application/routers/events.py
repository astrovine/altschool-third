from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.schemas.event import EventCreate, EventListResponse, EventResponse
from application.services.event_service import event_service
from application.services.file_service import file_service
from application.utilities.database import get_db


router = APIRouter(prefix="/events", tags=["Events"])


@router.post(
    "/",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    request: Request,
    title: Annotated[str, Form(...)],
    description: Annotated[str, Form(...)],
    date: Annotated[datetime, Form(...)],
    location: Annotated[str, Form(...)],
    flyer: Annotated[Optional[UploadFile], File()] = None,
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    flyer_filename: Optional[str] = None
    if flyer and flyer.filename:
        flyer_filename = await file_service.save_upload(flyer)

    event_data = EventCreate(
        title=title,
        description=description,
        date=date,
        location=location,
    )

    event = await event_service.create_event(db, event_data, flyer_filename)
    base_url = str(request.base_url).rstrip("/")

    return EventResponse(
        id=event.id,
        title=event.title,
        description=event.description,
        date=event.date,
        location=event.location,
        flyer_filename=event.flyer_filename,
        flyer_url=file_service.get_file_url(event.flyer_filename, base_url),
        created_at=event.created_at,
        updated_at=event.updated_at,
        rsvp_count=len(event.rsvps) if event.rsvps else 0,
    )


@router.get(
    "/",
    response_model=EventListResponse,
)
async def list_events(
    request: Request,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    db: AsyncSession = Depends(get_db),
) -> EventListResponse:
    events, total = await event_service.get_events(db, skip, limit)
    base_url = str(request.base_url).rstrip("/")

    return EventListResponse(
        events=[
            EventResponse(
                id=event.id,
                title=event.title,
                description=event.description,
                date=event.date,
                location=event.location,
                flyer_filename=event.flyer_filename,
                flyer_url=file_service.get_file_url(event.flyer_filename, base_url),
                created_at=event.created_at,
                updated_at=event.updated_at,
                rsvp_count=len(event.rsvps) if event.rsvps else 0,
            )
            for event in events
        ],
        total=total,
    )

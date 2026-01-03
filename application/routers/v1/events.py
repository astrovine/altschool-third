from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.user import User
from application.schemas.event import (
    EventCreate,
    EventDetailResponse,
    EventListResponse,
    EventResponse,
    EventSearchParams,
    EventUpdate,
)
from application.services.event_service import event_service
from application.services.file_service import file_service
from application.utilities.database import get_db
from application.utilities.dependencies import get_current_user
from application.utilities.exceptions import (
    EventNotFoundException,
    FileUploadException,
    NotEventOrganizerException,
)
from application.utilities.logging import logger


router = APIRouter(prefix="/events", tags=["Events"])


@router.post(
    "/",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    title: Annotated[str, Form(...)],
    description: Annotated[str, Form(...)],
    date: Annotated[datetime, Form(...)],
    location: Annotated[str, Form(...)],
    capacity: Annotated[Optional[int], Form()] = None,
    is_public: Annotated[bool, Form()] = True,
    flyer: Annotated[Optional[UploadFile], File()] = None,
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    try:
        flyer_filename: Optional[str] = None
        if flyer and flyer.filename:
            flyer_filename = await file_service.save_upload(flyer)

        event_data = EventCreate(
            title=title,
            description=description,
            date=date,
            location=location,
            capacity=capacity,
            is_public=is_public,
        )

        event = await event_service.create_event(db, event_data, current_user.id, flyer_filename)
        base_url = str(request.base_url).rstrip("/")

        return EventResponse(
            id=event.id,
            organizer_id=event.organizer_id,
            title=event.title,
            description=event.description,
            date=event.date,
            location=event.location,
            capacity=event.capacity,
            flyer_filename=event.flyer_filename,
            flyer_url=file_service.get_file_url(event.flyer_filename, base_url),
            is_public=event.is_public,
            created_at=event.created_at,
            updated_at=event.updated_at,
            going_count=event_service.get_going_count(event),
            rsvp_count=len(event.rsvps) if event.rsvps else 0,
        )
    except FileUploadException:
        raise
    except Exception as e:
        logger.error(f"Event creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Event creation failed. Please try again.",
        )


@router.get(
    "/",
    response_model=EventListResponse,
)
async def list_events(
    request: Request,
    q: Annotated[Optional[str], Query()] = None,
    from_date: Annotated[Optional[datetime], Query()] = None,
    to_date: Annotated[Optional[datetime], Query()] = None,
    location: Annotated[Optional[str], Query()] = None,
    is_public: Annotated[Optional[bool], Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    sort_by: Annotated[str, Query(pattern="^(date|title|created_at)$")] = "date",
    order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    db: AsyncSession = Depends(get_db),
) -> EventListResponse:
    try:
        params = EventSearchParams(
            q=q,
            from_date=from_date,
            to_date=to_date,
            location=location,
            is_public=is_public,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            order=order,
        )

        events, total = await event_service.get_events(db, params)
        base_url = str(request.base_url).rstrip("/")
        pages = (total + per_page - 1) // per_page if total > 0 else 1

        return EventListResponse(
            events=[
                EventResponse(
                    id=event.id,
                    organizer_id=event.organizer_id,
                    title=event.title,
                    description=event.description,
                    date=event.date,
                    location=event.location,
                    capacity=event.capacity,
                    flyer_filename=event.flyer_filename,
                    flyer_url=file_service.get_file_url(event.flyer_filename, base_url),
                    is_public=event.is_public,
                    created_at=event.created_at,
                    updated_at=event.updated_at,
                    going_count=event_service.get_going_count(event),
                    rsvp_count=len(event.rsvps) if event.rsvps else 0,
                )
                for event in events
            ],
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )
    except Exception as e:
        logger.error(f"Event listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch events. Please try again.",
        )


@router.get(
    "/{event_id}",
    response_model=EventDetailResponse,
)
async def get_event(
    request: Request,
    event_id: int,
    db: AsyncSession = Depends(get_db),
) -> EventDetailResponse:
    try:
        event = await event_service.get_event_by_id(db, event_id)
        base_url = str(request.base_url).rstrip("/")

        from application.schemas.user import UserResponse

        return EventDetailResponse(
            id=event.id,
            organizer_id=event.organizer_id,
            title=event.title,
            description=event.description,
            date=event.date,
            location=event.location,
            capacity=event.capacity,
            flyer_filename=event.flyer_filename,
            flyer_url=file_service.get_file_url(event.flyer_filename, base_url),
            is_public=event.is_public,
            created_at=event.created_at,
            updated_at=event.updated_at,
            going_count=event_service.get_going_count(event),
            rsvp_count=len(event.rsvps) if event.rsvps else 0,
            organizer=UserResponse.model_validate(event.organizer),
        )
    except EventNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Event retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch event. Please try again.",
        )


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
)
async def update_event(
    request: Request,
    event_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    title: Annotated[Optional[str], Form()] = None,
    description: Annotated[Optional[str], Form()] = None,
    date: Annotated[Optional[datetime], Form()] = None,
    location: Annotated[Optional[str], Form()] = None,
    capacity: Annotated[Optional[int], Form()] = None,
    is_public: Annotated[Optional[bool], Form()] = None,
    flyer: Annotated[Optional[UploadFile], File()] = None,
    db: AsyncSession = Depends(get_db),
) -> EventResponse:
    try:
        flyer_filename: Optional[str] = None
        if flyer and flyer.filename:
            flyer_filename = await file_service.save_upload(flyer)

        event_data = EventUpdate(
            title=title,
            description=description,
            date=date,
            location=location,
            capacity=capacity,
            is_public=is_public,
        )

        event = await event_service.update_event(db, event_id, event_data, current_user, flyer_filename)
        base_url = str(request.base_url).rstrip("/")

        return EventResponse(
            id=event.id,
            organizer_id=event.organizer_id,
            title=event.title,
            description=event.description,
            date=event.date,
            location=event.location,
            capacity=event.capacity,
            flyer_filename=event.flyer_filename,
            flyer_url=file_service.get_file_url(event.flyer_filename, base_url),
            is_public=event.is_public,
            created_at=event.created_at,
            updated_at=event.updated_at,
            going_count=event_service.get_going_count(event),
            rsvp_count=len(event.rsvps) if event.rsvps else 0,
        )
    except (EventNotFoundException, NotEventOrganizerException, FileUploadException):
        raise
    except Exception as e:
        logger.error(f"Event update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Event update failed. Please try again.",
        )


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_event(
    event_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await event_service.delete_event(db, event_id, current_user)
    except (EventNotFoundException, NotEventOrganizerException):
        raise
    except Exception as e:
        logger.error(f"Event deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Event deletion failed. Please try again.",
        )

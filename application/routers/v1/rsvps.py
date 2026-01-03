from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.user import User
from application.schemas.rsvp import (
    CheckInRequest,
    RSVPCreate,
    RSVPDetailResponse,
    RSVPListResponse,
    RSVPResponse,
)
from application.schemas.user import UserResponse
from application.services.rsvp_service import rsvp_service
from application.utilities.database import get_db
from application.utilities.dependencies import get_current_user
from application.utilities.exceptions import (
    EventAtCapacityException,
    EventNotFoundException,
    NotEventOrganizerException,
    RSVPNotFoundException,
)
from application.utilities.logging import logger


router = APIRouter(prefix="/events/{event_id}", tags=["RSVPs"])


@router.post(
    "/rsvp",
    response_model=RSVPResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_rsvp(
    event_id: Annotated[int, Path(gt=0)],
    rsvp_data: RSVPCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> RSVPResponse:
    try:
        rsvp = await rsvp_service.create_or_update_rsvp(db, event_id, current_user, rsvp_data)

        return RSVPResponse(
            id=rsvp.id,
            event_id=rsvp.event_id,
            user_id=rsvp.user_id,
            status=rsvp.status,
            checked_in=rsvp.checked_in,
            checked_in_at=rsvp.checked_in_at,
            created_at=rsvp.created_at,
            updated_at=rsvp.updated_at,
        )
    except (EventNotFoundException, EventAtCapacityException):
        raise
    except Exception as e:
        logger.error(f"RSVP creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RSVP failed. Please try again.",
        )


@router.get(
    "/rsvps",
    response_model=RSVPListResponse,
)
async def list_event_rsvps(
    event_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    db: AsyncSession = Depends(get_db),
) -> RSVPListResponse:
    try:
        rsvps, total = await rsvp_service.get_rsvps_by_event(
            db, event_id, current_user, page, per_page
        )

        return RSVPListResponse(
            rsvps=[
                RSVPDetailResponse(
                    id=rsvp.id,
                    event_id=rsvp.event_id,
                    user_id=rsvp.user_id,
                    status=rsvp.status,
                    checked_in=rsvp.checked_in,
                    checked_in_at=rsvp.checked_in_at,
                    created_at=rsvp.created_at,
                    updated_at=rsvp.updated_at,
                    user=UserResponse.model_validate(rsvp.user),
                )
                for rsvp in rsvps
            ],
            total=total,
            event_id=event_id,
            page=page,
            per_page=per_page,
        )
    except (EventNotFoundException, NotEventOrganizerException):
        raise
    except Exception as e:
        logger.error(f"RSVP listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch RSVPs. Please try again.",
        )


@router.get(
    "/rsvps/me",
    response_model=RSVPResponse,
)
async def get_my_rsvp(
    event_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> RSVPResponse:
    try:
        rsvp = await rsvp_service.get_user_rsvp(db, event_id, current_user.id)
        if not rsvp:
            raise RSVPNotFoundException(event_id)

        return RSVPResponse(
            id=rsvp.id,
            event_id=rsvp.event_id,
            user_id=rsvp.user_id,
            status=rsvp.status,
            checked_in=rsvp.checked_in,
            checked_in_at=rsvp.checked_in_at,
            created_at=rsvp.created_at,
            updated_at=rsvp.updated_at,
        )
    except RSVPNotFoundException:
        raise
    except Exception as e:
        logger.error(f"RSVP retrieval failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch RSVP. Please try again.",
        )


@router.delete(
    "/rsvp",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_rsvp(
    event_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await rsvp_service.delete_rsvp(db, event_id, current_user)
    except (EventNotFoundException, RSVPNotFoundException):
        raise
    except Exception as e:
        logger.error(f"RSVP deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="RSVP deletion failed. Please try again.",
        )


@router.post(
    "/checkin",
    response_model=RSVPResponse,
)
async def check_in_attendee(
    event_id: Annotated[int, Path(gt=0)],
    checkin_data: CheckInRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> RSVPResponse:
    try:
        rsvp = await rsvp_service.check_in_user(db, event_id, checkin_data.user_id, current_user)

        return RSVPResponse(
            id=rsvp.id,
            event_id=rsvp.event_id,
            user_id=rsvp.user_id,
            status=rsvp.status,
            checked_in=rsvp.checked_in,
            checked_in_at=rsvp.checked_in_at,
            created_at=rsvp.created_at,
            updated_at=rsvp.updated_at,
        )
    except (EventNotFoundException, NotEventOrganizerException, RSVPNotFoundException):
        raise
    except Exception as e:
        logger.error(f"Check-in failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Check-in failed. Please try again.",
        )

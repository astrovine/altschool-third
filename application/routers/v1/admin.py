from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.user import User
from application.schemas.user import UserBanUpdate, UserResponse
from application.services.event_service import event_service
from application.services.user_service import user_service
from application.utilities.database import get_db
from application.utilities.dependencies import get_current_admin_user
from application.utilities.exceptions import (
    EventNotFoundException,
    NotEventOrganizerException,
    UserNotFoundException,
)
from application.utilities.logging import logger


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/users",
    response_model=list[UserResponse],
)
async def list_users(
    current_user: Annotated[User, Depends(get_current_admin_user)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    db: AsyncSession = Depends(get_db),
) -> list[UserResponse]:
    try:
        users = await user_service.get_all_users(db, skip, limit)
        return [UserResponse.model_validate(user) for user in users]
    except Exception as e:
        logger.error(f"User listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users. Please try again.",
        )


@router.patch(
    "/users/{user_id}/ban",
    response_model=UserResponse,
)
async def ban_user(
    user_id: Annotated[int, Path(gt=0)],
    ban_data: UserBanUpdate,
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    try:
        user = await user_service.ban_user(db, user_id, ban_data.is_banned)
        return UserResponse.model_validate(user)
    except UserNotFoundException:
        raise
    except Exception as e:
        logger.error(f"User ban failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status. Please try again.",
        )


@router.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def admin_delete_event(
    event_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[User, Depends(get_current_admin_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await event_service.delete_event(db, event_id, current_user)
    except (EventNotFoundException, NotEventOrganizerException):
        raise
    except Exception as e:
        logger.error(f"Admin event deletion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Event deletion failed. Please try again.",
        )

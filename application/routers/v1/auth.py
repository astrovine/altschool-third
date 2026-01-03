from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.user import User
from application.schemas.auth import LoginRequest, Token, TokenRefresh
from application.schemas.user import UserCreate, UserResponse
from application.services.auth_service import auth_service
from application.utilities.database import get_db
from application.utilities.dependencies import get_current_user
from application.utilities.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    UserAlreadyExistsException,
)
from application.utilities.logging import logger


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    try:
        user = await auth_service.register(db, user_data)
        return UserResponse.model_validate(user)
    except UserAlreadyExistsException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again.",
        )


@router.post(
    "/login",
    response_model=Token,
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db),
) -> Token:
    try:
        return await auth_service.login(db, form_data.username, form_data.password)
    except InvalidCredentialsException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again.",
        )


@router.post(
    "/refresh",
    response_model=Token,
)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
) -> Token:
    try:
        return await auth_service.refresh_tokens(db, token_data.refresh_token)
    except InvalidTokenException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please try again.",
        )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        await auth_service.logout(db, current_user.id)
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again.",
        )


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse.model_validate(current_user)

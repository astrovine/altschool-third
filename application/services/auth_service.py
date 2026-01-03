from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.refresh_token import RefreshToken
from application.models.user import User
from application.schemas.auth import Token
from application.schemas.user import UserCreate
from application.services.user_service import user_service
from application.utilities.config import settings
from application.utilities.exceptions import InvalidCredentialsException, InvalidTokenException
from application.utilities.logging import logger
from application.utilities.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_token_expiry,
    verify_password,
)


class AuthService:
    async def register(
        self,
        db: AsyncSession,
        user_data: UserCreate,
    ) -> User:
        try:
            return await user_service.create_user(db, user_data)
        except Exception as e:
            logger.error(f"Registration error in service: {e}")
            raise

    async def login(
        self,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> Token:
        try:
            user = await user_service.get_user_by_email(db, email)
            if not user:
                logger.warning(f"Login attempt for non-existent user: {email}")
                raise InvalidCredentialsException()

            if not verify_password(password, user.hashed_password):
                logger.warning(f"Invalid password attempt for user: {email}")
                raise InvalidCredentialsException()

            if not user.is_active or user.is_banned:
                logger.warning(f"Login attempt for inactive/banned user: {email}")
                raise InvalidCredentialsException()

            access_token = create_access_token(subject=user.id)
            refresh_token = create_refresh_token(subject=user.id)

            token_record = RefreshToken(
                user_id=user.id,
                token=refresh_token,
                expires_at=get_token_expiry(days=settings.refresh_token_expire_days),
            )
            db.add(token_record)
            await db.flush()

            logger.info(f"User logged in successfully: {email}")
            return Token(
                access_token=access_token,
                refresh_token=refresh_token,
            )
        except InvalidCredentialsException:
            raise
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise

    async def refresh_tokens(
        self,
        db: AsyncSession,
        refresh_token: str,
    ) -> Token:
        try:
            payload = decode_token(refresh_token)
            if not payload:
                logger.warning("Invalid token during refresh attempt")
                raise InvalidTokenException()

            if payload.get("type") != "refresh":
                logger.warning("Non-refresh token used for refresh")
                raise InvalidTokenException()

            stmt = select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            result = await db.execute(stmt)
            token_record = result.scalar_one_or_none()

            if not token_record:
                logger.warning("Refresh token not found or expired")
                raise InvalidTokenException()

            user = await user_service.get_user_by_id(db, token_record.user_id)
            if not user or not user.is_active or user.is_banned:
                logger.warning("User not found or inactive during refresh")
                raise InvalidTokenException()

            token_record.revoked = True
            await db.flush()

            new_access_token = create_access_token(subject=user.id)
            new_refresh_token = create_refresh_token(subject=user.id)

            new_token_record = RefreshToken(
                user_id=user.id,
                token=new_refresh_token,
                expires_at=get_token_expiry(days=settings.refresh_token_expire_days),
            )
            db.add(new_token_record)
            await db.flush()

            logger.info(f"Tokens refreshed for user: {user.id}")
            return Token(
                access_token=new_access_token,
                refresh_token=new_refresh_token,
            )
        except InvalidTokenException:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise

    async def logout(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> None:
        try:
            stmt = (
                update(RefreshToken)
                .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
                .values(revoked=True)
            )
            await db.execute(stmt)
            await db.flush()
            logger.info(f"User logged out: {user_id}")
        except Exception as e:
            logger.error(f"Logout error: {e}")
            raise


auth_service = AuthService()

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.user import User
from application.schemas.user import UserCreate, UserUpdate
from application.utilities.exceptions import UserAlreadyExistsException, UserNotFoundException
from application.utilities.logging import logger
from application.utilities.security import get_password_hash


class UserService:
    async def create_user(
        self,
        db: AsyncSession,
        user_data: UserCreate,
    ) -> User:
        try:
            existing = await self.get_user_by_email(db, user_data.email)
            if existing:
                logger.warning(f"User creation failed - email exists: {user_data.email}")
                raise UserAlreadyExistsException(user_data.email)

            user = User(
                email=user_data.email,
                hashed_password=get_password_hash(user_data.password),
                full_name=user_data.full_name,
            )
            db.add(user)
            await db.flush()
            await db.refresh(user)
            logger.info(f"User created: {user.email}")
            return user
        except UserAlreadyExistsException:
            raise
        except Exception as e:
            logger.error(f"User creation error: {e}")
            raise

    async def get_user_by_id(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> Optional[User]:
        try:
            stmt = select(User).where(User.id == user_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Get user by id error: {e}")
            raise

    async def get_user_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> Optional[User]:
        try:
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Get user by email error: {e}")
            raise

    async def update_user(
        self,
        db: AsyncSession,
        user: User,
        user_data: UserUpdate,
    ) -> User:
        try:
            if user_data.full_name is not None:
                user.full_name = user_data.full_name
            if user_data.password is not None:
                user.hashed_password = get_password_hash(user_data.password)

            await db.flush()
            await db.refresh(user)
            logger.info(f"User updated: {user.id}")
            return user
        except Exception as e:
            logger.error(f"User update error: {e}")
            raise

    async def ban_user(
        self,
        db: AsyncSession,
        user_id: int,
        is_banned: bool,
    ) -> User:
        try:
            user = await self.get_user_by_id(db, user_id)
            if not user:
                logger.warning(f"Ban attempt on non-existent user: {user_id}")
                raise UserNotFoundException(str(user_id))

            user.is_banned = is_banned
            await db.flush()
            await db.refresh(user)

            action = "banned" if is_banned else "unbanned"
            logger.info(f"User {action}: {user_id}")
            return user
        except UserNotFoundException:
            raise
        except Exception as e:
            logger.error(f"User ban error: {e}")
            raise

    async def get_all_users(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        try:
            stmt = select(User).offset(skip).limit(limit)
            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Get all users error: {e}")
            raise


user_service = UserService()

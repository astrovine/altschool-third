from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from application.models.rsvp import RSVP, RSVPStatus
from application.models.user import User, UserRole
from application.schemas.rsvp import RSVPCreate
from application.services.event_service import event_service
from application.utilities.exceptions import (
    EventAtCapacityException,
    EventNotFoundException,
    NotEventOrganizerException,
    RSVPNotFoundException,
)
from application.utilities.logging import logger


class RSVPService:
    async def create_or_update_rsvp(
        self,
        db: AsyncSession,
        event_id: int,
        user: User,
        rsvp_data: RSVPCreate,
    ) -> RSVP:
        try:
            event = await event_service.get_event_by_id(db, event_id)

            existing_rsvp = await self.get_user_rsvp(db, event_id, user.id)

            if existing_rsvp:
                if rsvp_data.status == RSVPStatus.GOING and existing_rsvp.status != RSVPStatus.GOING:
                    if event.capacity is not None:
                        going_count = event_service.get_going_count(event)
                        if going_count >= event.capacity:
                            logger.warning(f"Event at capacity: {event_id}")
                            raise EventAtCapacityException(event_id)

                existing_rsvp.status = rsvp_data.status
                await db.flush()
                await db.refresh(existing_rsvp)
                logger.info(f"RSVP updated: user {user.id} event {event_id} status {rsvp_data.status}")
                return existing_rsvp

            if rsvp_data.status == RSVPStatus.GOING and event.capacity is not None:
                going_count = event_service.get_going_count(event)
                if going_count >= event.capacity:
                    logger.warning(f"Event at capacity on new RSVP: {event_id}")
                    raise EventAtCapacityException(event_id)

            rsvp = RSVP(
                event_id=event_id,
                user_id=user.id,
                status=rsvp_data.status,
            )
            db.add(rsvp)
            await db.flush()
            await db.refresh(rsvp)
            logger.info(f"RSVP created: user {user.id} event {event_id} status {rsvp_data.status}")
            return rsvp
        except (EventNotFoundException, EventAtCapacityException):
            raise
        except Exception as e:
            logger.error(f"RSVP create/update error: {e}")
            raise

    async def get_user_rsvp(
        self,
        db: AsyncSession,
        event_id: int,
        user_id: int,
    ) -> Optional[RSVP]:
        try:
            stmt = (
                select(RSVP)
                .options(selectinload(RSVP.user))
                .where(RSVP.event_id == event_id, RSVP.user_id == user_id)
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Get user RSVP error: {e}")
            raise

    async def get_rsvps_by_event(
        self,
        db: AsyncSession,
        event_id: int,
        current_user: User,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[RSVP], int]:
        try:
            event = await event_service.get_event_by_id(db, event_id)

            if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN:
                logger.warning(f"Unauthorized RSVP list access: user {current_user.id} event {event_id}")
                raise NotEventOrganizerException()

            count_stmt = (
                select(func.count())
                .select_from(RSVP)
                .where(RSVP.event_id == event_id)
            )
            count_result = await db.execute(count_stmt)
            total = count_result.scalar() or 0

            offset = (page - 1) * per_page
            stmt = (
                select(RSVP)
                .options(selectinload(RSVP.user))
                .where(RSVP.event_id == event_id)
                .order_by(RSVP.created_at.desc())
                .offset(offset)
                .limit(per_page)
            )
            result = await db.execute(stmt)
            rsvps = list(result.scalars().all())
            logger.info(f"RSVPs fetched: {len(rsvps)} of {total} for event {event_id}")
            return rsvps, total
        except (EventNotFoundException, NotEventOrganizerException):
            raise
        except Exception as e:
            logger.error(f"Get RSVPs error: {e}")
            raise

    async def delete_rsvp(
        self,
        db: AsyncSession,
        event_id: int,
        user: User,
    ) -> None:
        try:
            if not await event_service.event_exists(db, event_id):
                logger.warning(f"RSVP delete on non-existent event: {event_id}")
                raise EventNotFoundException(event_id)

            rsvp = await self.get_user_rsvp(db, event_id, user.id)
            if not rsvp:
                logger.warning(f"RSVP not found for delete: user {user.id} event {event_id}")
                raise RSVPNotFoundException(event_id)

            await db.delete(rsvp)
            await db.flush()
            logger.info(f"RSVP deleted: user {user.id} event {event_id}")
        except (EventNotFoundException, RSVPNotFoundException):
            raise
        except Exception as e:
            logger.error(f"RSVP delete error: {e}")
            raise

    async def check_in_user(
        self,
        db: AsyncSession,
        event_id: int,
        user_id: int,
        current_user: User,
    ) -> RSVP:
        try:
            event = await event_service.get_event_by_id(db, event_id)

            if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN:
                logger.warning(f"Unauthorized check-in attempt: user {current_user.id} event {event_id}")
                raise NotEventOrganizerException()

            rsvp = await self.get_user_rsvp(db, event_id, user_id)
            if not rsvp:
                logger.warning(f"Check-in RSVP not found: user {user_id} event {event_id}")
                raise RSVPNotFoundException(event_id)

            rsvp.checked_in = True
            rsvp.checked_in_at = datetime.now(timezone.utc)
            await db.flush()
            await db.refresh(rsvp)
            logger.info(f"User checked in: user {user_id} event {event_id}")
            return rsvp
        except (EventNotFoundException, NotEventOrganizerException, RSVPNotFoundException):
            raise
        except Exception as e:
            logger.error(f"Check-in error: {e}")
            raise


rsvp_service = RSVPService()

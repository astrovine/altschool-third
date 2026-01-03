from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from application.models.event import Event
from application.models.rsvp import RSVPStatus
from application.models.user import User, UserRole
from application.schemas.event import EventCreate, EventSearchParams, EventUpdate
from application.utilities.exceptions import EventNotFoundException, NotEventOrganizerException
from application.utilities.logging import logger


class EventService:
    async def create_event(
        self,
        db: AsyncSession,
        event_data: EventCreate,
        organizer_id: int,
        flyer_filename: Optional[str] = None,
    ) -> Event:
        try:
            event = Event(
                organizer_id=organizer_id,
                title=event_data.title,
                description=event_data.description,
                date=event_data.date,
                location=event_data.location,
                capacity=event_data.capacity,
                is_public=event_data.is_public,
                flyer_filename=flyer_filename,
            )
            db.add(event)
            await db.flush()
            await db.refresh(event)
            logger.info(f"Event created: {event.id} by user {organizer_id}")
            return event
        except Exception as e:
            logger.error(f"Event creation error: {e}")
            raise

    async def get_event_by_id(
        self,
        db: AsyncSession,
        event_id: int,
    ) -> Event:
        try:
            stmt = (
                select(Event)
                .options(selectinload(Event.rsvps), selectinload(Event.organizer))
                .where(Event.id == event_id)
            )
            result = await db.execute(stmt)
            event = result.scalar_one_or_none()
            if not event:
                logger.warning(f"Event not found: {event_id}")
                raise EventNotFoundException(event_id)
            return event
        except EventNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Get event error: {e}")
            raise

    async def get_events(
        self,
        db: AsyncSession,
        params: EventSearchParams,
    ) -> Tuple[List[Event], int]:
        try:
            base_query = select(Event).options(
                selectinload(Event.rsvps),
                selectinload(Event.organizer),
            )

            if params.q:
                search_term = f"%{params.q}%"
                base_query = base_query.where(
                    or_(
                        Event.title.ilike(search_term),
                        Event.description.ilike(search_term),
                    )
                )

            if params.from_date:
                base_query = base_query.where(Event.date >= params.from_date)

            if params.to_date:
                base_query = base_query.where(Event.date <= params.to_date)

            if params.location:
                base_query = base_query.where(Event.location.ilike(f"%{params.location}%"))

            if params.is_public is not None:
                base_query = base_query.where(Event.is_public == params.is_public)

            count_stmt = select(func.count()).select_from(base_query.subquery())
            count_result = await db.execute(count_stmt)
            total = count_result.scalar() or 0

            sort_column = getattr(Event, params.sort_by)
            if params.order == "desc":
                sort_column = sort_column.desc()
            else:
                sort_column = sort_column.asc()

            offset = (params.page - 1) * params.per_page
            stmt = base_query.order_by(sort_column).offset(offset).limit(params.per_page)

            result = await db.execute(stmt)
            events = list(result.scalars().all())
            logger.info(f"Events fetched: {len(events)} of {total}")
            return events, total
        except Exception as e:
            logger.error(f"Get events error: {e}")
            raise

    async def update_event(
        self,
        db: AsyncSession,
        event_id: int,
        event_data: EventUpdate,
        current_user: User,
        flyer_filename: Optional[str] = None,
    ) -> Event:
        try:
            event = await self.get_event_by_id(db, event_id)

            if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN:
                logger.warning(f"Unauthorized event update attempt: user {current_user.id} on event {event_id}")
                raise NotEventOrganizerException()

            if event_data.title is not None:
                event.title = event_data.title
            if event_data.description is not None:
                event.description = event_data.description
            if event_data.date is not None:
                event.date = event_data.date
            if event_data.location is not None:
                event.location = event_data.location
            if event_data.capacity is not None:
                event.capacity = event_data.capacity
            if event_data.is_public is not None:
                event.is_public = event_data.is_public
            if flyer_filename is not None:
                event.flyer_filename = flyer_filename

            await db.flush()
            await db.refresh(event)
            logger.info(f"Event updated: {event_id}")
            return event
        except (EventNotFoundException, NotEventOrganizerException):
            raise
        except Exception as e:
            logger.error(f"Event update error: {e}")
            raise

    async def delete_event(
        self,
        db: AsyncSession,
        event_id: int,
        current_user: User,
    ) -> None:
        try:
            event = await self.get_event_by_id(db, event_id)

            if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN:
                logger.warning(f"Unauthorized event delete attempt: user {current_user.id} on event {event_id}")
                raise NotEventOrganizerException()

            await db.delete(event)
            await db.flush()
            logger.info(f"Event deleted: {event_id}")
        except (EventNotFoundException, NotEventOrganizerException):
            raise
        except Exception as e:
            logger.error(f"Event delete error: {e}")
            raise

    async def event_exists(
        self,
        db: AsyncSession,
        event_id: int,
    ) -> bool:
        try:
            stmt = select(func.count()).select_from(Event).where(Event.id == event_id)
            result = await db.execute(stmt)
            count = result.scalar() or 0
            return count > 0
        except Exception as e:
            logger.error(f"Event exists check error: {e}")
            raise

    def get_going_count(self, event: Event) -> int:
        return sum(1 for rsvp in event.rsvps if rsvp.status == RSVPStatus.GOING)


event_service = EventService()

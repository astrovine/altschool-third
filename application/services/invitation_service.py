from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.invitation import EventInvitation
from application.models.user import User, UserRole
from application.services.event_service import event_service
from application.utilities.exceptions import (
    EventNotFoundException,
    InvitationAlreadyExistsException,
    NotEventOrganizerException,
)
from application.utilities.logging import logger


class InvitationService:
    async def create_invitations(
        self,
        db: AsyncSession,
        event_id: int,
        emails: List[str],
        current_user: User,
    ) -> List[EventInvitation]:
        try:
            event = await event_service.get_event_by_id(db, event_id)

            if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN:
                logger.warning(f"Unauthorized invitation attempt: user {current_user.id} event {event_id}")
                raise NotEventOrganizerException()

            created_invitations = []
            for email in emails:
                invitation = EventInvitation(
                    event_id=event_id,
                    email=email.lower(),
                    invited_by=current_user.id,
                )
                db.add(invitation)
                try:
                    await db.flush()
                    await db.refresh(invitation)
                    created_invitations.append(invitation)
                    logger.info(f"Invitation created: {email} for event {event_id}")
                except IntegrityError:
                    await db.rollback()
                    logger.warning(f"Duplicate invitation: {email} event {event_id}")
                    raise InvitationAlreadyExistsException(email, event_id)

            return created_invitations
        except (EventNotFoundException, NotEventOrganizerException, InvitationAlreadyExistsException):
            raise
        except Exception as e:
            logger.error(f"Invitation creation error: {e}")
            raise

    async def get_event_invitations(
        self,
        db: AsyncSession,
        event_id: int,
        current_user: User,
    ) -> Tuple[List[EventInvitation], int]:
        try:
            event = await event_service.get_event_by_id(db, event_id)

            if event.organizer_id != current_user.id and current_user.role != UserRole.ADMIN:
                logger.warning(f"Unauthorized invitation list access: user {current_user.id} event {event_id}")
                raise NotEventOrganizerException()

            count_stmt = (
                select(func.count())
                .select_from(EventInvitation)
                .where(EventInvitation.event_id == event_id)
            )
            count_result = await db.execute(count_stmt)
            total = count_result.scalar() or 0

            stmt = (
                select(EventInvitation)
                .where(EventInvitation.event_id == event_id)
                .order_by(EventInvitation.created_at.desc())
            )
            result = await db.execute(stmt)
            invitations = list(result.scalars().all())
            logger.info(f"Invitations fetched: {len(invitations)} for event {event_id}")
            return invitations, total
        except (EventNotFoundException, NotEventOrganizerException):
            raise
        except Exception as e:
            logger.error(f"Get invitations error: {e}")
            raise


invitation_service = InvitationService()

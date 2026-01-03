from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.user import User
from application.schemas.invitation import (
    InvitationCreate,
    InvitationListResponse,
    InvitationResponse,
)
from application.services.invitation_service import invitation_service
from application.utilities.database import get_db
from application.utilities.dependencies import get_current_user
from application.utilities.exceptions import (
    EventNotFoundException,
    InvitationAlreadyExistsException,
    NotEventOrganizerException,
)
from application.utilities.logging import logger


router = APIRouter(prefix="/events/{event_id}", tags=["Invitations"])


@router.post(
    "/invite",
    response_model=list[InvitationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def send_invitations(
    event_id: Annotated[int, Path(gt=0)],
    invitation_data: InvitationCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> list[InvitationResponse]:
    try:
        invitations = await invitation_service.create_invitations(
            db, event_id, invitation_data.emails, current_user
        )

        return [
            InvitationResponse(
                id=inv.id,
                event_id=inv.event_id,
                email=inv.email,
                invited_by=inv.invited_by,
                accepted_at=inv.accepted_at,
                created_at=inv.created_at,
            )
            for inv in invitations
        ]
    except (EventNotFoundException, NotEventOrganizerException, InvitationAlreadyExistsException):
        raise
    except Exception as e:
        logger.error(f"Invitation creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send invitations. Please try again.",
        )


@router.get(
    "/invitations",
    response_model=InvitationListResponse,
)
async def list_event_invitations(
    event_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> InvitationListResponse:
    try:
        invitations, total = await invitation_service.get_event_invitations(
            db, event_id, current_user
        )

        return InvitationListResponse(
            invitations=[
                InvitationResponse(
                    id=inv.id,
                    event_id=inv.event_id,
                    email=inv.email,
                    invited_by=inv.invited_by,
                    accepted_at=inv.accepted_at,
                    created_at=inv.created_at,
                )
                for inv in invitations
            ],
            total=total,
            event_id=event_id,
        )
    except (EventNotFoundException, NotEventOrganizerException):
        raise
    except Exception as e:
        logger.error(f"Invitation listing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch invitations. Please try again.",
        )

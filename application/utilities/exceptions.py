from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class BaseApplicationException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class EventNotFoundException(BaseApplicationException):
    def __init__(self, event_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event with id {event_id} not found",
        )


class UserNotFoundException(BaseApplicationException):
    def __init__(self, identifier: str = "") -> None:
        detail = f"User {identifier} not found" if identifier else "User not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class UserAlreadyExistsException(BaseApplicationException):
    def __init__(self, email: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {email} already exists",
        )


class InvalidCredentialsException(BaseApplicationException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenException(BaseApplicationException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


class RSVPAlreadyExistsException(BaseApplicationException):
    def __init__(self, user_id: int, event_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"RSVP already exists for user {user_id} on event {event_id}",
        )


class RSVPNotFoundException(BaseApplicationException):
    def __init__(self, event_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RSVP not found for event {event_id}",
        )


class EventAtCapacityException(BaseApplicationException):
    def __init__(self, event_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Event {event_id} has reached maximum capacity",
        )


class NotEventOrganizerException(BaseApplicationException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the event organizer can perform this action",
        )


class InvitationAlreadyExistsException(BaseApplicationException):
    def __init__(self, email: str, event_id: int) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Invitation already sent to {email} for event {event_id}",
        )


class FileUploadException(BaseApplicationException):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class InvalidFileTypeException(FileUploadException):
    def __init__(self, allowed_types: list[str]) -> None:
        super().__init__(
            detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}",
        )


class FileSizeLimitExceededException(FileUploadException):
    def __init__(self, max_size_mb: int) -> None:
        super().__init__(
            detail=f"File size exceeds maximum allowed size of {max_size_mb}MB",
        )


class ValidationException(BaseApplicationException):
    def __init__(self, detail: str) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class UserBannedException(BaseApplicationException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been banned",
        )

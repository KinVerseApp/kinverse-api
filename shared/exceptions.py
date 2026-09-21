from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status


class KinVerseAPIError(Exception):
    def __init__(self, message: str, *, status_code: int = status.HTTP_400_BAD_REQUEST, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_http_exception(self) -> HTTPException:
        return HTTPException(status_code=self.status_code, detail={"message": self.message, "details": self.details})


class NotFoundError(KinVerseAPIError):
    def __init__(self, entity: str, entity_id: str | None = None) -> None:
        identifier = f" {entity_id}" if entity_id else ""
        super().__init__(f"{entity}{identifier} was not found.", status_code=status.HTTP_404_NOT_FOUND)


class PermissionDeniedError(KinVerseAPIError):
    def __init__(self, message: str = "You do not have permission to perform this action.") -> None:
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class InvalidAuthError(KinVerseAPIError):
    def __init__(self, message: str = "Authentication failed.") -> None:
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class ValidationError(KinVerseAPIError):
    def __init__(self, message: str = "The submitted data is invalid.", details: dict[str, Any] | None = None) -> None:
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details)

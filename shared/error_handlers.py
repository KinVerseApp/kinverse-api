"""Application-wide exception handlers.

Every error response the API sends has the same JSON shape:

    {"message": "<human readable>", "details": {...}}

That's the shape KinVerseAPIError already used. These handlers make
framework errors (unknown route, bad request body), database errors and
anything genuinely unexpected use it too, instead of falling through to
Starlette's plain-text "Internal Server Error".

Rules:
  * Client mistakes the database catches (duplicate row, reference to a row
    that doesn't exist, value outside an enum, CHECK constraint) become
    4xx with a generic message. SQL, table names and constraint names are
    logged, never returned.
  * The database being unreachable is 503, not 500. The request may succeed
    if retried.
  * Anything else is 500 with an error_id. The full traceback is logged
    under that id, so a user-reported id can be matched to the server log.
"""

from __future__ import annotations

import socket
import uuid
from typing import Any

import asyncpg.exceptions as pg_errors
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import (
    DataError,
    DisconnectionError,
    IntegrityError,
    InterfaceError,
    OperationalError,
)
from sqlalchemy.exc import TimeoutError as PoolTimeoutError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import KinVerseAPIError
from .telemetry import get_logger

logger = get_logger("kinverse.api.errors")

# PostgreSQL SQLSTATE codes - https://www.postgresql.org/docs/current/errcodes-appendix.html
_UNIQUE_VIOLATION = "23505"
_FOREIGN_KEY_VIOLATION = "23503"
_NOT_NULL_VIOLATION = "23502"
_CHECK_VIOLATION = "23514"

_UNAVAILABLE_MESSAGE = "The service is temporarily unavailable. Please try again shortly."


def error_body(message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"message": message, "details": details or {}}


def _json(status_code: int, message: str, details: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=error_body(message, details), headers=headers)


def _sqlstate(exc: Exception) -> str | None:
    # SQLAlchemy's asyncpg adapter copies the server's SQLSTATE onto the
    # wrapped DBAPI exception as both .sqlstate and .pgcode.
    orig = getattr(exc, "orig", None)
    return getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)


def _db_error_context(request: Request, exc: Exception) -> str:
    # Log where the error happened, not the values involved: Postgres's
    # message and DETAIL echo the offending row (e.g. "Key (email)=(...)
    # already exists"), which can be personal data. The underlying asyncpg
    # error carries structured fields that identify the cause without it.
    pg = getattr(getattr(exc, "orig", None), "__cause__", None)
    return (
        f"{request.method} {request.url.path} sqlstate={_sqlstate(exc)} "
        f"table={getattr(pg, 'table_name', None)} column={getattr(pg, 'column_name', None)} "
        f"constraint={getattr(pg, 'constraint_name', None)}"
    )


async def _kinverse_error(request: Request, exc: KinVerseAPIError) -> JSONResponse:
    del request
    return _json(exc.status_code, exc.message, exc.details, exc.headers)


async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    del request
    detail = exc.detail
    if isinstance(detail, dict) and "message" in detail:
        return _json(exc.status_code, str(detail["message"]), detail.get("details"), exc.headers)
    return _json(exc.status_code, str(detail), None, exc.headers)


async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    del request
    errors = []
    for err in exc.errors():
        # FastAPI's default handler echoes "input" back - for a login or
        # register body that is the submitted password. Never return it.
        errors.append({k: v for k, v in err.items() if k not in ("input", "url")})
    return _json(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        "Request validation failed.",
        {"errors": jsonable_encoder(errors)},
    )


async def _integrity_error(request: Request, exc: IntegrityError) -> JSONResponse:
    code = _sqlstate(exc)
    logger.info("Integrity error on %s", _db_error_context(request, exc))
    if code == _UNIQUE_VIOLATION:
        return _json(status.HTTP_409_CONFLICT, "A record with these details already exists.")
    if code == _FOREIGN_KEY_VIOLATION:
        if "is still referenced" in str(exc.orig):
            return _json(status.HTTP_409_CONFLICT, "This record is still in use and cannot be removed.")
        return _json(status.HTTP_404_NOT_FOUND, "A referenced record was not found.")
    if code in (_CHECK_VIOLATION, _NOT_NULL_VIOLATION):
        return _json(status.HTTP_422_UNPROCESSABLE_ENTITY, "The submitted data is invalid.")
    return await _unexpected_error(request, exc)


async def _data_error(request: Request, exc: DataError) -> JSONResponse:
    # Value the column type rejects: not one of an enum's values, too long
    # for a VARCHAR, malformed date, ...
    logger.info("Data error on %s", _db_error_context(request, exc))
    return _json(status.HTTP_422_UNPROCESSABLE_ENTITY, "One or more submitted values are invalid.")


async def _database_unavailable(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Database unavailable on %s %s: %s: %s", request.method, request.url.path, type(exc).__name__, exc
    )
    return _json(status.HTTP_503_SERVICE_UNAVAILABLE, _UNAVAILABLE_MESSAGE, headers={"Retry-After": "5"})


async def _unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    error_id = uuid.uuid4().hex
    logger.error(
        "Unhandled error %s on %s %s", error_id, request.method, request.url.path, exc_info=exc
    )
    return _json(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "An unexpected error occurred. Please try again later.",
        {"error_id": error_id},
    )


# Raised when the database server can't be reached or the connection drops:
# SQLAlchemy's wrapped forms, plus what asyncpg raises unwrapped while
# opening a new connection - network errors (refused, DNS failure, timeout)
# and server-side refusals (bad credentials, server starting up, too many
# connections). None of these is something the client can fix; all are
# logged at ERROR with the exception type so an operator can.
_UNAVAILABLE_ERRORS: tuple[type[BaseException], ...] = (
    OperationalError,
    InterfaceError,
    DisconnectionError,
    PoolTimeoutError,
    ConnectionError,
    socket.gaierror,
    TimeoutError,
    pg_errors.PostgresConnectionError,
    pg_errors.InvalidAuthorizationSpecificationError,
    pg_errors.CannotConnectNowError,
    pg_errors.TooManyConnectionsError,
)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(KinVerseAPIError, _kinverse_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(IntegrityError, _integrity_error)
    app.add_exception_handler(DataError, _data_error)
    for exc_type in _UNAVAILABLE_ERRORS:
        app.add_exception_handler(exc_type, _database_unavailable)
    # Registered for Exception, Starlette routes this through
    # ServerErrorMiddleware - the last line of defence for anything above
    # didn't anticipate.
    app.add_exception_handler(Exception, _unexpected_error)

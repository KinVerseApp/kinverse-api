from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime

# Every timestamp column in kinverse_schema.sql (kinverse-project repo) is
# TIMESTAMPTZ. SQLAlchemy's plain DateTime() type binds parameters as
# timezone-naive by default. Against a TIMESTAMPTZ column that either
# crashes outright (asyncpg refuses a tz-aware Python value: "can't
# subtract offset-naive and offset-aware datetimes") or, worse, silently
# succeeds with a naive value that Postgres then interprets in the
# session's timezone instead of UTC - a correctness bug that wouldn't
# surface until timestamps were subtly wrong later. Always use this type
# for any column backed by a TIMESTAMPTZ, and utcnow() - never the naive
# datetime.utcnow() - for its Python-side default.
UTCDateTime = DateTime(timezone=True)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)

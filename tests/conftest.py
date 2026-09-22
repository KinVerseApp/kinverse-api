from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import app
from shared.database import get_db
from tests.fixtures.sample_tree import seed_sample_tree

# A dedicated database, never the same one a developer might be using by
# hand for manual testing - every test runs in a rolled-back transaction, so
# this database ends each test run exactly as empty as it started, and
# tests can run in any order or in parallel without stepping on each other.
TEST_DATABASE_URL = os.environ.get(
    "KINVERSE_TEST_DATABASE_URL",
    "postgresql+asyncpg://kinverse:test@localhost:5432/kinverse_ci_test",
)

# kinverse-api owns the ORM models; kinverse-project owns the DDL that
# creates the actual tables/enums those models describe. This suite needs
# both, so it looks for a sibling checkout of kinverse-project (the layout
# this session and the CI workflow both use) and applies its schema script
# once, at session start, only if the tables don't already exist. See
# tests/README.md for the alternative (pre-apply the schema yourself and
# skip this entirely by pointing KINVERSE_TEST_DATABASE_URL at a database
# that already has it).
_SCHEMA_SQL = (
    Path(__file__).resolve().parents[2]
    / "kinverse-project" / "databasefiles" / "postgresql" / "001_kinverse_schema.sql"
)


def _sync_url(async_url: str) -> str:
    return async_url.replace("postgresql+asyncpg://", "postgresql://")


@pytest.fixture(scope="session")
def ensure_schema() -> None:
    import asyncio

    import asyncpg

    async def _check() -> bool:
        conn = await asyncpg.connect(_sync_url(TEST_DATABASE_URL))
        try:
            row = await conn.fetchrow(
                "SELECT 1 FROM information_schema.tables WHERE table_name = 'relationship_edge'"
            )
            return row is not None
        finally:
            await conn.close()

    if asyncio.run(_check()):
        return

    if not _SCHEMA_SQL.exists():
        pytest.exit(
            f"Test database has no schema and {_SCHEMA_SQL} was not found.\n"
            "Either check out kinverse-project as a sibling of kinverse-api, "
            "or apply 001_kinverse_schema.sql to the test database yourself "
            "and re-run - see tests/README.md.",
            returncode=1,
        )

    subprocess.run(
        ["psql", _sync_url(TEST_DATABASE_URL), "-v", "ON_ERROR_STOP=1", "-f", str(_SCHEMA_SQL)],
        check=True,
    )


@pytest_asyncio.fixture
async def engine(ensure_schema):
    # Function-scoped deliberately: asyncpg connections are bound to the
    # event loop they were created on, and pytest-asyncio gives each test
    # function its own loop by default. A session-scoped engine here was
    # tried first and broke on the second test in any module with
    # "attached to a different loop" - a fresh engine per test avoids that
    # whole class of problem at a small, acceptable setup cost.
    del ensure_schema  # ordering dependency only - schema must exist first
    eng = create_async_engine(TEST_DATABASE_URL)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """One test = one transaction, always rolled back.

    The app's repositories call session.commit() internally (that's how
    they're written throughout, not an artifact of testing), so a plain
    'wrap in a transaction and roll back' doesn't work - commit() would end
    the outer transaction early. join_transaction_mode="create_savepoint"
    makes every commit() from application code only release a SAVEPOINT;
    the real transaction, and everything in it, is rolled back here.
    """
    async with engine.connect() as connection:
        outer = await connection.begin()
        session_factory = async_sessionmaker(
            bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        session: AsyncSession = session_factory()
        yield session
        await session.close()
        await outer.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    """An httpx client that talks to the real FastAPI app in-process, with
    the database dependency overridden to use this test's isolated,
    soon-to-be-rolled-back session - so 'send a real request' and 'check the
    database directly' (via db_session in the same test) see the same data.
    """

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_tree(db_session):
    """Seeds the standard Narayanan/Kumar/Smith/Rao family (see
    tests/fixtures/sample_tree.py) inside this test's transaction. Returns a
    dict of person key -> Person, plus 'sunil_account' -> UserAccount.
    """
    return await seed_sample_tree(db_session)

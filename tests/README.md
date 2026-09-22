# Test automation

Real HTTP requests against the actual FastAPI app, over a real Postgres
database, with the resulting rows checked directly - not mocks, and not
just "did the endpoint return 200".

## What's here

| File | Covers |
|---|---|
| `conftest.py` | Fixtures: an isolated per-test DB transaction, an HTTP client wired to it, and schema bootstrapping |
| `fixtures/sample_tree.py` | The standard 10-person family (Ramesh/Lakshmi/John/Mary/Deepa/Sunil/Priya/Arjun/Meera/Kiran) used across most test modules - same tree used for manual verification throughout development |
| `test_auth.py` | Register, login, refresh - including the regression tests for the security bugs found in review (broken password check, unvalidated refresh tokens, account enumeration) |
| `test_relationships.py` | Adding relatives, canonical partner-edge ordering, confirm/reject/remove |
| `test_tree.py` | Ancestors/descendants/siblings/completeness score against the sample tree |
| `test_profiles.py` | The "Add Relative" composite flow (create person -> link relationship -> appears in tree) |
| `test_invitations.py` | Full lifecycle including a genuinely different account claiming an unclaimed person on accept |
| `test_notifications.py` | List/read/unread-count, including the cross-user ownership check |
| `test_privacy.py` | Per-field visibility defaults and updates |
| `test_search.py` | Trigram name search (including typo tolerance) and email search |

Every test that creates or changes data also queries the database directly
(via `db_session`, in the same transaction the HTTP request ran in) to
confirm the row is actually there with the right values - not just that the
API said 200.

## Running locally

Needs Postgres reachable and the schema applied. Two ways:

**Automatic** (what CI does): check out `kinverse-project` as a sibling of
this repo -

```
some-folder/
├── kinverse-api/       (this repo)
└── kinverse-project/
```

then just run `pytest` - `conftest.py` detects an empty test database and
applies `kinverse-project/databasefiles/postgresql/001_kinverse_schema.sql`
itself, once.

**Manual**: apply the schema yourself to whatever database you point at,
then run tests against it:

```bash
export KINVERSE_TEST_DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dbname"
pytest tests/
```

Defaults to `postgresql+asyncpg://kinverse:test@localhost:5432/kinverse_ci_test`
if the env var isn't set.

## Isolation

Each test runs inside its own database transaction, which is rolled back
when the test ends - including any `session.commit()` calls the application
code makes internally (repositories throughout this codebase commit
directly, not deferred to the caller), via SQLAlchemy's
`join_transaction_mode="create_savepoint"`. Tests can run in any order, and
the database is left exactly as empty as it started - verified by hand:
every table has 0 rows both before and after a full run.

## CI

`.github/workflows/api-tests.yml` runs this suite on every push/PR to
`main`, against a real `postgres:16` service container.

# Pass 4 — FastAPI Project Scaffolding

## Folder layout

The project is organized as a modular monolith:

```text
kinverse-api/
  app.py
  users/
    routes.py
    service.py
    repository.py
    schemas.py
    models.py
  profiles/
    routes.py
    service.py
    repository.py
    schemas.py
  relationships/
    routes.py
    service.py
    repository.py
    schemas.py
  tree/
    routes.py
    service.py
    repository.py
    schemas.py
  invitations/
    routes.py
    service.py
    repository.py
    schemas.py
  notifications/
    routes.py
    service.py
    repository.py
    schemas.py
  search/
    routes.py
    service.py
    repository.py
    schemas.py
  privacy/
    routes.py
    service.py
    repository.py
    schemas.py
  auth/
    routes.py
    service.py
    schemas.py
  shared/
    database.py
    security.py
    exceptions.py
    telemetry.py
    settings.py
    dependencies.py
  tests/
```

## Dependency injection design

Each module exposes an `APIRouter` and a service object created at startup. Global `AsyncSession` lifecycle is managed by the database dependency.

```python
app = FastAPI(title="KinVerse API")

app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(users_router, prefix="/api/v1/users")
app.include_router(profiles_router, prefix="/api/v1/profiles")
```

## Shared infrastructure

- `shared/settings.py`: environment configuration for DB, JWT, Azure, rate limiting, and logging
- `shared/database.py`: SQLAlchemy async engine and session factory
- `shared/dependencies.py`: authentication and role dependencies
- `shared/security.py`: token generation, verification, and password hashing
- `shared/exceptions.py`: translated custom errors
- `shared/telemetry.py`: Application Insights instrumentation and log correlation

## Environment variables

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/kinverse
JWT_SECRET_KEY=replace_me
JWT_ALGORITHM=HS256
APPINSIGHTS_CONNECTION_STRING=
AZURE_STORAGE_ACCOUNT_NAME=
AZURE_STORAGE_ACCOUNT_KEY=
AZURE_STORAGE_CONTAINER=profiles
```

## Operational concerns

- Use SQLAlchemy async session scope per request.
- Use `asyncio.TaskGroup` or Azure Functions for asynchronous jobs.
- Apply rate limiting at the app boundary to protect login and invite endpoints.
- Keep tree queries bounded by a `max_depth` and `limit` guard.

## Recommended implementation order

1. Shared infrastructure and settings
2. Authentication and user account modules
3. Profile and privacy modules
4. Relationship and tree graph modules
5. Invitations and notifications
6. Search and contact discovery
7. Background job contracts and Azure Functions hooks
8. E2E tests and smoke validation

# KinVerse API Foundation

This backend foundation implements a production-ready FastAPI backend for the KinVerse family relationship platform using a modular monolith pattern.

## Project summary

- Python 3.12
- FastAPI + Pydantic v2
- SQLAlchemy 2.0 async + PostgreSQL
- Alembic migrations
- JWT access/refresh token support
- Azure Entra External ID authentication support for Microsoft, Google, Apple, and email login
- Azure App Service deployment configuration
- Azure Blob Storage integration and background jobs via Azure Functions
- Application Insights logging
- Graph-based family relationship model using only `parent_child` and `partner` edges

## Five-pass delivery sequence

1. [pass_01_api_catalog_and_openapi.md](pass_01_api_catalog_and_openapi.md)
2. [pass_02_auth_architecture.md](pass_02_auth_architecture.md)
3. [pass_03_service_repository_interfaces.md](pass_03_service_repository_interfaces.md)
4. [pass_04_fastapi_project_scaffolding.md](pass_04_fastapi_project_scaffolding.md)
5. [pass_05_endpoint_implementations.md](pass_05_endpoint_implementations.md)

## Folder structure

```text
kinverse-api/
  app.py
  requirements.txt
  README.md
  openapi.yaml
  auth/
    __init__.py
    routes.py
    service.py
    schemas.py
  users/
    __init__.py
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
  shared/
    __init__.py
    database.py
    security.py
    exceptions.py
    telemetry.py
    settings.py
    dependencies.py
  tests/
    test_app_smoke.py
```

## Design principles

- Graph relationships are derived from edge traversal only.
- No labels like sibling, aunt, or grandparent are stored in the database.
- The API uses lazy loading, pagination, and branch expansion to respect the 50-relative tree request limit.
- Authorization is enforced using JWT claims and policy checks by user ownership and relationship scope.
- Background work is separated from request processing.

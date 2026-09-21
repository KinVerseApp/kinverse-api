# Pass 5 — Endpoint Implementations

## Implementation conventions

Each feature area uses the same pattern:

1. `schemas.py` defines request and response Pydantic models.
2. `repository.py` encapsulates SQLAlchemy queries.
3. `service.py` holds business logic and authorization checks.
4. `routes.py` exposes HTTP endpoints and depends on the service.

## Example auth route

```python
@router.post("/login", response_model=TokenResponse, tags=["auth"])
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    return await service.login(payload)
```

## Example tree route

```python
@router.get("/", response_model=TreeResponse, tags=["tree"])
async def get_tree(
    root_id: UUID | None = None,
    limit: int = Query(default=50, le=50),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TreeResponse:
    service = TreeService(db)
    return await service.get_tree(current_user["sub"], root_id=root_id, limit=limit)
```

## Example repository query pattern

```python
async def get_descendants(self, person_id: UUID) -> list[PersonNode]:
    query = text("""
        WITH RECURSIVE descendants AS (
            SELECT person_b_id AS id, 1 AS depth
            FROM relationship_edge
            WHERE person_a_id = :person_id
              AND edge_type = 'parent_child'
              AND status = 'confirmed'
            UNION ALL
            SELECT re.person_b_id, d.depth + 1
            FROM relationship_edge re
            JOIN descendants d ON re.person_a_id = d.id
            WHERE re.edge_type = 'parent_child' AND re.status = 'confirmed'
        )
        SELECT * FROM descendants
    """)
    return await self._execute(query, {"person_id": str(person_id)})
```

## Endpoint implementation order

1. `auth` and `users`
2. `profiles` and `privacy`
3. `relationships`
4. `tree`
5. `invitations`, `notifications`, and `search`
6. `contact discovery` extension and background job interfaces

## Testing strategy

The project includes a smoke test to confirm that the app boots correctly and the route metadata appears in OpenAPI.

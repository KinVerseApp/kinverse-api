from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse

from shared.exceptions import KinVerseAPIError
from auth.routes import router as auth_router
from invitations.routes import router as invitations_router
from notifications.routes import router as notifications_router
from privacy.routes import router as privacy_router
from profiles.routes import router as profiles_router
from relationships.routes import router as relationships_router
from search.routes import router as search_router
from tree.routes import router as tree_router
from users.routes import router as users_router
from shared.telemetry import configure_telemetry

app = FastAPI(
    title="KinVerse API",
    version="0.1.0",
    description=(
        "Production-ready FastAPI backend foundation for the KinVerse family relationship platform. "
        "The model stores only parent_child and partner edges and derives all named relationships "
        "at query time."
    ),
    openapi_tags=[
        {"name": "auth", "description": "Authentication, JWT, login, reset, verification"},
        {"name": "users", "description": "User registration and current-user endpoints"},
        {"name": "profiles", "description": "Profile creation, updates, heritage and image upload"},
        {"name": "relationships", "description": "Graph relationship lifecycle"},
        {"name": "tree", "description": "Family tree, ancestors, descendants and derived relationship labels"},
        {"name": "invitations", "description": "Invite generation and invitation acceptance flows"},
        {"name": "notifications", "description": "Notification list, read status and unread count"},
        {"name": "search", "description": "Discovery, name search, email search and family member search"},
        {"name": "privacy", "description": "Privacy settings and visibility filtering"},
    ],
)

configure_telemetry(app)


@app.exception_handler(KinVerseAPIError)
async def kinverse_api_error_handler(request: Request, exc: KinVerseAPIError) -> JSONResponse:
    # Every service raises KinVerseAPIError subclasses (NotFoundError, ValidationError,
    # PermissionDeniedError, ...) instead of HTTPException directly, so this single
    # handler is what turns them into the right status code + body. Without it, a
    # raised NotFoundError bubbles up as an unhandled 500 instead of a 404.
    del request
    http_exc = exc.to_http_exception()
    return JSONResponse(status_code=http_exc.status_code, content=http_exc.detail)


app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(users_router, prefix="/api/v1/users")
app.include_router(profiles_router, prefix="/api/v1/profiles")
app.include_router(relationships_router, prefix="/api/v1/relationships")
app.include_router(tree_router, prefix="/api/v1/tree")
app.include_router(invitations_router, prefix="/api/v1/invitations")
app.include_router(notifications_router, prefix="/api/v1/notifications")
app.include_router(search_router, prefix="/api/v1/search")
app.include_router(privacy_router, prefix="/api/v1/privacy")

@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

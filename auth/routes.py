from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.dependencies import get_current_user
from .schemas import (
    EmailVerificationRequest,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from .service import AuthService

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=TokenResponse, summary="Register a user")
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    result = await service.register_user(payload.model_dump())
    return TokenResponse(**result)


@router.post("/login", response_model=TokenResponse, summary="Login with email")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    result = await service.login(payload.model_dump())
    return TokenResponse(**result)


@router.post("/logout", status_code=204, response_model=None, summary="Logout and revoke refresh token")
async def logout(
    payload: LogoutRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = AuthService(db)
    await service.logout(current_user["sub"], payload.refresh_token)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
async def refresh(payload: RefreshTokenRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    service = AuthService(db)
    result = await service.refresh_token(payload.refresh_token)
    return TokenResponse(**result)


@router.post("/password-reset/request", summary="Request password reset")
async def request_password_reset(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)) -> dict:
    service = AuthService(db)
    return await service.request_password_reset(payload.email)


@router.post("/password-reset/confirm", summary="Confirm password reset")
async def confirm_password_reset(payload: PasswordResetConfirmRequest, db: AsyncSession = Depends(get_db)) -> dict:
    service = AuthService(db)
    return await service.confirm_password_reset(payload.token, payload.new_password)


@router.post("/email/verify", summary="Send email verification")
async def verify_email(payload: EmailVerificationRequest, db: AsyncSession = Depends(get_db)) -> dict:
    service = AuthService(db)
    return await service.verify_email(payload.email)


@router.post("/email/verify/confirm", summary="Confirm email verification")
async def confirm_email_verification(payload: EmailVerificationRequest, db: AsyncSession = Depends(get_db)) -> dict:
    service = AuthService(db)
    return await service.confirm_email_verification(payload.email)

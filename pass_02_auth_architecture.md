# Pass 2 — Authentication Architecture

## 1. Identity strategy

KinVerse uses Azure Entra External ID as the central identity platform for all external logins. The backend accepts tokens from Microsoft, Google, and Apple and maps them to the locally managed `user_account` and `person` records.

Supported providers:

- `google`
- `apple`
- `microsoft`
- `email`

## 2. Token model

- Access token: short-lived, e.g. 15 minutes
- Refresh token: long-lived, e.g. 30 days, stored hashed in database or a secure token store
- JWT claims include:
  - `sub`: user account UUID
  - `provider`
  - `email`
  - `role`
  - `tenant_id` or external subject mapping
  - `token_type`

## 3. Auth flow

### Email login

1. Client posts email and password to `/api/v1/auth/login`.
2. FastAPI validates client inputs.
3. Service checks `user_account` row and verifies hashed password.
4. Access and refresh tokens are minted.
5. `last_login_at` is updated.

### External login

1. Mobile app authenticates with provider and receives an external ID token.
2. Backend verifies the JWT signature against the provider's public keys or Azure Entra metadata.
3. The service resolves the matching `auth_provider_subject` record.
4. If absent, a new `user_account` is created and a new `person` can be created or linked.
5. Tokens are returned to the client.

## 4. Authorization model

Authorization is claim-based and ownership-aware.

- `user` role: normal user
- `admin` role: elevated internal operations
- `anonymous` role: unauthenticated requests

The policy checks include:

- current user owns the `person` record or is the creator
- request is within the same family graph scope
- relationship visibility policy allows the data to be viewed
- privacy settings restrict field visibility

## 5. Refresh and logout

- Logout invalidates the refresh token by setting a revoked flag or storing a denylist.
- Refresh token rotation is recommended: each refresh emits a new refresh token and revokes the previous one.
- Replay detection prevents refresh token reuse.

## 6. Password reset and verification

- Password reset uses a time-limited reset token.
- Email verification uses a signed verification token with expiry.
- Notification jobs send email verification links and verification completion messages.

## 7. Security hardening

- HTTPS only
- JWT signed with RS256 or HS256 with strong secret rotation
- Refresh tokens stored hashed or in secure token vault
- Add rate limiting on `/auth/login` and `/auth/refresh`
- Add CSRF protection for browser sessions if cookies are used
- Use App Service managed identity for Azure dependencies

## 8. Recommended dependency flow

```python
# dependency injection design
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    session: AsyncSession = Depends(get_db),
) -> UserAccount:
    return await auth_service.get_current_user(session, credentials.credentials)
```

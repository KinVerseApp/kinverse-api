# Pass 1 — API Catalog and OpenAPI Design

## A. Complete API endpoint catalog

### Authentication and user account

| Method | Path | Summary |
| --- | --- | --- |
| POST | /api/v1/auth/register | Register new user with email or external provider |
| POST | /api/v1/auth/login | Login with email, Google, Apple, or Microsoft |
| POST | /api/v1/auth/logout | Logout and invalidate refresh token |
| POST | /api/v1/auth/refresh | Refresh access token |
| POST | /api/v1/auth/password-reset/request | Request password reset |
| POST | /api/v1/auth/password-reset/confirm | Confirm password reset |
| POST | /api/v1/auth/email/verify | Trigger email verification |
| POST | /api/v1/auth/email/verify/confirm | Confirm email verification |
| GET | /api/v1/users/me | Get current user |

### Profiles

| Method | Path | Summary |
| --- | --- | --- |
| POST | /api/v1/profiles | Create profile |
| GET | /api/v1/profiles/{person_id} | Get profile |
| PATCH | /api/v1/profiles/{person_id} | Update profile |
| POST | /api/v1/profiles/{person_id}/image | Upload profile image |
| GET | /api/v1/profiles/{person_id}/heritage | Get heritage metadata |
| PATCH | /api/v1/profiles/{person_id}/heritage | Update heritage metadata |

### Relationships

| Method | Path | Summary |
| --- | --- | --- |
| POST | /api/v1/relationships | Add relative or partner relationship |
| PATCH | /api/v1/relationships/{relationship_id} | Update pending relationship |
| POST | /api/v1/relationships/{relationship_id}/confirm | Confirm relationship |
| POST | /api/v1/relationships/{relationship_id}/reject | Reject relationship |
| DELETE | /api/v1/relationships/{relationship_id} | Remove relationship |
| GET | /api/v1/relationships | List relationship requests and graph edges |

### Tree

| Method | Path | Summary |
| --- | --- | --- |
| GET | /api/v1/tree | Get family tree |
| GET | /api/v1/tree/ancestors | Get ancestor tree |
| GET | /api/v1/tree/descendants | Get descendant tree |
| GET | /api/v1/tree/{person_id}/branch | Expand branch |
| GET | /api/v1/tree/{person_id}/siblings | Get siblings |
| GET | /api/v1/tree/{person_id}/cousins | Get cousins |
| GET | /api/v1/tree/completeness | Get family completeness score |

### Invitations

| Method | Path | Summary |
| --- | --- | --- |
| POST | /api/v1/invitations | Create invite |
| POST | /api/v1/invitations/email | Create email invite |
| POST | /api/v1/invitations/sms | Create SMS invite |
| POST | /api/v1/invitations/link | Generate invite link |
| POST | /api/v1/invitations/qr | Generate QR invite |
| POST | /api/v1/invitations/{invite_id}/accept | Accept invite |
| POST | /api/v1/invitations/{invite_id}/decline | Decline invite |

### Notifications

| Method | Path | Summary |
| --- | --- | --- |
| GET | /api/v1/notifications | List notifications |
| PATCH | /api/v1/notifications/{notification_id}/read | Mark as read |
| PATCH | /api/v1/notifications/read-all | Mark all read |
| GET | /api/v1/notifications/unread-count | Unread count |

### Search

| Method | Path | Summary |
| --- | --- | --- |
| GET | /api/v1/search | Search members |
| GET | /api/v1/search/name | Search by name |
| GET | /api/v1/search/email | Search by email |
| GET | /api/v1/search/discovery | Family discovery search |

### Privacy

| Method | Path | Summary |
| --- | --- | --- |
| GET | /api/v1/privacy | Get privacy settings |
| PATCH | /api/v1/privacy | Update privacy settings |
| GET | /api/v1/privacy/visibility | Get visibility filters |

### Contact discovery

| Method | Path | Summary |
| --- | --- | --- |
| POST | /api/v1/contact-discovery/upload | Upload phone contacts |
| POST | /api/v1/contact-discovery/match | Match existing users |

## B. OpenAPI specification

The application exposes a FastAPI OpenAPI document under `/openapi.json` and a Swagger UI under `/docs`.

Key metadata:

- Title: `KinVerse API`
- Version: `0.1.0`
- Description: `Modular monolith API for family relationships and invitations`
- Tags: `auth`, `users`, `profiles`, `relationships`, `tree`, `invitations`, `notifications`, `search`, `privacy`

### Example schema shape

```yaml
openapi: 3.1.0
info:
  title: KinVerse API
  version: 0.1.0
paths:
  /api/v1/auth/login:
    post:
      tags: [auth]
      summary: Login
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/LoginRequest'
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TokenResponse'
components:
  schemas:
    LoginRequest:
      type: object
      required: [email, password]
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          format: password
    TokenResponse:
      type: object
      required: [access_token, refresh_token]
      properties:
        access_token:
          type: string
        refresh_token:
          type: string
        token_type:
          type: string
          example: bearer
```

## C. Error schema

```yaml
ErrorResponse:
  type: object
  required: [error, message, status_code]
  properties:
    error:
      type: string
      example: validation_error
    message:
      type: string
      example: A required field is missing.
    status_code:
      type: integer
      example: 422
    details:
      type: object
      nullable: true
```

## D. Design decisions

- All response models are explicit to keep mobile clients stable.
- Graph-derived labels are returned only in computed DTOs, never persisted in the database.
- Paginated responses use `page`, `page_size`, `total`, and `items` fields.
- Search endpoints support server-side filtering and lazy loading for large result sets.

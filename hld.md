# High-Level Design

This document describes the database schema, API contract, and architecture for the blog application defined in `requirements.md`.

The system supports:
- User signup, login, and logout.
- Creating, editing, and deleting blog entries.
- Setting title and text content for each blog post.
- Viewing a public feed of recently posted blogs.
- Creating, editing, and deleting comments on blog posts.

## Database Schema

All tables include:
- `created_at TIMESTAMPTZ NOT NULL DEFAULT now()`
- `updated_at TIMESTAMPTZ NOT NULL DEFAULT now()`

### `users`

Django's built-in `auth_user` table. No custom model.

- `id BIGINT PRIMARY KEY` (Django default `BigAutoField`)
- `username VARCHAR(150) NOT NULL UNIQUE` — enforced to 3–30 lowercase alphanumeric chars via validation
- `first_name VARCHAR(150) NOT NULL` — used as the display `name` field in all API responses
- `password VARCHAR(128) NOT NULL` — stored as Django's hashed password string

Note: `first_name` is mapped to `name` in all serializer output. All other built-in fields (`last_name`, `email`, etc.) are unused by the API.

### `blogs`

Stores blog posts authored by users. Public read URLs use globally unique slugs, while write operations use blog `id`.

- `id BIGINT PRIMARY KEY` (Django default `BigAutoField`)
- `user_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE`
- `title VARCHAR(200) NOT NULL`
- `slug VARCHAR(220) NOT NULL UNIQUE`
- `content TEXT NOT NULL`
- `INDEX blogs_created_at_idx (created_at DESC)`

Notes:
- Slug uniqueness is global, not per-user.
- Slug is immutable after blog creation.

### `comments`

Stores comments posted by users on blogs.

- `id BIGINT PRIMARY KEY` (Django default `BigAutoField`)
- `user_id BIGINT NOT NULL REFERENCES auth_user(id) ON DELETE CASCADE`
- `blog_id BIGINT NOT NULL REFERENCES blogs(id) ON DELETE CASCADE`
- `content TEXT NOT NULL`
- `INDEX comments_blog_id_created_at_idx (blog_id, created_at DESC)`

Notes:
- Comment deletion uses hard delete.

### Sessions (Redis)

Authentication uses cookie-based sessions stored in Redis.
These will be designed according to the choosen session management framework. 

## API Contract

### API Conventions

- Base path: `/api`
- Content type: `application/json`
- Auth mechanism: secure HTTP-only session cookie
- Public endpoints: feed, blog read endpoints, and `GET /api/health`
- Protected endpoints: create/update/delete for blogs and comments, logout, and `GET /user`
- Blog resource keys: use `slug` for `GET /api/blog/:slug`; use `id` for blog/comment write endpoints
- Pagination style: page + fixed page size
- Validation failures return `422` and use the standard error shape.

### Standard Error Format

For request validation failures, the API follows Django REST Framework serializer error format:

```json
{
  "name": [
    "This field may not be blank."
  ],
  "username": [
    "This field must be lowercase alphanumeric."
  ],
  "non_field_errors": [
    "Unable to create user with the provided data."
  ]
}
```

General guidance:
- Each key is a serializer field name, and the value is an array of error messages.
- `non_field_errors` contains object-level validation errors.
- Error message text should remain stable and user-friendly.

### Common Status Codes (generate guide, use django defualt if it makes sense)

- `200 OK`: successful read/update/login/logout
- `201 Created`: successful create
- `204 No Content`: successful delete with empty response
- `400 Bad Request`: malformed request
- `401 Unauthorized`: no valid session
- `403 Forbidden`: authenticated but not allowed
- `404 Not Found`: resource missing
- `409 Conflict`: uniqueness conflicts (username/slug)
- `422 Unprocessable Entity`: validation failures
- `503 Service Unavailable`: dependency unhealthy (for example database or Redis unreachable)
- `500 Internal Server Error`: unexpected server error

---

## Health Endpoint

### `GET /api/health`

Liveness-style check for operators and load balancers. No authentication required.

The handler verifies:

- **Database**: a trivial query (for example `SELECT 1`) against PostgreSQL succeeds.
- **Redis**: a trivial operation (for example `PING` or a short-lived read) succeeds.

Success response (`200 OK`) when both checks pass:

```json
{
  "status": "ok",
  "database": "ok",
  "redis": "ok"
}
```

Failure response (`503 Service Unavailable`) when either dependency fails. The payload indicates which checks failed (exact shape is implementation-defined but should be stable), for example:

```json
{
  "status": "unavailable",
  "database": "error",
  "redis": "ok"
}
```

Possible errors:

- `503` if PostgreSQL or Redis is unreachable or errors during the check.
- `500` only for unexpected failures outside those checks.

---

## User Endpoints

### `POST /api/user`

Creates a new user account.

Request body:
```json
{
  "name": "Ada Lovelace",
  "username": "ada",
  "password": "strong-password"
}
```

Success response (`201 Created`):
```json
{
  "id": 1,
  "name": "Ada Lovelace",
  "username": "ada",
  "created_at": "2026-05-04T20:00:00.000Z"
}
```

Possible errors:
- `409` if `username` already exists.
- `422` for validation errors.

### `POST /api/login`

Authenticates user credentials and creates a Redis-backed session.

Request body:
```json
{
  "username": "ada",
  "password": "strong-password"
}
```

Success response (`200 OK`):
```json
{
  "message": "Logged in successfully",
  "user": {
    "id": 1,
    "name": "Ada Lovelace",
    "username": "ada"
  }
}
```

Possible errors:
- `401` for invalid credentials.
- `422` for validation errors.

### `POST /api/logout`

Deletes the current session from Redis and clears the cookie.
This endpoint invalidates only the current session (current device/browser).

Request body:
- none

Success response (`200 OK`):
```json
{
  "message": "Logged out successfully"
}
```

Possible errors:
- `401` if there is no active session.

### `GET /api/user`

Returns the currently logged-in user.

Request body:
- none

Success response (`200 OK`):
```json
{
  "id": 1,
  "name": "Ada Lovelace",
  "username": "ada"
}
```

Possible errors:
- `401` if unauthenticated.

---

## Blog Endpoints

### `POST /api/blog`

Creates a blog post owned by the authenticated user.

Request body:
```json
{
  "title": "My first post",
  "slug": "my-first-post",
  "content": "Long-form blog content"
}
```

Success response (`201 Created`):
```json
{
  "id": 1,
  "title": "My first post",
  "slug": "my-first-post",
  "content": "Long-form blog content",
  "author": {
    "id": 1,
    "name": "Ada Lovelace",
    "username": "ada"
  },
  "created_at": "2026-05-04T20:10:00.000Z",
  "updated_at": "2026-05-04T20:10:00.000Z"
}
```

Possible errors:
- `401` if unauthenticated.
- `409` if `slug` is already in use.
- `422` for validation errors.

### `PUT /api/blog/:id`

Updates an existing blog post. Only the owner can update.

Request body:
```json
{
  "title": "My first post (edited)",
  "content": "Updated long-form blog content"
}
```

Success response (`200 OK`):
```json
{
  "id": 1,
  "title": "My first post (edited)",
  "slug": "my-first-post",
  "content": "Updated long-form blog content",
  "updated_at": "2026-05-04T21:00:00.000Z"
}
```

Possible errors:
- `401` if unauthenticated.
- `403` if not the owner.
- `404` if blog is not found.
- `422` for validation errors.

### `DELETE /api/blog/:id`

Deletes a blog post. Only the owner can delete.

Request body:
- none

Success response (`204 No Content`):
- empty body

Possible errors:
- `401` if unauthenticated.
- `403` if not the owner.
- `404` if blog is not found.

### `GET /api/blog/:slug`

Returns a public blog detail view including comments.
For now, all comments are returned in a single response (no comment pagination yet).

Request body:
- none

Success response (`200 OK`):
```json
{
  "id": 1,
  "title": "My first post",
  "slug": "my-first-post",
  "content": "Long-form blog content",
  "author": {
    "id": 1,
    "name": "Ada Lovelace",
    "username": "ada"
  },
  "created_at": "2026-05-04T20:10:00.000Z",
  "updated_at": "2026-05-04T20:10:00.000Z",
  "comments": [
    {
      "id": 2,
      "content": "Great post!",
      "author": {
        "id": 2,
        "name": "Grace Hopper",
        "username": "grace"
      },
      "created_at": "2026-05-04T20:15:00.000Z",
      "updated_at": "2026-05-04T20:15:00.000Z"
    }
  ]
}
```

Possible errors:
- `404` if blog is not found.

---

## Comment Endpoints

### `POST /api/blog/:id/comment`

Creates a comment on a blog post.

Request body:
```json
{
  "content": "Great post!"
}
```

Success response (`201 Created`):
```json
{
  "id": 2,
  "blog_id": 1,
  "content": "Great post!",
  "author": {
    "id": 2,
    "name": "Grace Hopper",
    "username": "grace"
  },
  "created_at": "2026-05-04T20:15:00.000Z",
  "updated_at": "2026-05-04T20:15:00.000Z"
}
```

Possible errors:
- `401` if unauthenticated.
- `404` if blog is not found.
- `422` for validation errors.

### `PUT /api/blog/:id/comment/:commentId`

Updates a comment. Only the comment owner can update.

Request body:
```json
{
  "content": "Great post! I learned a lot."
}
```

Success response (`200 OK`):
```json
{
  "id": 2,
  "content": "Great post! I learned a lot.",
  "updated_at": "2026-05-04T20:20:00.000Z"
}
```

Possible errors:
- `401` if unauthenticated.
- `403` if not the owner.
- `404` if comment or blog is not found.
- `422` for validation errors.

### `DELETE /api/blog/:id/comment/:commentId`

Hard-deletes a comment. Only the comment owner can delete.

Request body:
- none

Success response (`204 No Content`):
- empty body

Possible errors:
- `401` if unauthenticated.
- `403` if not the owner.
- `404` if comment or blog is not found.

---

## Feed Endpoint

### `GET /api/feed?page=<int>`

Returns the latest public blogs in reverse chronological order.

Pagination behavior:
- Fixed page size (server-configured constant, for example `20`).
- `page` starts at `1`.

Success response (`200 OK`):
```json
{
  "page": 1,
  "page_size": 20,
  "total_items": 145,
  "total_pages": 8,
  "items": [
    {
      "title": "My first post",
      "slug": "my-first-post",
      "comment_count": 12,
      "author": {
        "name": "Ada Lovelace",
        "username": "ada"
      },
      "created_at": "2026-05-04T20:10:00.000Z",
      "updated_at": "2026-05-04T20:10:00.000Z"
    }
  ]
}
```

Possible errors:
- `400` if `page` is invalid.

## Architecture

The system uses a simple client-server model and RESTful APIs.

### Backend

The backend is a Django API server built with Django REST Framework. PostgreSQL is the source of truth for persistent application data. Redis stores session state for cookie-based authentication. The Next.js frontend runs as a separate service and calls the API server for data operations.

- Use Django's built-in `User` model. `first_name` is the display name (`name` in all API responses).
- Integer primary keys (`BigAutoField`) throughout. No UUIDs.
- All application code (models, services, serializers, views, URLs, tests) lives in the `blog` app.
- Use DRF class-based views with permission classes.
- Layered architecture: `views → services → models`. Services own all business logic and ORM queries. Views validate input via DRF serializers and translate output.

### Frontend

The frontend is a Next.js application. It can use a mix of SSR and CSR depending on the page type. Public pages such as feed and blog detail can be server-rendered for better SEO, while authenticated interactions can use client-side API calls.

## Finalized Decisions

1. Integer primary keys (`BigAutoField`) are used for all tables. No UUIDs.
2. Django's built-in `User` model is used. `first_name` stores the display name and is exposed as `name` in all API responses.
3. Usernames are lowercase alphanumeric only (`^[a-z0-9]+$`), unique, and limited to 30 characters. Enforced via serializer validation, not a DB constraint.
4. Blog slugs are globally unique and immutable after blog creation.
5. Validation limits are:
   - `name` (`first_name`): 1 to 100 characters
   - `username`: 3 to 30 characters, lowercase alphanumeric only
   - `password`: 8 to 128 characters
   - `title`: 1 to 200 characters
   - `content`: 1 to 20000 characters
   - `comment.content`: 1 to 2000 characters
6. `GET /api/blog/:slug` returns all comments for now (no comment pagination yet).
7. Logout invalidates only the current session (current device/browser).
8. Validation failures use status `422`.
9. All application code lives in the `blog` app. No separate `users` or `core` apps.
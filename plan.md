# Build Plan

Step-by-step execution plan for the blog REST API. Each step builds one layer and is independently completable.

Status values: `pending` | `in_progress` | `done`

Constraints:
- Integer primary keys (Django default `BigAutoField`).
- Django's built-in `User` model (`django.contrib.auth.models.User`). Map `first_name` to `name` in serializers.
- Everything lives inside the `blog` app: models, services, serializers, views, urls, tests.

---

## Layer 1: Models

### Step 1 — Blog & Comment Models `[done]`

**Tasks:**
- In `blog/models.py`, define:
  - `Blog`:
    - `id`: auto `BigAutoField` (default, no override needed)
    - `user`: `ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE)`
    - `title`: `CharField(max_length=200)`
    - `slug`: `SlugField(max_length=220, unique=True)`
    - `content`: `TextField()`
    - `created_at`: `DateTimeField(auto_now_add=True)`
    - `updated_at`: `DateTimeField(auto_now=True)`
    - `Meta`: `Index(fields=["-created_at"], name="blogs_created_at_idx")`
  - `Comment`:
    - `id`: auto `BigAutoField` (default)
    - `user`: `ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE)`
    - `blog`: `ForeignKey(Blog, on_delete=CASCADE, related_name="comments")`
    - `content`: `TextField()`
    - `created_at`: `DateTimeField(auto_now_add=True)`
    - `updated_at`: `DateTimeField(auto_now=True)`
    - `Meta`: `Index(fields=["blog", "-created_at"], name="comments_blog_created_at_idx")`
- Generate and apply migrations: `makemigrations blog`, `migrate`.

**Files to create/edit:**
- `app/blog/models.py`
- `app/blog/migrations/`

---

## Layer 2: Services
### Step 2 — User Services `[done]`

Services contain all business logic. Views must not query the ORM directly.

Define shared service exceptions at the top of `app/blog/services.py`:
- `class ConflictError(Exception): pass`
- `class NotFoundError(Exception): pass`
- `class ForbiddenError(Exception): pass`


Add to `app/blog/services.py`:

- `create_user(name, username, password) -> User`
  - Validate username regex (`^[a-z0-9]{3,30}$`); raise `ValidationError` if invalid.
  - Check uniqueness; raise `ConflictError` if username taken.
  - Call `User.objects.create_user(username=username, password=password, first_name=name)`.
  - Return created `User`.

**Files to create/edit:**
- `app/blog/services.py`

---

### Step 3 — Service Split: Exceptions + User Service `[done]`

Split the existing `app/blog/services.py` implementation from Step 2 into dedicated files:

- Create `app/blog/services/exceptions.py` with:
  - `class ConflictError(Exception): pass`
  - `class NotFoundError(Exception): pass`
  - `class ForbiddenError(Exception): pass`
- Create `app/blog/services/user_service.py` with:
  - `create_user(name, username, password) -> User` (same behavior as Step 2)
- Create `app/blog/services/__init__.py` and export:
  - `ConflictError`, `NotFoundError`, `ForbiddenError`
  - `create_user`

After this split, add all new service logic to domain-specific files under `app/blog/services/`.

**Files to create/edit:**
- `app/blog/services/exceptions.py`
- `app/blog/services/user_service.py`
- `app/blog/services/__init__.py`

---

### Step 4 — Blog Services `[done]`

Add to `app/blog/services/blog_service.py`:

- `create_blog(user, title, slug, content) -> Blog`
  - Check slug uniqueness; raise `ConflictError` if taken.
  - Create and return `Blog`.
- `update_blog(blog_id, user, title, content) -> Blog`
  - Fetch blog; raise `NotFoundError` if missing.
  - Check ownership; raise `ForbiddenError` if not owner.
  - Update `title`, `content`; save and return.
- `delete_blog(blog_id, user) -> None`
  - Fetch blog; raise `NotFoundError` if missing.
  - Check ownership; raise `ForbiddenError` if not owner.
  - Delete.
- `get_blog_by_slug(slug) -> Blog`
  - Use `prefetch_related("comments__user")` to avoid N+1 on the comments list.
  - Raise `NotFoundError` if missing.
- `get_feed(page, page_size=20) -> dict`
  - Return `{page, page_size, total_items, total_pages, items}`.
  - Order by `-created_at`; annotate each blog with `comment_count` via `Count("comments")`.
  - Raise `ValueError` for `page < 1`.

Import `ConflictError`, `NotFoundError`, and `ForbiddenError` from `app/blog/services/exceptions.py`.

**Files to create/edit:**
- `app/blog/services/blog_service.py`
- `app/blog/services/__init__.py`

---

### Step 5 — Comment Services `[done]`

Add to `app/blog/services/comment_service.py`:

- `create_comment(blog_id, user, content) -> Comment`
  - Fetch blog; raise `NotFoundError` if blog missing.
  - Create and return `Comment`.
- `update_comment(blog_id, comment_id, user, content) -> Comment`
  - Fetch blog; raise `NotFoundError` if blog missing.
  - Fetch comment scoped to that blog; raise `NotFoundError` if comment missing.
  - Check ownership; raise `ForbiddenError` if not owner.
  - Update and return.
- `delete_comment(blog_id, comment_id, user) -> None`
  - Fetch blog; raise `NotFoundError` if blog missing.
  - Fetch comment scoped to that blog; raise `NotFoundError` if comment missing.
  - Check ownership; raise `ForbiddenError` if not owner.
  - Hard delete.

Import `NotFoundError` and `ForbiddenError` from `app/blog/services/exceptions.py`.

**Files to create/edit:**
- `app/blog/services/comment_service.py`
- `app/blog/services/__init__.py`

---

### Step 6 — Health Service `[done]`

Add to `app/blog/services/health_service.py`:

- `check_health() -> dict`
  - Run `SELECT 1` via `connection.cursor()`; mark `database: "ok"` or `"error"`.
  - Run Redis `PING` via `django_redis.get_redis_connection("default")`; mark `redis: "ok"` or `"error"`.
  - Return `{status: "ok"|"unavailable", database: ..., redis: ...}`.
  - Set overall `status` to `"unavailable"` if either check fails.

**Files to create/edit:**
- `app/blog/services/health_service.py`
- `app/blog/services/__init__.py`

---

## Layer 3: Serializers

Serializers handle input validation and output shaping only. No business logic here.

### Step 7 — All Serializers `[done]`

Create `app/blog/serializers.py`:

**User serializers:**
- `UserCreateSerializer(Serializer)` — input for `POST /api/user`
  - `name` (CharField, 1–100)
  - `username` (CharField, 3–30, regex `^[a-z0-9]+$`)
  - `password` (CharField, 8–128, `write_only=True`)
- `UserOutputSerializer(Serializer)` — output for user responses
  - `id`, `name` (sourced from `first_name`), `username`, `date_joined` (as `created_at`), `last_login` (as `updated_at`)
  - Note: Django's `User` has no `updated_at`; use `date_joined` for `created_at` and omit `updated_at` or expose `last_login`.
- `LoginSerializer(Serializer)` — input for `POST /api/login`
  - `username`, `password`

**Blog serializers:**
- `AuthorSerializer(Serializer)` — `{id, name, username}` nested in blog/comment output
- `BlogCreateSerializer(Serializer)` — input for `POST /api/blog`
  - `title` (1–200), `slug` (1–220, valid slug chars), `content` (1–20000)
- `BlogUpdateSerializer(Serializer)` — input for `PUT /api/blog/:id`
  - `title` (1–200), `content` (1–20000)
- `BlogWriteOutputSerializer(Serializer)` — output for `POST` and `PUT` blog
  - `id`, `title`, `slug`, `content`, `author` (nested `AuthorSerializer`), `created_at`, `updated_at`
- `BlogDetailSerializer(Serializer)` — output for `GET /api/blog/:slug`
  - All fields of `BlogWriteOutputSerializer` plus `comments` (list of `CommentOutputSerializer`)
- `FeedItemSerializer(Serializer)` — single item in feed list
  - `id`, `title`, `slug`, `comment_count`, `author` (nested), `created_at`, `updated_at`
- `FeedOutputSerializer(Serializer)` — full paginated feed response
  - `page`, `page_size`, `total_items`, `total_pages`, `items` (list of `FeedItemSerializer`)

**Comment serializers:**
- `CommentCreateSerializer(Serializer)` — input: `content` (1–2000)
- `CommentUpdateSerializer(Serializer)` — input: `content` (1–2000)
- `CommentOutputSerializer(Serializer)` — `id`, `blog_id`, `content`, `author` (nested), `created_at`, `updated_at`

**Files to create/edit:**
- `app/blog/serializers.py`

---

## Layer 4: Views

Class-based views using DRF. Views validate input (via serializers), call services, and format output. Permission classes enforce auth.
Import service functions/exceptions from `app/blog/services/__init__.py` exports (backed by split files under `app/blog/services/`).

### Step 8 — Health View `[done]`

In `app/blog/views.py`:

- `HealthView(APIView)` — `GET /api/health`
  - `permission_classes = [AllowAny]`
  - Call `check_health()`; return 200 if `status == "ok"`, else 503.

---

### Step 9 — User Views `[done]`

In `app/blog/views.py`:

- `UserCreateView(APIView)` — `POST /api/user`
  - `permission_classes = [AllowAny]`
  - Validate with `UserCreateSerializer`; raise 422 on invalid input.
  - Call `create_user()`; handle `ConflictError` → 409.
  - Return `UserOutputSerializer` data with status 201.
- `UserDetailView(APIView)` — `GET /api/user`
  - `permission_classes = [IsAuthenticated]`
  - Return `UserOutputSerializer(request.user)` with status 200.
- `LoginView(APIView)` — `POST /api/login`
  - `permission_classes = [AllowAny]`
  - Validate with `LoginSerializer`.
  - Call `authenticate(request, username=..., password=...)`; return 401 on `None`.
  - Call `login(request, user)` to create session.
  - Return `{message, user: UserOutputSerializer(...)}` with status 200.
- `LogoutView(APIView)` — `POST /api/logout`
  - `permission_classes = [IsAuthenticated]`
  - Call `logout(request)`.
  - Return `{"message": "Logged out successfully"}` with status 200.

---

### Step 10 — Blog Views `[done]`

In `app/blog/views.py`:

- `BlogCreateView(APIView)` — `POST /api/blog`
  - `permission_classes = [IsAuthenticated]`
  - Validate with `BlogCreateSerializer`.
  - Call `create_blog()`; handle `ConflictError` → 409.
  - Return `BlogWriteOutputSerializer` with status 201.
- `BlogDetailView(APIView)` — `GET /api/blog/<slug:slug>`
  - `permission_classes = [AllowAny]`
  - Call `get_blog_by_slug()`; handle `NotFoundError` → 404.
  - Return `BlogDetailSerializer` with status 200.
- `BlogUpdateDeleteView(APIView)` — `PUT /api/blog/<int:pk>`, `DELETE /api/blog/<int:pk>`
  - `permission_classes = [IsAuthenticated]`
  - `put`: validate with `BlogUpdateSerializer`, call `update_blog()`.
    - Handle `NotFoundError` → 404, `ForbiddenError` → 403.
    - Return `BlogWriteOutputSerializer` with status 200.
  - `delete`: call `delete_blog()`.
    - Handle `NotFoundError` → 404, `ForbiddenError` → 403.
    - Return 204 with empty body.

---

### Step 11 — Comment Views `[done]`

In `app/blog/views.py`:

- `CommentCreateView(APIView)` — `POST /api/blog/<int:blog_pk>/comment`
  - `permission_classes = [IsAuthenticated]`
  - Validate with `CommentCreateSerializer`.
  - Call `create_comment()`; handle `NotFoundError` → 404.
  - Return `CommentOutputSerializer` with status 201.
- `CommentUpdateDeleteView(APIView)` — `PUT /api/blog/<int:blog_pk>/comment/<int:pk>`, `DELETE ...`
  - `permission_classes = [IsAuthenticated]`
  - `put`: validate with `CommentUpdateSerializer`, call `update_comment()`.
    - Handle `NotFoundError` → 404, `ForbiddenError` → 403.
    - Return `CommentOutputSerializer` with status 200.
  - `delete`: call `delete_comment()`.
    - Handle `NotFoundError` → 404, `ForbiddenError` → 403.
    - Return 204 with empty body.

---

### Step 12 — Feed View `[done]`

In `app/blog/views.py`:

- `FeedView(APIView)` — `GET /api/feed?page=<int>`
  - `permission_classes = [AllowAny]`
  - Parse `page` query param (default `1`); return 400 if not a positive integer.
  - Call `get_feed(page)`; return `FeedOutputSerializer` with status 200.

---

## Layer 5: URL Wiring

### Step 13 — URL Configuration `[done]`

Update `app/blog/urls.py` to wire all routes:

```
GET    /api/health                                  → HealthView
POST   /api/user                                    → UserCreateView
GET    /api/user                                    → UserDetailView
POST   /api/login                                   → LoginView
POST   /api/logout                                  → LogoutView
GET    /api/feed                                    → FeedView
POST   /api/blog                                    → BlogCreateView
GET    /api/blog/<slug:slug>                        → BlogDetailView
PUT    /api/blog/<int:pk>                           → BlogUpdateDeleteView
DELETE /api/blog/<int:pk>                           → BlogUpdateDeleteView
POST   /api/blog/<int:blog_pk>/comment              → CommentCreateView
PUT    /api/blog/<int:blog_pk>/comment/<int:pk>     → CommentUpdateDeleteView
DELETE /api/blog/<int:blog_pk>/comment/<int:pk>     → CommentUpdateDeleteView
```

`app/app/urls.py` already includes `blog.urls` under `/api/` — no change needed there.

**Files to create/edit:**
- `app/blog/urls.py`

---

## Layer 6: Tests

### Step 14 — High-Level API Tests `[done]`

Integration-style tests using DRF's `APIClient` against the full stack. All tests live in `app/blog/tests/`.

**Test modules and cases:**

#### `blog/tests/test_health.py`
- `GET /api/health` — returns 200 with `{status: "ok", database: "ok", redis: "ok"}` when both deps are up.

#### `blog/tests/test_user.py`
- `POST /api/user` — creates user, returns 201 with correct shape (`id`, `name`, `username`).
- `POST /api/user` — returns 409 on duplicate username.
- `POST /api/user` — returns 422 on username with uppercase or special chars.
- `POST /api/user` — returns 422 on password shorter than 8 chars.
- `POST /api/user` — returns 422 on missing required fields.
- `POST /api/login` — returns 200 and sets session cookie on valid credentials.
- `POST /api/login` — returns 401 on wrong password.
- `POST /api/logout` — returns 200 when logged in.
- `POST /api/logout` — returns 401 when unauthenticated.
- `GET /api/user` — returns 200 with user data when authenticated.
- `GET /api/user` — returns 401 when unauthenticated.

#### `blog/tests/test_blog.py`
- `POST /api/blog` — creates blog, returns 201 with nested `author`.
- `POST /api/blog` — returns 409 on duplicate slug.
- `POST /api/blog` — returns 401 when unauthenticated.
- `POST /api/blog` — returns 422 on blank title or content.
- `PUT /api/blog/:id` — updates title and content, returns 200; slug is unchanged.
- `PUT /api/blog/:id` — returns 403 when non-owner updates.
- `PUT /api/blog/:id` — returns 404 when blog does not exist.
- `DELETE /api/blog/:id` — deletes blog, returns 204.
- `DELETE /api/blog/:id` — returns 403 when non-owner deletes.
- `DELETE /api/blog/:id` — returns 404 when blog does not exist.
- `GET /api/blog/:slug` — returns blog with nested `comments` list.
- `GET /api/blog/:slug` — returns 404 when blog does not exist.

#### `blog/tests/test_comment.py`
- `POST /api/blog/:id/comment` — creates comment, returns 201 with nested `author`.
- `POST /api/blog/:id/comment` — returns 401 when unauthenticated.
- `POST /api/blog/:id/comment` — returns 404 when blog does not exist.
- `POST /api/blog/:id/comment` — returns 422 on blank content.
- `PUT /api/blog/:id/comment/:cid` — updates comment, returns 200.
- `PUT /api/blog/:id/comment/:cid` — returns 403 for non-owner.
- `PUT /api/blog/:id/comment/:cid` — returns 404 when comment does not exist.
- `DELETE /api/blog/:id/comment/:cid` — deletes comment, returns 204.
- `DELETE /api/blog/:id/comment/:cid` — returns 403 for non-owner.

#### `blog/tests/test_feed.py`
- `GET /api/feed` — returns 200 with correct paginated shape.
- `GET /api/feed?page=1` — `total_items` and `total_pages` are accurate.
- `GET /api/feed?page=99` — returns 200 with empty `items` (not 404).
- `GET /api/feed?page=0` — returns 400.
- `GET /api/feed?page=abc` — returns 400.
- Feed items include `comment_count`.

**Setup:**
- Use `pytest-django` as the test runner with `APIClient`.
- All tests use the test DB; no mocking of DB or Redis except in the health check test.

**Files to create:**
- `app/blog/tests/__init__.py`
- `app/blog/tests/test_health.py`
- `app/blog/tests/test_user.py`
- `app/blog/tests/test_blog.py`
- `app/blog/tests/test_comment.py`
- `app/blog/tests/test_feed.py`

---

## Layer 7: Routing Refactor

### Step 15 — DRF-Native Method Dispatch `[done]`

Refactor routing so each URL pattern maps directly to a DRF view (`.as_view()`) and let DRF handle method dispatch/405 responses natively.

In `app/blog/views.py`:

- Add `UserView(APIView)` that combines:
  - `POST /api/user` (registration behavior from `UserCreateView`)
  - `GET /api/user` (current-user behavior from `UserDetailView`)
  - Method-specific permissions via `get_permissions()`:
    - `POST` => `AllowAny`
    - `GET` => `IsAuthenticated`
- Replace split blog write/update-delete classes with route-oriented names:
  - `BlogView(APIView)` for `POST /api/blog`
  - `BlogByIdView(APIView)` for `PUT/DELETE /api/blog/<int:pk>`
- Keep existing single-route views unchanged (`HealthView`, `LoginView`, `LogoutView`, `FeedView`, `BlogDetailView`, comment views).

In `app/blog/urls.py`:

- Remove custom `map_methods(...)` helper and `HttpResponseNotAllowed` import.
- Route directly with `.as_view()` for each endpoint:
  - `/api/user` -> `UserView`
  - `/api/blog` -> `BlogView`
  - `/api/blog/<int:pk>` -> `BlogByIdView`
  - Other routes remain direct `APIView` mappings.

Validation:

- Lint edited files (`app/blog/views.py`, `app/blog/urls.py`) with no errors.
- Confirm no runtime references remain to `map_methods`.
- Run tests via Django test command:
  - `uv run python app/manage.py test --settings=app.settings.test`
  - Current project state reports `0` discovered tests and exits cleanly.

**Files to create/edit:**
- `app/blog/views.py`
- `app/blog/urls.py`

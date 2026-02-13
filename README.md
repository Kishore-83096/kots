# KOTS Flask Backend

## Summary
This project is a modular Flask REST API for a rental/property workflow with three role scopes:
- `user`: registration/login, profile management, building/tower/flat browsing, and booking creation.
- `admin`: CRUD over buildings/towers/flats/amenities and booking management for owned buildings.
- `master`: privileged admin creation and admin listing.

The application uses JWT-based auth, SQLAlchemy ORM, Alembic migrations, and optional Cloudinary image upload for profile and property assets.

## Why This Application Is Used
This application is used to manage the full rental discovery and booking flow for apartment communities (buildings/residencies, towers, and flats) in one system.

It is built to solve three practical needs:
- Users can quickly discover available flats by location, type, and rent range, then place bookings.
- Admins can manage property inventory (buildings, towers, flats, amenities) and control booking approvals.
- Master users can control platform-level operations by creating and supervising admin accounts.

In short, it reduces manual coordination between tenants and property managers by providing a structured, role-based rental workflow with searchable inventory and trackable booking status.

## Directory Structure
```text
flask/
  app.py                     # App factory, blueprint registration, root + health endpoints
  run.py                     # Local run entrypoint
  config.py                  # Environment-driven configuration
  extensions.py              # SQLAlchemy, Migrate, JWT singletons
  requirements.txt           # Python dependency lock list
  .env                       # Local environment variables (not for public sharing)

  common/
    response.py              # Unified success/error response envelope + payload size metadata
    permissions.py           # Role-based route guard decorator using JWT identity
    error_handlers.py        # Global HTTP and unhandled exception handlers
    __init__.py

  users/
    routes_users.py          # User-facing endpoints
    services_users.py        # User business logic
    schemas_users.py         # User payload validation + serialization
    models_users.py          # RegistrationUser + UserProfile models
    __init__.py

  admins/
    routes_admins.py         # Admin-facing endpoints
    services_admins.py       # Admin business logic
    schemas_admins.py        # Admin payload validation + serialization
    models_admins.py         # Building, Tower, Flat, Amenity, Booking models + relation table
    __init__.py

  master/
    routes_master.py         # Master-facing endpoints
    services_master.py       # Master business logic
    schemas_master.py        # Master payload validation + serialization
    models_master.py         # Placeholder for master-specific models
    __init__.py

  migrations/               # Alembic migration environment + revision history
  venv/                     # Local virtual environment
```

## Tech Stack
- Python 3.x
- Flask 3.x
- Flask-SQLAlchemy (ORM)
- SQLAlchemy 2.x
- Flask-Migrate + Alembic (database migrations)
- Flask-JWT-Extended (authentication)
- PostgreSQL driver via `psycopg`
- Cloudinary SDK (image upload and asset deletion)
- python-dotenv (environment loading)

## Core Architecture
- API routes are split by domain into blueprints:
  - `/users`
  - `/admins`
  - `/master`
- Route layer is thin: each route calls a service and returns a standard response shape.
- Service layer implements validation, authorization checks, DB operations, and business rules.
- Schema layer handles validation and response serialization.
- Common layer provides reusable response contracts, error handling, and role guards.

## Configuration
Configured in `config.py` via `.env`:
- `DEBUG`
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `CLOUDINARY_URL`

## Authentication and Authorization
- JWT tokens are issued on `/users/register` and `/users/login`.
- Access token lifetime is configured to 5 hours.
- Identity stored in token is user ID (string).
- Role resolution is based on flags in `registration_users`:
  - `is_master -> master`
  - `is_admin -> admin`
  - else `user`
- `@role_required(...)` enforces role for admin/master routes.
- `@jwt_required()` protects logged-in user endpoints.

## Response Contract
All endpoints return a common envelope from `common/response.py`:
- Success
  - `status_code`
  - `success: true`
  - `message`
  - `data`
  - optional `size` (when `add_size=True`)
- Error
  - `status_code`
  - `success: false`
  - `message`
  - `error.detail`
  - `error.user_message`
  - `data: null`
  - optional `size`

## Main Modules Explained
- `users` module: account lifecycle, self profile, profile picture upload/removal, inventory discovery for end users, booking creation and booking read.
- `admins` module: property inventory management (building/tower/flat), amenity assignment, and booking status operations constrained to admin-owned buildings.
- `master` module: superuser-only admin management (create/list admins).
- `common` module: shared cross-cutting API behavior.

## API Documentation

### Global Endpoints

#### `GET /`
- Auth: none
- Description: service connectivity check.
- Success message: `Flask + Neon PostgreSQL connected`

#### `GET /health`
- Auth: none
- Description: generic service health endpoint.

---

### Users APIs (`/users`)

#### `GET /users/health`
- Auth: none
- Purpose: users module health.

#### `POST /users/register`
- Auth: none
- Body: `email`, `password`, optional `is_admin`, `is_master`
- Behavior:
  - validates required fields
  - creates account with hashed password
  - returns JWT token + resolved role
- Errors:
  - `400` missing fields
  - `409` email already registered

#### `POST /users/login`
- Auth: none
- Body: `email`, `password`
- Behavior: validates credentials and issues JWT.
- Errors:
  - `400` validation error
  - `401` invalid credentials

#### `GET /users/me`
- Auth: JWT required
- Purpose: basic account summary for current user.

#### `PUT /users/me`
- Auth: JWT required
- Body: at least one of `email` or `password`
- Purpose: update own account credentials.

#### `DELETE /users/me`
- Auth: JWT required
- Purpose: delete own account.

#### `POST /users/logout`
- Auth: JWT required
- Purpose: revoke the current access token (`jti`) and return logout success.

#### `GET /users/profile`
- Auth: JWT required
- Purpose: full profile payload including optional fields.

#### `PUT /users/profile`
- Auth: JWT required
- Body (any subset):
  - `username`, `mobile_number`, `profile_pic_url`, `profile_pic_public_id`, `profile_pic_folder`, `bio`, `date_of_birth`, `city`, `state`, `country`
- Rules:
  - `primary_email` cannot be updated
  - username uniqueness enforced
  - `date_of_birth` must be ISO-8601

#### `POST /users/profile/picture`
- Auth: JWT required
- Content-Type: `multipart/form-data`
- Form fields:
  - `file` (required)
  - `folder` (optional)
- Behavior: uploads image to Cloudinary, updates profile image fields, removes previous Cloudinary asset if replaced.

#### `DELETE /users/profile/picture`
- Auth: JWT required
- Behavior: clears profile image data and attempts Cloudinary delete.

#### `GET /users/buildings`
- Auth: JWT required
- Purpose: list buildings with counts (towers/flats/available flats) and amenities.

#### `GET /users/buildings/{building_id}`
- Auth: JWT required
- Purpose: get building detail with towers and amenities.

#### `GET /users/buildings/{building_id}/amenities`
- Auth: JWT required
- Purpose: list amenities for a building.

#### `GET /users/buildings/{building_id}/amenities/{amenity_id}`
- Auth: JWT required
- Purpose: get a single amenity for a building.

#### `GET /users/buildings/{building_id}/towers`
- Auth: JWT required
- Purpose: list towers for building.

#### `GET /users/buildings/{building_id}/towers/{tower_id}`
- Auth: JWT required
- Purpose: tower detail including building address metadata.

#### `GET /users/buildings/{building_id}/towers/{tower_id}/flats`
- Auth: JWT required
- Query:
  - `status`: `all|available|true|false` (optional)
  - `page`: integer >= 1 (optional, default `1`)
- Purpose: paginated flat listing (`per_page=10`).

#### `GET /users/flats/search`
- Auth: JWT required
- Query:
  - `address` (optional, partial match)
  - `city` (optional, partial match)
  - `state` (optional, partial match)
  - `flat_type` (optional, partial match against `bhk_type`)
  - `min_rent` (optional, numeric)
  - `max_rent` (optional, numeric)
  - `available_only` (optional, boolean, default `true`)
  - `page` (optional, default `1`)
  - `per_page` (optional, default `10`, max `100`)
- Purpose: paginated search for flats across buildings by location and rent range.

#### `GET /users/buildings/search`
- Auth: JWT required
- Query:
  - `name` (optional, partial match)
  - `address` (optional, partial match)
  - `city` (optional, partial match)
  - `state` (optional, partial match)
  - `page` (optional, default `1`)
  - `per_page` (optional, default `10`, max `100`)
- Purpose: paginated search for buildings/residencies by name and location.

#### `GET /users/buildings/{building_id}/towers/{tower_id}/flats/{flat_id}`
- Auth: JWT required
- Purpose: flat detail including building/tower context and amenities.

#### `POST /users/flats/{flat_id}/bookings`
- Auth: JWT required
- Purpose: create booking by marking security deposit paid.
- Behavior:
  - booking starts with status `PENDING`
  - captures `building_full_address` and optional username snapshot
- Errors:
  - `409` if current user already booked the same flat

#### `GET /users/bookings`
- Auth: JWT required
- Purpose: list all current user bookings with building/tower/flat summary and manager contact (`name`, `phone`).

#### `GET /users/bookings/{booking_id}`
- Auth: JWT required
- Purpose: single booking detail for current user, including manager contact (`name`, `phone`).

---

### Admin APIs (`/admins`)
All admin routes except `/admins/health` require role `admin` or `master`.

#### `GET /admins/health`
- Auth: none
- Purpose: admins module health.

#### `GET /admins/dashboard`
- Auth: admin/master
- Purpose: static dashboard scope payload.

#### `POST /admins/buildings`
- Auth: admin/master
- Body: JSON or multipart form
- Required: `name`, `address`, `city`, `state`, `pincode`
- Optional: `total_towers`, `file`, `folder`
- Purpose: create building under current admin ID.

#### `PUT /admins/buildings/{building_id}`
- Auth: admin/master
- Body: JSON or multipart form with any updatable building fields
- Purpose: update building and optionally replace image.

#### `PUT /admins/buildings`
- Auth: admin/master
- Body: must include `id` or `building_id`
- Purpose: alternate update endpoint using body ID.

#### `DELETE /admins/buildings/{building_id}`
- Auth: admin/master
- Rule: only owner admin can delete
- Behavior: cascades building/tower/flat/amenity deletion and Cloudinary asset cleanup.

#### `GET /admins/buildings/my`
- Auth: admin/master
- Purpose: list buildings owned by current admin.

#### `GET /admins/buildings/{building_id}`
- Auth: admin/master
- Purpose: get one owned building.

#### `POST /admins/buildings/{building_id}/towers`
- Auth: admin/master
- Body: JSON or multipart form
- Required: `name`, `floors`
- Optional: `total_flats`, `file`, `folder`
- Purpose: create tower under owned building.

#### `PUT /admins/towers/{tower_id}`
- Auth: admin/master
- Body: JSON or multipart form, at least one field among `name`, `floors`, `total_flats`
- Purpose: update tower and optionally replace image.

#### `GET /admins/buildings/{building_id}/towers`
- Auth: admin/master
- Purpose: list towers of an owned building.

#### `GET /admins/buildings/{building_id}/towers/{tower_id}`
- Auth: admin/master
- Purpose: get specific tower of an owned building.

#### `DELETE /admins/towers/{tower_id}`
- Auth: admin/master
- Rule: ownership required
- Behavior: deletes tower + dependent flats + associated images.

#### `POST /admins/towers/{tower_id}/flats`
- Auth: admin/master
- Body: JSON or multipart form
- Required: `flat_number`, `floor_number`, `bhk_type`, `area_sqft`, `rent_amount`, `security_deposit`
- Optional: `is_available`, `file`, `folder`
- Purpose: create flat in an owned tower.

#### `PUT /admins/flats/{flat_id}`
- Auth: admin/master
- Body: any flat updatable fields
- Purpose: update flat and optionally replace image.

#### `PUT /admins/towers/{tower_id}/flats/{flat_id}`
- Auth: admin/master
- Body: any flat updatable fields
- Purpose: update a specific flat under a specific owned tower and optionally replace image.

#### `GET /admins/towers/{tower_id}/flats`
- Auth: admin/master
- Purpose: list flats for owned tower.

#### `GET /admins/towers/{tower_id}/flats/{flat_id}`
- Auth: admin/master
- Purpose: get specific flat in tower.

#### `DELETE /admins/flats/{flat_id}`
- Auth: admin/master
- Purpose: delete owned flat and image.

#### `POST /admins/buildings/{building_id}/amenities`
- Auth: admin/master
- Body: JSON or multipart form
- Required: `name`
- Optional: `description`, `file`, `folder`
- Purpose: create amenity for owned building.

#### `GET /admins/buildings/{building_id}/amenities`
- Auth: admin/master
- Purpose: list amenities for owned building.

#### `PUT /admins/amenities/{amenity_id}`
- Auth: admin/master
- Body: JSON or multipart form, any of `name`, `description`, optional `file`, `folder`
- Purpose: update owned amenity and optionally replace image.

#### `PUT /admins/flats/{flat_id}/amenities`
- Auth: admin/master
- Body: `amenity_ids` (non-empty list)
- Purpose: replace flat amenity mapping, validated against same building.

#### `DELETE /admins/amenities/{amenity_id}`
- Auth: admin/master
- Purpose: delete owned amenity and image.

#### `GET /admins/bookings`
- Auth: admin/master
- Purpose: list bookings for buildings owned by admin.

#### `GET /admins/bookings/{booking_id}`
- Auth: admin/master
- Purpose: get one owned booking.

#### `PUT /admins/bookings/{booking_id}/status`
- Auth: admin/master
- Body: `status` in `PENDING|APPROVED|DECLINED`
- Purpose: update booking status.

---

### Master APIs (`/master`)
All master routes except `/master/health` require role `master`.

#### `GET /master/health`
- Auth: none
- Purpose: master module health.

#### `GET /master/control`
- Auth: master
- Purpose: static master scope payload.

#### `POST /master/create-admin`
- Auth: master
- Body: `email`, `password`
- Purpose: create a new admin account (`is_admin=True`, `is_master=False`).
- Errors:
  - `400` validation error
  - `409` duplicate email

#### `GET /master/admins`
- Auth: master
- Query:
  - `page` (default `1`)
  - `per_page` (default `10`, max `100`)
- Purpose: paginated list of admin users excluding current master identity.

## File-by-File Explanation

### `users/`
- `users/models_users.py`
  - `RegistrationUser`: login identity table, role flags, password hash methods.
  - `UserProfile`: one-to-one extension for user profile data and profile image metadata.
- `users/schemas_users.py`
  - input validators for registration/login/update/profile update.
  - serializers for user profile, property listing details, and booking payloads.
- `users/services_users.py`
  - core user business logic: auth, profile CRUD, Cloudinary upload/delete, listing buildings/towers/flats, booking create/read.
- `users/routes_users.py`
  - HTTP route definitions and service orchestration for users blueprint.
- `users/__init__.py`
  - package marker file.

### `admins/`
- `admins/models_admins.py`
  - `Building`, `Tower`, `Flat`, `Amenity`, `Booking` entities.
  - `flat_amenities` many-to-many join table.
  - cascade relationships for dependent cleanup.
- `admins/schemas_admins.py`
  - validators for building/tower/flat/amenity/booking status payloads.
  - serializers for admin views of entities and booking context.
- `admins/services_admins.py`
  - admin ownership checks, CRUD workflows, Cloudinary image handling, amenity mapping, and booking status management.
- `admins/routes_admins.py`
  - admin HTTP endpoints mapped to services with role guards.
- `admins/__init__.py`
  - package marker file.

### `master/`
- `master/models_master.py`
  - currently placeholder file (no active model definitions yet).
- `master/schemas_master.py`
  - validation for admin creation and pagination.
  - serializers for master responses.
- `master/services_master.py`
  - master-level actions: create admin, list admins, health/control responses.
- `master/routes_master.py`
  - master HTTP routes with `role_required("master")` guards.
- `master/__init__.py`
  - package marker file.

## Data Model Summary
- `registration_users` (auth + role flags)
- `user_profiles` (1:1 with users)
- `buildings` (owned by admin)
- `towers` (belongs to building)
- `flats` (belongs to tower)
- `amenities` (belongs to building)
- `flat_amenities` (flat <-> amenity mapping)
- `bookings` (user booking against flat/tower/building with workflow status)

## Booking Lifecycle (Current Behavior)
1. User calls `POST /users/flats/{flat_id}/bookings`.
2. Booking is created with:
   - `status = PENDING`
   - `paid = true`
   - copied security deposit/address/user_name snapshot fields.
   - duplicate booking for same `user_id + flat_id` is blocked with `409 Conflict`.
3. Admin can read bookings and update status via `/admins/bookings/{booking_id}/status`.

## Important Notes
- Logout now revokes the current JWT access token by storing its `jti` in `revoked_tokens`.
- Some update/delete admin endpoints enforce strict ownership by `admin_id`.
- Cloudinary operations are optional but required for image upload routes.
- Global exception handlers convert unexpected failures into standard error responses.

## API Example JSON (All Endpoints)
Notes:
- Authenticated endpoints require `Authorization: Bearer <JWT>` header.
- For `multipart/form-data` endpoints, JSON shown below represents logical fields; file upload is sent as form-data.

### Global

#### `GET /`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Flask + Neon PostgreSQL connected",
  "data": null,
  "size": "120b"
}
```

#### `GET /health`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Service healthy",
  "data": {"service": "api"},
  "size": "132b"
}
```

### Users (`/users`)

#### `GET /users/health`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Users service healthy",
  "data": {"service": "users"},
  "size": "140b"
}
```

#### `POST /users/register`
Input JSON:
```json
{
  "email": "user1@example.com",
  "password": "User@123",
  "is_admin": false,
  "is_master": false
}
```
Response JSON:
```json
{
  "status_code": 201,
  "success": true,
  "message": "Account created for user1@example.com with role user.",
  "data": {
    "id": 12,
    "email": "user1@example.com",
    "role": "user",
    "token": "<jwt_token>"
  },
  "size": "250b"
}
```

#### `POST /users/login`
Input JSON:
```json
{
  "email": "user1@example.com",
  "password": "User@123"
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Login successful",
  "data": {
    "email": "user1@example.com",
    "role": "user",
    "token": "<jwt_token>"
  },
  "size": "210b"
}
```

#### `GET /users/me`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Profile fetched",
  "data": {
    "email": "user1@example.com",
    "role": "user",
    "created_at": "2026-02-10T12:00:00"
  },
  "size": "196b"
}
```

#### `PUT /users/me`
Input JSON:
```json
{
  "email": "user1.updated@example.com",
  "password": "NewPass@123"
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Account updated",
  "data": {
    "email": "user1.updated@example.com",
    "role": "user"
  },
  "size": "170b"
}
```

#### `DELETE /users/me`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Logged out and account deleted permanently.",
  "data": {
    "email": "user1.updated@example.com"
  },
  "size": "190b"
}
```

#### `POST /users/logout`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Logout successful",
  "data": null,
  "size": "120b"
}
```

#### `GET /users/profile`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "User profile fetched",
  "data": {
    "username": "jay14",
    "primary_email": "user1@example.com",
    "mobile_number": "9876543210",
    "profile_pic_url": "https://res.cloudinary.com/demo/image/upload/v1/kots/profile_pics/a1.jpg",
    "profile_pic_public_id": "kots/profile_pics/a1",
    "profile_pic_folder": "kots/profile_pics",
    "bio": "Looking for 2BHK.",
    "date_of_birth": "2000-01-01T00:00:00",
    "city": "Hyderabad",
    "state": "Telangana",
    "country": "India",
    "created_at": "2026-02-10T12:10:00",
    "updated_at": "2026-02-10T12:15:00"
  },
  "size": "640b"
}
```

#### `PUT /users/profile`
Input JSON:
```json
{
  "username": "jay14",
  "mobile_number": "9876543210",
  "bio": "Looking for 2BHK.",
  "city": "Hyderabad",
  "state": "Telangana",
  "country": "India"
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "User profile updated",
  "data": {
    "username": "jay14",
    "primary_email": "user1@example.com",
    "mobile_number": "9876543210",
    "profile_pic_url": null,
    "profile_pic_public_id": null,
    "profile_pic_folder": "kots/profile_pics",
    "bio": "Looking for 2BHK.",
    "date_of_birth": null,
    "city": "Hyderabad",
    "state": "Telangana",
    "country": "India",
    "created_at": "2026-02-10T12:10:00",
    "updated_at": "2026-02-10T12:25:00"
  },
  "size": "590b"
}
```

#### `POST /users/profile/picture`
Input JSON:
```json
{
  "file": "<binary_image>",
  "folder": "kots/profile_pics"
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Profile picture uploaded",
  "data": {
    "username": "jay14",
    "primary_email": "user1@example.com",
    "profile_pic_url": "https://res.cloudinary.com/demo/image/upload/v1/kots/profile_pics/new.jpg",
    "profile_pic_public_id": "kots/profile_pics/new",
    "profile_pic_folder": "kots/profile_pics"
  },
  "size": "330b"
}
```

#### `DELETE /users/profile/picture`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Profile picture removed",
  "data": {
    "username": "jay14",
    "primary_email": "user1@example.com",
    "profile_pic_url": null,
    "profile_pic_public_id": null,
    "profile_pic_folder": "kots/profile_pics"
  },
  "size": "280b"
}
```

#### `GET /users/buildings`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Buildings fetched",
  "data": [
    {
      "id": 1,
      "name": "Green Residency",
      "address": "Madhapur",
      "city": "Hyderabad",
      "state": "Telangana",
      "pincode": "500081",
      "full_address": "Madhapur, Hyderabad, Telangana, 500081",
      "total_towers": 3,
      "picture_url": "https://res.cloudinary.com/demo/image/upload/v1/kots/assets/b1.jpg",
      "towers_count": 2,
      "flats_count": 20,
      "available_flats_count": 7,
      "amenities": [{"id": 1, "name": "Gym", "description": "24x7", "picture_url": null}]
    }
  ],
  "size": "700b"
}
```

#### `GET /users/buildings/{building_id}`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Building fetched",
  "data": {
    "id": 1,
    "name": "Green Residency",
    "address": "Madhapur",
    "city": "Hyderabad",
    "state": "Telangana",
    "pincode": "500081",
    "full_address": "Madhapur, Hyderabad, Telangana, 500081",
    "picture_url": "https://res.cloudinary.com/demo/image/upload/v1/kots/assets/b1.jpg",
    "towers": [{"id": 10, "name": "A", "floors": 10, "total_flats": 50, "flats_count": 12, "available_flats_count": 4, "picture_url": null}],
    "amenities": [{"id": 1, "name": "Gym", "description": "24x7", "picture_url": null}]
  },
  "size": "760b"
}
```

#### `GET /users/buildings/{building_id}/amenities`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Building amenities fetched",
  "data": {
    "building": {"id": 1, "name": "Green Residency"},
    "amenities": [
      {"id": 1, "name": "Gym", "description": "24x7", "picture_url": null}
    ]
  },
  "size": "360b"
}
```

#### `GET /users/buildings/{building_id}/amenities/{amenity_id}`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Building amenity fetched",
  "data": {
    "building": {"id": 1, "name": "Green Residency"},
    "amenity": {"id": 1, "name": "Gym", "description": "24x7", "picture_url": null}
  },
  "size": "320b"
}
```

#### `GET /users/buildings/{building_id}/towers`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Towers fetched",
  "data": [
    {
      "id": 10,
      "name": "A",
      "floors": 10,
      "total_flats": 50,
      "picture_url": null,
      "flats_count": 12,
      "available_flats_count": 4
    }
  ],
  "size": "300b"
}
```

#### `GET /users/buildings/{building_id}/towers/{tower_id}`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Tower fetched",
  "data": {
    "tower": {
      "id": 10,
      "name": "A",
      "floors": 10,
      "total_flats": 50,
      "picture_url": null,
      "flats_count": 12,
      "available_flats_count": 4
    },
    "building": {
      "id": 1,
      "name": "Green Residency",
      "picture_url": null,
      "address": "Madhapur",
      "city": "Hyderabad",
      "state": "Telangana",
      "pincode": "500081",
      "full_address": "Madhapur, Hyderabad, Telangana, 500081"
    }
  },
  "size": "540b"
}
```

#### `GET /users/buildings/{building_id}/towers/{tower_id}/flats`
Input JSON:
```json
{
  "status": "available",
  "page": 1
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Flats fetched",
  "data": {
    "building": {"id": 1, "name": "Green Residency", "address": "Madhapur", "city": "Hyderabad", "state": "Telangana", "pincode": "500081", "full_address": "Madhapur, Hyderabad, Telangana, 500081"},
    "tower": {"id": 10, "name": "A"},
    "items": [
      {
        "id": 101,
        "tower_id": 10,
        "flat_number": "A-101",
        "floor_number": 1,
        "bhk_type": "2BHK",
        "area_sqft": 1200,
        "rent_amount": "25000.00",
        "security_deposit": "50000.00",
        "is_available": true,
        "picture_url": null
      }
    ],
    "page": 1,
    "per_page": 10,
    "total": 1,
    "total_pages": 1
  },
  "size": "720b"
}
```

#### `GET /users/flats/search`
Input JSON:
```json
{
  "address": "Madhapur",
  "city": "Hyderabad",
  "state": "Telangana",
  "flat_type": "2BHK",
  "min_rent": 15000,
  "max_rent": 30000,
  "available_only": true,
  "page": 1,
  "per_page": 10
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Flat search results fetched",
  "data": {
    "items": [
      {
        "flat": {
          "id": 101,
          "tower_id": 10,
          "flat_number": "A-101",
          "floor_number": 1,
          "bhk_type": "2BHK",
          "area_sqft": 1200,
          "rent_amount": "25000.00",
          "security_deposit": "50000.00",
          "is_available": true,
          "picture_url": null
        },
        "tower": {"id": 10, "name": "A"},
        "building": {
          "id": 1,
          "name": "Green Residency",
          "address": "Madhapur",
          "city": "Hyderabad",
          "state": "Telangana",
          "pincode": "500081",
          "full_address": "Madhapur, Hyderabad, Telangana, 500081"
        }
      }
    ],
    "page": 1,
    "per_page": 10,
    "total": 1,
    "total_pages": 1
  },
  "size": "980b"
}
```

#### `GET /users/buildings/search`
Input JSON:
```json
{
  "name": "Green",
  "address": "Madhapur",
  "city": "Hyderabad",
  "state": "Telangana",
  "page": 1,
  "per_page": 10
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Building search results fetched",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "Green Residency",
        "address": "Madhapur",
        "city": "Hyderabad",
        "state": "Telangana",
        "pincode": "500081",
        "full_address": "Madhapur, Hyderabad, Telangana, 500081",
        "total_towers": 3,
        "picture_url": null,
        "towers_count": 3,
        "flats_count": 12,
        "available_flats_count": 4,
        "amenities": [{"id": 1, "name": "Gym", "description": "24x7", "picture_url": null}]
      }
    ],
    "page": 1,
    "per_page": 10,
    "total": 1,
    "total_pages": 1
  },
  "size": "860b"
}
```

#### `GET /users/buildings/{building_id}/towers/{tower_id}/flats/{flat_id}`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Flat fetched",
  "data": {
    "flat": {
      "id": 101,
      "tower_id": 10,
      "flat_number": "A-101",
      "floor_number": 1,
      "bhk_type": "2BHK",
      "area_sqft": 1200,
      "rent_amount": "25000.00",
      "security_deposit": "50000.00",
      "is_available": true,
      "picture_url": null
    },
    "tower": {"id": 10, "name": "A"},
    "building": {"id": 1, "name": "Green Residency", "address": "Madhapur", "city": "Hyderabad", "state": "Telangana", "pincode": "500081", "full_address": "Madhapur, Hyderabad, Telangana, 500081"},
    "amenities": [{"id": 1, "name": "Gym", "description": "24x7", "picture_url": null}]
  },
  "size": "900b"
}
```

#### `POST /users/flats/{flat_id}/bookings`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 201,
  "success": true,
  "message": "Security deposit paid and booking created",
  "data": {
    "id": 501,
    "user_id": 12,
    "flat_id": 101,
    "tower_id": 10,
    "building_id": 1,
    "status": "PENDING",
    "security_deposit": "50000.00",
    "paid": true,
    "building_full_address": "Madhapur, Hyderabad, Telangana, 500081",
    "user_name": "jay14",
    "created_at": "2026-02-11T09:10:00"
  },
  "size": "420b"
}
```

Duplicate booking response JSON:
```json
{
  "status_code": 409,
  "success": false,
  "message": "Conflict",
  "user_message": "You have already booked this flat.",
  "size": "170b"
}
```

#### `GET /users/bookings`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Bookings fetched",
  "data": [
    {
      "id": 501,
      "user_id": 12,
      "flat_id": 101,
      "tower_id": 10,
      "building_id": 1,
      "status": "PENDING",
      "security_deposit": "50000.00",
      "paid": true,
      "building_full_address": "Madhapur, Hyderabad, Telangana, 500081",
      "user_name": "jay14",
      "created_at": "2026-02-11T09:10:00",
      "building": {"id": 1, "name": "Green Residency"},
      "tower": {"id": 10, "name": "A"},
      "flat": {"id": 101, "flat_number": "A-101"},
      "manager": {"name": "admin1", "phone": "9876543210"}
    }
  ],
  "size": "690b"
}
```

#### `GET /users/bookings/{booking_id}`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Booking fetched",
  "data": {
    "id": 501,
    "user_id": 12,
    "flat_id": 101,
    "tower_id": 10,
    "building_id": 1,
    "status": "PENDING",
    "security_deposit": "50000.00",
    "paid": true,
    "building_full_address": "Madhapur, Hyderabad, Telangana, 500081",
    "user_name": "jay14",
    "created_at": "2026-02-11T09:10:00",
    "building": {"id": 1, "name": "Green Residency"},
    "tower": {"id": 10, "name": "A"},
    "flat": {"id": 101, "flat_number": "A-101"},
    "manager": {"name": "admin1", "phone": "9876543210"}
  },
  "size": "680b"
}
```

### Admins (`/admins`)

#### `GET /admins/health`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Admins service healthy",
  "data": {"service": "admins"},
  "size": "142b"
}
```

#### `GET /admins/dashboard`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Admins dashboard",
  "data": {"scope": "admin"},
  "size": "136b"
}
```

#### `POST /admins/buildings`
Input JSON:
```json
{
  "name": "Green Residency",
  "address": "Madhapur",
  "city": "Hyderabad",
  "state": "Telangana",
  "pincode": "500081",
  "total_towers": 3,
  "file": "<binary_image>",
  "folder": "kots/assets"
}
```
Response JSON:
```json
{
  "status_code": 201,
  "success": true,
  "message": "Building created",
  "data": {
    "id": 1,
    "admin_id": 2,
    "name": "Green Residency",
    "address": "Madhapur",
    "city": "Hyderabad",
    "state": "Telangana",
    "pincode": "500081",
    "total_towers": 3,
    "picture_url": "https://res.cloudinary.com/demo/image/upload/v1/kots/assets/b1.jpg",
    "picture_public_id": "kots/assets/b1",
    "picture_folder": "kots/assets",
    "created_at": "2026-02-11T08:00:00"
  },
  "size": "510b"
}
```

#### `PUT /admins/buildings/{building_id}`
Input JSON:
```json
{
  "name": "Green Residency Phase 2",
  "total_towers": 4,
  "file": "<binary_image>",
  "folder": "kots/assets"
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Building updated",
  "data": {
    "id": 1,
    "admin_id": 2,
    "name": "Green Residency Phase 2",
    "address": "Madhapur",
    "city": "Hyderabad",
    "state": "Telangana",
    "pincode": "500081",
    "total_towers": 4,
    "picture_url": "https://res.cloudinary.com/demo/image/upload/v1/kots/assets/b2.jpg",
    "picture_public_id": "kots/assets/b2",
    "picture_folder": "kots/assets",
    "created_at": "2026-02-11T08:00:00"
  },
  "size": "520b"
}
```

#### `PUT /admins/buildings`
Input JSON:
```json
{
  "id": 1,
  "city": "Secunderabad"
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Building updated",
  "data": {
    "id": 1,
    "admin_id": 2,
    "name": "Green Residency",
    "address": "Madhapur",
    "city": "Secunderabad",
    "state": "Telangana",
    "pincode": "500081",
    "total_towers": 3,
    "picture_url": null,
    "picture_public_id": null,
    "picture_folder": "kots/assets",
    "created_at": "2026-02-11T08:00:00"
  },
  "size": "450b"
}
```

#### `DELETE /admins/buildings/{building_id}`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Building deleted",
  "data": {
    "id": 1,
    "name": "Green Residency"
  },
  "size": "150b"
}
```

#### `GET /admins/buildings/my`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Admin buildings fetched",
  "data": [
    {
      "id": 1,
      "admin_id": 2,
      "name": "Green Residency",
      "address": "Madhapur",
      "city": "Hyderabad",
      "state": "Telangana",
      "pincode": "500081",
      "total_towers": 3,
      "picture_url": null,
      "picture_public_id": null,
      "picture_folder": "kots/assets",
      "created_at": "2026-02-11T08:00:00"
    }
  ],
  "size": "470b"
}
```

#### `GET /admins/buildings/{building_id}`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Building fetched",
  "data": {
    "id": 1,
    "admin_id": 2,
    "name": "Green Residency",
    "address": "Madhapur",
    "city": "Hyderabad",
    "state": "Telangana",
    "pincode": "500081",
    "total_towers": 3,
    "picture_url": null,
    "picture_public_id": null,
    "picture_folder": "kots/assets",
    "created_at": "2026-02-11T08:00:00"
  },
  "size": "450b"
}
```

#### `POST /admins/buildings/{building_id}/towers`
Input JSON:
```json
{
  "name": "A",
  "floors": 10,
  "total_flats": 50,
  "file": "<binary_image>",
  "folder": "kots/assets"
}
```
Response JSON:
```json
{
  "status_code": 201,
  "success": true,
  "message": "Tower created",
  "data": {
    "id": 10,
    "building_id": 1,
    "name": "A",
    "floors": 10,
    "total_flats": 50,
    "picture_url": "https://res.cloudinary.com/demo/image/upload/v1/kots/assets/t1.jpg",
    "picture_public_id": "kots/assets/t1",
    "picture_folder": "kots/assets",
    "created_at": "2026-02-11T08:20:00"
  },
  "size": "420b"
}
```

#### `PUT /admins/towers/{tower_id}`
Input JSON:
```json
{
  "name": "A1",
  "floors": 12,
  "total_flats": 60
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Tower updated",
  "data": {
    "id": 10,
    "building_id": 1,
    "name": "A1",
    "floors": 12,
    "total_flats": 60,
    "picture_url": null,
    "picture_public_id": null,
    "picture_folder": "kots/assets",
    "created_at": "2026-02-11T08:20:00"
  },
  "size": "380b"
}
```

#### `GET /admins/buildings/{building_id}/towers`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Towers fetched",
  "data": [
    {
      "id": 10,
      "building_id": 1,
      "building_name": "Green Residency",
      "name": "A",
      "floors": 10,
      "total_flats": 50,
      "picture_url": null,
      "picture_public_id": null,
      "picture_folder": "kots/assets",
      "created_at": "2026-02-11T08:20:00"
    }
  ],
  "size": "430b"
}
```

#### `GET /admins/buildings/{building_id}/towers/{tower_id}`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Tower fetched",
  "data": {
    "id": 10,
    "building_id": 1,
    "building_name": "Green Residency",
    "name": "A",
    "floors": 10,
    "total_flats": 50,
    "picture_url": null,
    "picture_public_id": null,
    "picture_folder": "kots/assets",
    "created_at": "2026-02-11T08:20:00"
  },
  "size": "420b"
}
```

#### `DELETE /admins/towers/{tower_id}`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Tower deleted",
  "data": {
    "id": 10
  },
  "size": "120b"
}
```

#### `POST /admins/towers/{tower_id}/flats`
Input JSON:
```json
{
  "flat_number": "A-101",
  "floor_number": 1,
  "bhk_type": "2BHK",
  "area_sqft": 1200,
  "rent_amount": 25000,
  "security_deposit": 50000,
  "is_available": true,
  "file": "<binary_image>",
  "folder": "kots/assets"
}
```
Response JSON:
```json
{
  "status_code": 201,
  "success": true,
  "message": "Flat created",
  "data": {
    "id": 101,
    "tower_id": 10,
    "flat_number": "A-101",
    "floor_number": 1,
    "bhk_type": "2BHK",
    "area_sqft": 1200,
    "rent_amount": "25000.00",
    "security_deposit": "50000.00",
    "is_available": true,
    "picture_url": "https://res.cloudinary.com/demo/image/upload/v1/kots/assets/f1.jpg",
    "picture_public_id": "kots/assets/f1",
    "picture_folder": "kots/assets",
    "created_at": "2026-02-11T08:30:00"
  },
  "size": "520b"
}
```

#### `PUT /admins/flats/{flat_id}`
Input JSON:
```json
{
  "rent_amount": 27000,
  "security_deposit": 54000,
  "is_available": false
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Flat updated",
  "data": {
    "id": 101,
    "tower_id": 10,
    "flat_number": "A-101",
    "floor_number": 1,
    "bhk_type": "2BHK",
    "area_sqft": 1200,
    "rent_amount": "27000.00",
    "security_deposit": "54000.00",
    "is_available": false,
    "picture_url": null,
    "picture_public_id": null,
    "picture_folder": "kots/assets",
    "created_at": "2026-02-11T08:30:00"
  },
  "size": "470b"
}
```

#### `PUT /admins/towers/{tower_id}/flats/{flat_id}`
Input JSON:
```json
{
  "rent_amount": 27000,
  "security_deposit": 54000,
  "is_available": false
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Flat updated",
  "data": {
    "id": 101,
    "tower_id": 10,
    "flat_number": "A-101",
    "floor_number": 1,
    "bhk_type": "2BHK",
    "area_sqft": 1200,
    "rent_amount": "27000.00",
    "security_deposit": "54000.00",
    "is_available": false,
    "picture_url": null,
    "picture_public_id": null,
    "picture_folder": "kots/assets",
    "created_at": "2026-02-11T08:30:00"
  },
  "size": "470b"
}
```

#### `GET /admins/towers/{tower_id}/flats`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Flats fetched",
  "data": [
    {
      "id": 101,
      "tower_id": 10,
      "flat_number": "A-101",
      "floor_number": 1,
      "bhk_type": "2BHK",
      "area_sqft": 1200,
      "rent_amount": "25000.00",
      "security_deposit": "50000.00",
      "is_available": true,
      "picture_url": null,
      "picture_public_id": null,
      "picture_folder": "kots/assets",
      "created_at": "2026-02-11T08:30:00"
    }
  ],
  "size": "500b"
}
```

#### `GET /admins/towers/{tower_id}/flats/{flat_id}`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Flat fetched",
  "data": {
    "id": 101,
    "tower_id": 10,
    "flat_number": "A-101",
    "floor_number": 1,
    "bhk_type": "2BHK",
    "area_sqft": 1200,
    "rent_amount": "25000.00",
    "security_deposit": "50000.00",
    "is_available": true,
    "picture_url": null,
    "picture_public_id": null,
    "picture_folder": "kots/assets",
    "created_at": "2026-02-11T08:30:00"
  },
  "size": "480b"
}
```

#### `DELETE /admins/flats/{flat_id}`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Flat deleted",
  "data": {
    "id": 101
  },
  "size": "118b"
}
```

#### `POST /admins/buildings/{building_id}/amenities`
Input JSON:
```json
{
  "name": "Gym",
  "description": "24x7",
  "file": "<binary_image>",
  "folder": "kots/assets"
}
```
Response JSON:
```json
{
  "status_code": 201,
  "success": true,
  "message": "Amenity created",
  "data": {
    "id": 1,
    "building_id": 1,
    "name": "Gym",
    "description": "24x7",
    "picture_url": "https://res.cloudinary.com/demo/image/upload/v1/kots/assets/am1.jpg",
    "picture_public_id": "kots/assets/am1",
    "picture_folder": "kots/assets",
    "created_at": "2026-02-11T08:40:00"
  },
  "size": "390b"
}
```

#### `GET /admins/buildings/{building_id}/amenities`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Amenities fetched",
  "data": [
    {
      "id": 1,
      "building_id": 1,
      "name": "Gym",
      "description": "24x7",
      "picture_url": null,
      "picture_public_id": null,
      "picture_folder": "kots/assets",
      "created_at": "2026-02-11T08:40:00"
    }
  ],
  "size": "350b"
}
```

#### `PUT /admins/flats/{flat_id}/amenities`
Input JSON:
```json
{
  "amenity_ids": [1, 2, 3]
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Flat amenities updated",
  "data": {
    "flat_id": 101,
    "amenity_ids": [1, 2, 3]
  },
  "size": "165b"
}
```

#### `PUT /admins/amenities/{amenity_id}`
Input JSON:
```json
{
  "name": "Gym Plus",
  "description": "24x7 with trainer",
  "file": "<binary_image>",
  "folder": "kots/assets"
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Amenity updated",
  "data": {
    "id": 1,
    "building_id": 1,
    "name": "Gym Plus",
    "description": "24x7 with trainer",
    "picture_url": "https://res.cloudinary.com/demo/image/upload/v1/kots/assets/am2.jpg",
    "picture_public_id": "kots/assets/am2",
    "picture_folder": "kots/assets",
    "created_at": "2026-02-11T08:40:00"
  },
  "size": "430b"
}
```

#### `DELETE /admins/amenities/{amenity_id}`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Amenity deleted",
  "data": {
    "id": 1,
    "name": "Gym"
  },
  "size": "145b"
}
```

#### `GET /admins/bookings`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Bookings fetched",
  "data": [
    {
      "id": 501,
      "user_id": 12,
      "flat_id": 101,
      "tower_id": 10,
      "building_id": 1,
      "status": "PENDING",
      "security_deposit": "50000.00",
      "paid": true,
      "building": {"id": 1, "name": "Green Residency"},
      "tower": {"id": 10, "name": "A"},
      "flat": {"id": 101, "flat_number": "A-101"},
      "created_at": "2026-02-11T09:10:00"
    }
  ],
  "size": "560b"
}
```

#### `GET /admins/bookings/{booking_id}`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Booking fetched",
  "data": {
    "id": 501,
    "user_id": 12,
    "flat_id": 101,
    "tower_id": 10,
    "building_id": 1,
    "status": "PENDING",
    "security_deposit": "50000.00",
    "paid": true,
    "building": {"id": 1, "name": "Green Residency"},
    "tower": {"id": 10, "name": "A"},
    "flat": {"id": 101, "flat_number": "A-101"},
    "created_at": "2026-02-11T09:10:00"
  },
  "size": "540b"
}
```

#### `PUT /admins/bookings/{booking_id}/status`
Input JSON:
```json
{
  "status": "APPROVED"
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Booking status updated",
  "data": {
    "id": 501,
    "status": "APPROVED"
  },
  "size": "145b"
}
```

### Master (`/master`)

#### `GET /master/health`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Master service healthy",
  "data": {"service": "master"},
  "size": "142b"
}
```

#### `GET /master/control`
Input JSON:
```json
{}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Master control panel",
  "data": {"scope": "master"},
  "size": "140b"
}
```

#### `POST /master/create-admin`
Input JSON:
```json
{
  "email": "newadmin@example.com",
  "password": "Admin@123"
}
```
Response JSON:
```json
{
  "status_code": 201,
  "success": true,
  "message": "Admin account created for newadmin@example.com.",
  "data": {
    "id": 22,
    "email": "newadmin@example.com",
    "role": "admin"
  },
  "size": "210b"
}
```

#### `GET /master/admins`
Input JSON:
```json
{
  "page": 1,
  "per_page": 10
}
```
Response JSON:
```json
{
  "status_code": 200,
  "success": true,
  "message": "Admins fetched",
  "data": {
    "items": [
      {
        "id": 2,
        "email": "admin1@example.com",
        "role": "admin",
        "created_at": "2026-02-10T10:00:00"
      }
    ],
    "page": 1,
    "per_page": 10,
    "total": 1,
    "pages": 1,
    "has_next": false,
    "has_prev": false
  },
  "size": "360b"
}
```

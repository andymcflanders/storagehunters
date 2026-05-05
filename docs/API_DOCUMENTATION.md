# StorageHub API Documentation

This document provides comprehensive documentation for the StorageHub API, with a focus on Home Assistant integration.

## Table of Contents

1. [Overview](#overview)
2. [First-Run Setup](#first-run-setup)
3. [Authentication](#authentication)
4. [Home Assistant Integration API](#home-assistant-integration-api)
5. [Webhooks](#webhooks)
6. [Core API Reference](#core-api-reference)
7. [Error Handling](#error-handling)
8. [Rate Limiting](#rate-limiting)
9. [Examples](#examples)

---

## Overview

StorageHub provides a RESTful API for managing your personal inventory. The API is designed to be easy to integrate with Home Assistant and other automation platforms.

### Base URL

```
http://your-storagehub-instance/api
```

### API Versions

- **v1.0**: Current stable version
- OpenAPI/Swagger documentation available at `/api/docs`
- ReDoc documentation available at `/api/redoc`

### Content Type

All requests and responses use JSON:
```
Content-Type: application/json
```

---

## First-Run Setup

A clean install (empty users table) exposes two public endpoints used by
the in-app `/setup` wizard. Both bypass authentication because there's
no user to authenticate as yet.

### Probe Setup Status

```http
GET /api/setup/status
```

Response:

```json
{
  "needs_setup": true
}
```

The frontend layout calls this on first load and redirects to `/setup`
when `needs_setup` is true.

### Complete Setup

One-shot bootstrap. Creates the first admin, optionally persists an
OpenAI API key, optionally configures supported AI languages, optionally
creates a first location, and returns a session cookie so the new admin
lands logged in.

```http
POST /api/setup/complete
Content-Type: application/json

{
  "admin_name": "Admin",
  "admin_email": "admin@example.com",
  "admin_password": "strong-password",
  "admin_language": "en",
  "openai_api_key": "sk-...",
  "supported_languages": ["en", "no"],
  "default_language": "en",
  "first_location": {
    "name": "Home",
    "description": "Main residence",
    "address": null
  }
}
```

`admin_email` and `admin_password` are required — admins sign in via
email + password rather than the household card grid. Everything else
is optional.

The endpoint returns **409 Conflict** if any user already exists, so
the public route can't be re-used to inject a second admin after
onboarding completes.

---

## Authentication

StorageHub supports two authentication methods:

### 1. Session-Based Authentication (Web UI)

Used by the web interface. Requires logging in and uses HTTP-only cookies.

The login endpoint accepts **either** `user_id` (household members tap
their card on the login screen) **or** `email` (admin sign-in via the
"Administer this instance" link, since admins are hidden from the card
grid). Email lookup is case-insensitive. A wrong identifier and a wrong
password both return the same 401 — no account-enumeration leak.

```http
POST /api/auth/login
Content-Type: application/json

# Card-tap path (household users)
{
  "user_id": "uuid-of-user",
  "password": "optional-password"
}

# Admin path (email sign-in)
{
  "email": "admin@example.com",
  "password": "your-password"
}
```

The login screen calls
`GET /api/users?include_admins=false&include_profiles=false` to populate
the household card grid: admins sign in via the email/password modal
instead, and *profile users* (household members like small kids who
own items but never log in) shouldn't appear on the picker either.
Owner pickers in the rest of the app keep both filters at their
default `true` so profiles can still be assigned items.

User responses include `is_profile: bool`, `birthdate: date | null`,
and `gender: 'male' | 'female' | 'other' | null` — all introduced
to support the AI owner-suggestion and `/outgrown` workflows.

### 2. API Key Authentication (Recommended for Home Assistant)

API keys are the recommended method for Home Assistant and other external integrations.

#### Creating an API Key

1. Log into the StorageHub web UI
2. Navigate to Settings > API Keys
3. Click "Create API Key"
4. Select the required scopes
5. Copy the key immediately (it's only shown once!)

Or via API:
```http
POST /api/api-keys
Content-Type: application/json
Cookie: session_token=your-session

{
  "name": "Home Assistant",
  "description": "API key for Home Assistant integration",
  "scopes": ["read", "search"],
  "expires_at": null
}
```

Response:
```json
{
  "id": "uuid",
  "name": "Home Assistant",
  "key": "shub_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "key_prefix": "shub_xxxxxxx",
  "scopes": ["read", "search"],
  "is_active": true,
  "created_at": "2025-12-09T10:00:00Z"
}
```

#### Using API Keys

Include the key in your requests using either header:

**Option 1: X-API-Key header (Recommended)**
```http
GET /api/ha/stats
X-API-Key: shub_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Option 2: Authorization Bearer header**
```http
GET /api/ha/stats
Authorization: Bearer shub_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### API Key Scopes

| Scope | Description |
|-------|-------------|
| `read` | Read-only access to inventory data |
| `write` | Create, update, and delete items/containers |
| `search` | Use the search functionality |
| `webhooks` | Manage webhooks |
| `admin` | Full administrative access |

---

## Home Assistant Integration API

The Home Assistant API is available at `/api/ha/*` and is optimized for sensor data and automations.

### Status Endpoint

Check system status (no authentication required):

```http
GET /api/ha/status
```

Response:
```json
{
  "status": "online",
  "version": "1.0.0",
  "api_version": "v1",
  "name": "StorageHub",
  "instance_id": "f3e2d1c0-1234-5678-9abc-def012345678"
}
```

`instance_id` is a stable UUID per database. The HA integration uses
it as the config-entry `unique_id` so reconfiguring the host URL
doesn't fork a new entry.

### Inventory Statistics

Get comprehensive inventory statistics for Home Assistant sensors:

```http
GET /api/ha/stats
X-API-Key: your-api-key
```

Response:
```json
{
  "total_locations": 5,
  "total_containers": 42,
  "total_items": 1523,
  "total_photos": 3847,
  "total_tags": 156,
  "items_needing_review": 12,
  "items_by_condition": {
    "good": 1200,
    "fair": 250,
    "damaged": 50,
    "needs_repair": 23
  },
  "items_by_season": {
    "none": 1000,
    "winter": 200,
    "summer": 150,
    "spring": 100,
    "fall": 50,
    "holiday": 23
  },
  "last_updated": "2025-12-09T10:30:00Z"
}
```

### Reminder Summary

Get reminder counts for sensors:

```http
GET /api/ha/reminders
X-API-Key: your-api-key
```

Response:
```json
{
  "total_reminders": 15,
  "pending_reminders": 10,
  "overdue_reminders": 3,
  "due_today": 2,
  "due_this_week": 5,
  "reminders_by_type": {
    "check_item": 5,
    "expiration": 3,
    "maintenance": 4,
    "restock": 2,
    "custom": 1
  }
}
```

### List Reminders

Get detailed reminder list for notifications:

```http
GET /api/ha/reminders/list?limit=20&include_completed=false
X-API-Key: your-api-key
```

Response:
```json
[
  {
    "id": "uuid",
    "title": "Check winter clothes condition",
    "reminder_type": "check_item",
    "due_date": "2025-12-15T00:00:00Z",
    "is_overdue": false,
    "item_name": "Winter Jacket",
    "container_name": "Winter Storage Box"
  }
]
```

### Locations

```http
GET /api/ha/locations
X-API-Key: your-api-key
```

Response:
```json
[
  {
    "id": "uuid",
    "name": "Garage",
    "description": "Main garage storage",
    "container_count": 15,
    "item_count": 234
  }
]
```

### Containers

```http
GET /api/ha/containers?location_id=uuid&limit=50
X-API-Key: your-api-key
```

Response:
```json
[
  {
    "id": "uuid",
    "name": "Holiday Decorations",
    "qr_code": "aOXfG4Td_nQ",
    "location_name": "Garage",
    "item_count": 45,
    "child_container_count": 3
  }
]
```

### Get Container by QR Code

Useful for NFC/QR scanning automations:

```http
GET /api/ha/containers/qr/aOXfG4Td_nQ
X-API-Key: your-api-key
```

### Items

```http
GET /api/ha/items?container_id=uuid&condition=good&limit=50
X-API-Key: your-api-key
```

Query parameters:
- `container_id`: Filter by container
- `condition`: Filter by condition (good, fair, damaged, needs_repair)
- `seasonal`: Filter by season (none, spring, summer, fall, winter, holiday)
- `needs_review`: Filter items needing AI review
- `limit`: Maximum results (default: 50, max: 200)
- `offset`: Pagination offset

Response:
```json
[
  {
    "id": "uuid",
    "name": "Red Winter Jacket",
    "description": "Size M, waterproof",
    "container_name": "Winter Clothes",
    "location_name": "Bedroom Closet",
    "condition": "good",
    "seasonal": "winter",
    "value_estimate": 150.00,
    "owner_name": "John",
    "primary_image_url": "/uploads/images/abc123.jpg",
    "tags": ["clothing", "winter", "jacket"]
  }
]
```

### Items Index (lite, ETag-cached)

Pre-loaded by the HA Lovelace card so it can substring-filter as
the user types without per-keystroke round-trips. Heavy fields
(images, tags, descriptions, full container objects) are
deliberately omitted.

```http
GET /api/ha/items/index
X-API-Key: your-api-key
If-None-Match: "abc123"   (optional)
```

Response (200 OK):
```http
ETag: "abc123"
Cache-Control: private, max-age=900
Content-Type: application/json
Content-Encoding: gzip
```
```json
[
  {
    "id": "uuid",
    "name": "Red wool cardigan",
    "owner_name": "Sverre",
    "container_name": "Winter Box",
    "location_name": "Attic",
    "ai_names": ["Rød ullgenser"]
  }
]
```

When `If-None-Match` matches the current ETag, the server returns
**304 Not Modified** with no body. The ETag is derived from the
`MAX(updated_at)` across `items`, `containers`, `locations`, and
`users`, hashed for compactness.

### Search

Search for items (requires `search` scope). Matches across the
manual `name` / `description`, the AI-generated translations
(`ai_names` / `ai_descriptions`), and the **owner's name** —
multi-token queries require every token to match some field, so
`?q=Sverre+jakke` returns only Sverre's jackets, not every jacket.
English apostrophe-s possessive (`Sverre's` → `Sverre`) is stripped
during tokenization.

```http
GET /api/ha/search?q=Sverre%20jakke&limit=20
X-API-Key: your-api-key
```

Response:
```json
{
  "items": [...],
  "total_count": 3,
  "query": "Sverre jakke"
}
```

### Semantic Search

Same response shape as `/api/ha/search`, but with two extra layers
designed for voice queries and "Smart matches" surfaces:

1. **Owner pre-filter.** Tokens whose stem matches a `User.name`
   are pulled out of the search and used as a hard owner filter.
   Handles English `'s` and Norwegian `s` suffixes (`Sverres
   genser` is restricted to Sverre's items).
2. **Synonym expansion.** Remaining tokens go through the same
   color/clothing dictionaries the web UI uses. `genser` →
   `sweater` → `[cardigan, pullover, jumper, …]`, so a query for
   *genser* matches an item literally named *Cardigan*.

This is **not** vector-embedding similarity — it's expanded
substring matching. If the synonym dictionaries don't cover a
domain, extend them in `services/semantic_search.py`.

```http
GET /api/ha/search/semantic?q=Sverres%20genser&limit=20
X-API-Key: your-api-key
```

Response (same shape as `/api/ha/search`):
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Hvit Oasis Cardigan",
      "owner_name": "Sverre",
      "container_name": "Winter Box",
      ...
    }
  ],
  "total_count": 1,
  "query": "Sverres genser"
}
```

### Tags

```http
GET /api/ha/tags
X-API-Key: your-api-key
```

Response:
```json
[
  {
    "id": "uuid",
    "name": "electronics",
    "is_ai_generated": false,
    "item_count": 45
  }
]
```

---

## Webhooks

Webhooks allow you to receive real-time notifications when events occur in StorageHub.

### Available Events

| Event | Description |
|-------|-------------|
| `item.created` | New item added |
| `item.updated` | Item modified |
| `item.deleted` | Item removed |
| `item.moved` | Item moved to different container |
| `container.created` | New container added |
| `container.updated` | Container modified |
| `container.deleted` | Container removed |
| `location.created` | New location added |
| `location.updated` | Location modified |
| `location.deleted` | Location removed |
| `reminder.due` | Reminder becomes due |
| `reminder.overdue` | Reminder is overdue |
| `reminder.completed` | Reminder marked complete |
| `stats.updated` | Inventory statistics changed |

### Creating a Webhook

```http
POST /api/webhooks
Content-Type: application/json
Cookie: session_token=your-session

{
  "name": "Home Assistant Events",
  "url": "http://homeassistant.local:8123/api/webhook/storagehub",
  "secret": "your-webhook-secret",
  "events": ["item.created", "item.updated", "reminder.due"],
  "retry_count": 3,
  "timeout_seconds": 30
}
```

### Webhook Payload

When an event occurs, StorageHub sends a POST request to your webhook URL:

```json
{
  "event": "item.created",
  "timestamp": "2025-12-09T10:30:00Z",
  "data": {
    "item_id": "uuid",
    "name": "New Item",
    "container_id": "uuid",
    "container_name": "Storage Box"
  }
}
```

### Webhook Signature

If you configure a secret, StorageHub signs the payload with HMAC-SHA256:

```
X-StorageHub-Signature: sha256=abc123...
X-StorageHub-Event: item.created
```

Verify the signature:
```python
import hmac
import hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### Testing Webhooks

```http
POST /api/webhooks/{webhook_id}/test
Content-Type: application/json
Cookie: session_token=your-session

{
  "event": "stats.updated"
}
```

### Webhook Delivery History

```http
GET /api/webhooks/{webhook_id}/deliveries?limit=20
Cookie: session_token=your-session
```

---

## Core API Reference

### Locations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/locations` | List all locations |
| POST | `/api/locations` | Create location |
| GET | `/api/locations/{id}` | Get location with top-level containers |
| PATCH | `/api/locations/{id}` | Update location |
| DELETE | `/api/locations/{id}` | Delete location |
| GET | `/api/locations/stats` | Dashboard counts (locations, containers, items, photos) |

### Containers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/containers` | List containers |
| POST | `/api/containers` | Create container (`container_type` optional) |
| GET | `/api/containers/{id}` | Get container with items, child containers, breadcrumb path |
| PATCH | `/api/containers/{id}` | Update container (name, type, notes, parent) |
| DELETE | `/api/containers/{id}` | Delete container (`?mode=fail|recursive|transfer`) |
| GET | `/api/containers/{id}/qr` | Get QR code image (PNG) |
| GET | `/api/containers/qr/{qr_code}` | Look up by QR token |
| POST | `/api/containers/{id}/image` | Upload (or replace) the hero image (multipart `file`) |
| DELETE | `/api/containers/{id}/image` | Remove the hero image |

The container response carries `container_type` (`box`, `drawer`,
`shelf`, `cabinet`, `closet`, `bin`, `basket`, `other`, or `null`) and
`image_url` (computed from the stored relative path).

### Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/items` | List items |
| POST | `/api/items` | Create item |
| GET | `/api/items/{id}` | Get item with images, tags, related items, path, owner + suggested_owner |
| PATCH | `/api/items/{id}` | Update item (also accepts `clear_suggestion` and `dismiss_outgrown` flags) |
| DELETE | `/api/items/{id}` | Delete item |
| POST | `/api/items/{id}/images` | Upload image |
| DELETE | `/api/items/{id}/images/{image_id}` | Remove image |
| POST | `/api/items/{id}/images/{image_id}/set-primary` | Set hero image |
| POST | `/api/items/{id}/images/{image_id}/reprocess` | Re-run AI on a single image |
| POST | `/api/items/{id}/process-all-images` | Re-run AI across every image |
| POST | `/api/items/{id}/move` | Move to a different container |
| POST | `/api/items/{id}/tags` | Attach a tag |
| DELETE | `/api/items/{id}/tags/{tag_id}` | Detach a tag |

Item responses carry `ai_names` and `ai_descriptions` as JSONB dicts
keyed by ISO language code (e.g. `{"en": "Red Sweater", "no": "Rød Genser"}`).
The set of keys depends on `AISettings.supported_languages` at the time
of generation; clients should fall back through the user's locale →
default language → first available value.

Items also surface AI-derived auxiliary fields:

| Field | Type | Populated by |
|-------|------|--------------|
| `suggested_owner_id` | UUID \| null | Vision classifier (matching size + motif against household demographics) |
| `owner_suggestion_reason` | string \| null | Vision classifier — one-sentence rationale shown on the item page |
| `size_age_min_months` | int \| null | Vision classifier (only set for kid-sized items); drives `/outgrown` |
| `size_age_max_months` | int \| null | Vision classifier; `/outgrown` shows items where the owner has aged past this |
| `outgrown_dismissed_at` | datetime \| null | User dismissing an item from `/outgrown` |
| `triage_decision` | `'love'\|'undecided'\|'hate'\|null` | User decision on `/declutter` |
| `triage_decided_at` | datetime \| null | When the decision was made |
| `triage_show_after` | datetime \| null | Cooldown — item is hidden from `/declutter` until this passes (love=12mo, undecided=3mo) |

`PATCH /api/items/{id}` accepts two write-only flags alongside the
real columns:

- `clear_suggestion: bool` — set to `true` when the user accepts or
  dismisses the AI owner suggestion. Clears `suggested_owner_id` and
  `owner_suggestion_reason`. The "Assign to X" path sends both
  `owner_id` and `clear_suggestion: true` in one PATCH.
- `dismiss_outgrown: bool` — `true` stamps `outgrown_dismissed_at = now()`,
  hiding the item from `/outgrown` even though its size + age data is
  unchanged. `false` clears the stamp.

### Outgrown

Surfaces items the household has aged out of. The endpoint joins
`items.size_age_max_months` with the effective owner's current age in
months (real `owner_id` if set, otherwise the AI's `suggested_owner_id`)
and returns rows where the owner is past the upper bound.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/outgrown` | List outgrown items, sorted most-outgrown first, with optional inherit candidates |

Each row also carries an `inherit_to` candidate when another non-admin
household member fits the size today or will fit within 12 months —
picked by the smallest `months_until_fit`, ties broken by youngest age.

### Triage / Declutter

The "Tinder for items" workflow. Decisions are shared per-household
(one row per item, no per-user fork). Cooldowns are hard-coded:
love = 12 months, undecided = 3 months, hate = no cooldown
(item moves to the discard pile and stays out of the next-card pool).

Adult items only: anything with `size_age_max_months` set is excluded
from the eligible pool because it's already covered by `/outgrown`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/triage/next` | Random eligible item, with optional `?owner_id=` and `?tag=` filters |
| POST | `/api/triage/{id}/decide` | Body `{decision: "love"\|"undecided"\|"hate"}` — applies the cooldown |
| POST | `/api/triage/{id}/undo` | Clear the decision (e.g. user re-thinks a Hate) |
| POST | `/api/triage/{id}/mark-donated` | Soft-delete with a "donated" entry in the activity log |
| GET | `/api/triage/filters` | Owner + top-30 tag dropdown options, with eligible-item counts |
| GET | `/api/triage/discard` | All hated items, grouped by container path for efficient sweeps |

`/api/triage/next` returns `{item, remaining_estimate}` where `item`
is `null` when the pool is empty (no items eligible after filters and
cooldowns). The `remaining_estimate` is a quick `COUNT(*)` over the
same filtered pool so the UI can show "12 items remaining".

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/search` | Full search |
| GET | `/api/search/autocomplete` | Fast autocomplete |

### Tags

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tags` | List all tags |
| POST | `/api/tags` | Create tag |
| PATCH | `/api/tags/{id}` | Update tag |
| DELETE | `/api/tags/{id}` | Delete tag |
| POST | `/api/tags/merge` | Merge tags |

### Reminders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reminders` | List reminders |
| POST | `/api/reminders` | Create reminder |
| PATCH | `/api/reminders/{id}` | Update reminder |
| POST | `/api/reminders/{id}/complete` | Mark complete |
| DELETE | `/api/reminders/{id}` | Delete reminder |

### API Keys

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/api-keys` | List API keys |
| POST | `/api/api-keys` | Create API key |
| GET | `/api/api-keys/{id}` | Get API key |
| PATCH | `/api/api-keys/{id}` | Update API key |
| DELETE | `/api/api-keys/{id}` | Delete API key |

### Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/webhooks` | List webhooks |
| POST | `/api/webhooks` | Create webhook |
| GET | `/api/webhooks/events` | List available events |
| GET | `/api/webhooks/{id}` | Get webhook |
| PATCH | `/api/webhooks/{id}` | Update webhook |
| DELETE | `/api/webhooks/{id}` | Delete webhook |
| POST | `/api/webhooks/{id}/test` | Test webhook |
| GET | `/api/webhooks/{id}/deliveries` | Delivery history |

### Admin

All admin endpoints require an authenticated session belonging to a
user with `role=admin`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/stats` | System-wide statistics |
| GET | `/api/admin/users` | List users (with admin-only fields) |
| POST | `/api/admin/users` | Create a user |
| PATCH | `/api/admin/users/{id}` | Update a user |
| DELETE | `/api/admin/users/{id}` | Delete a user |
| GET | `/api/admin/activity` | Activity log feed |
| GET | `/api/admin/openai` | Read OpenAI configuration (model + key status + feature toggles) |
| PUT | `/api/admin/openai` | Update OpenAI config (models, tokens, temp, persisted API key, `owner_suggestion_enabled`) |
| POST | `/api/admin/recompute-size-ages` | Queue a Celery task that infers `size_age_min/max_months` for items with a `size` but no age range yet |
| GET | `/api/admin/languages` | Read AI language config |
| PUT | `/api/admin/languages` | Update `supported_languages` and `default_language` |

`PUT /api/admin/openai` accepts an optional `openai_api_key` field — pass
an empty string to clear the persisted key (falls back to the
`OPENAI_API_KEY` env var). The persisted key takes precedence over the
env var for both the vision classifier and the semantic search query
parser.

`PUT /api/admin/languages` body shape:

```json
{
  "supported_languages": ["en", "no", "de"],
  "default_language": "en"
}
```

The OpenAI prompt builder iterates `supported_languages`, so adding a
new code makes the next item ingestion produce names + descriptions in
that language without any code change. `default_language` must be
present in `supported_languages`.

### Setup

Public endpoints used by the first-run wizard. See
[First-Run Setup](#first-run-setup) above.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/setup/status` | Returns `{needs_setup: bool}`, no auth |
| POST | `/api/setup/complete` | One-shot bootstrap (409 if any user exists) |

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful deletion) |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid/missing credentials |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

Validation errors:
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

Currently, StorageHub does not enforce rate limits. However, for production deployments, consider implementing rate limiting at the reverse proxy level (nginx, Traefik, etc.).

---

## Examples

### Home Assistant Configuration

#### REST Sensor

```yaml
# configuration.yaml
sensor:
  - platform: rest
    name: StorageHub Items
    resource: http://storagehub.local/api/ha/stats
    headers:
      X-API-Key: !secret storagehub_api_key
    value_template: "{{ value_json.total_items }}"
    json_attributes:
      - total_locations
      - total_containers
      - total_photos
      - items_needing_review

  - platform: rest
    name: StorageHub Overdue Reminders
    resource: http://storagehub.local/api/ha/reminders
    headers:
      X-API-Key: !secret storagehub_api_key
    value_template: "{{ value_json.overdue_reminders }}"
    json_attributes:
      - due_today
      - due_this_week
      - pending_reminders
```

#### Webhook Automation

```yaml
# automations.yaml
automation:
  - alias: "StorageHub - New Item Notification"
    trigger:
      - platform: webhook
        webhook_id: storagehub_item_created
    action:
      - service: notify.mobile_app
        data:
          title: "New Item Added"
          message: "{{ trigger.json.data.name }} was added to {{ trigger.json.data.container_name }}"

  - alias: "StorageHub - Reminder Due"
    trigger:
      - platform: webhook
        webhook_id: storagehub_reminder
    condition:
      - condition: template
        value_template: "{{ trigger.json.event == 'reminder.due' }}"
    action:
      - service: notify.mobile_app
        data:
          title: "StorageHub Reminder"
          message: "{{ trigger.json.data.title }}"
```

#### Template Sensor for Search

```yaml
# configuration.yaml
rest_command:
  storagehub_search:
    url: "http://storagehub.local/api/ha/search"
    method: GET
    headers:
      X-API-Key: !secret storagehub_api_key
    payload: '{"q": "{{ query }}"}'
```

### Python Example

```python
import requests

API_KEY = "shub_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
BASE_URL = "http://storagehub.local/api"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Get inventory stats
response = requests.get(f"{BASE_URL}/ha/stats", headers=headers)
stats = response.json()
print(f"Total items: {stats['total_items']}")

# Search for items
response = requests.get(
    f"{BASE_URL}/ha/search",
    headers=headers,
    params={"q": "winter jacket", "limit": 10}
)
results = response.json()
for item in results["items"]:
    print(f"- {item['name']} in {item['container_name']}")
```

### cURL Examples

```bash
# Get system status (no auth required)
curl http://storagehub.local/api/ha/status

# Get inventory stats
curl -H "X-API-Key: shub_xxx" http://storagehub.local/api/ha/stats

# Search for items
curl -H "X-API-Key: shub_xxx" "http://storagehub.local/api/ha/search?q=red%20jacket"

# Get container by QR code
curl -H "X-API-Key: shub_xxx" http://storagehub.local/api/ha/containers/qr/aOXfG4Td_nQ

# Create a webhook
curl -X POST http://storagehub.local/api/webhooks \
  -H "Cookie: session_token=your-session" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Home Assistant",
    "url": "http://homeassistant.local:8123/api/webhook/storagehub",
    "events": ["item.created", "reminder.due"]
  }'
```

---

## Changelog

### v1.2.1 (2026-05-05) — semantic search for HA

- **`GET /api/ha/search/semantic`** is new. Same response shape as
  `/api/ha/search`. Adds two pieces over the lexical endpoint:
  *(a)* owner pre-filter via the same token-pattern logic from v1.2.0
  (English `'s` strip + Norwegian `s`-stem ≥ 4 chars), so
  `?q=Sverres+genser` is restricted to Sverre's items; *(b)* synonym
  expansion via the same machinery the web UI uses
  (`SemanticSearchService.parse_query()`), so `?q=genser` finds
  items named `Cardigan` even though no field literally contains
  "genser". Implementation is synonym-expanded LIKE matching, not
  vector embeddings — the response includes only items the
  expansion reaches. Requires the `search` scope.

### v1.2.0 (2026-05-03) — HA integration support

- **`GET /api/ha/status`** now returns `instance_id` (UUID). Stable
  per-database; lets the HA integration use it as its config-entry
  `unique_id` and migrate cleanly when the user changes the
  StorageHub host URL.
- **`GET /api/ha/search?q=...`** now matches the *owner's name*
  alongside `name` / `description` / `ai_names` / `ai_descriptions`.
  Multi-token queries require every token to match some field, so
  `?q=Sverre+jakke` finds Sverre's jackets (not every jacket).
  English apostrophe-s possessive (`Sverre's` → `Sverre`) is
  stripped during tokenization. Norwegian possessive `s` is handled
  naturally by substring matching — no special-casing needed.
- **`GET /api/ha/items/index`** is new: a lite item record per row
  (id, name, owner_name, container_name, location_name, ai_names)
  designed for the HA Lovelace card's as-you-type filter. Returns
  an `ETag` and honors `If-None-Match` with a `304 Not Modified`.
  Requires the `read` scope. Responses are gzipped via the new
  `GZipMiddleware` (>1 KB threshold).

### v1.1.0 (2026-05-03)

- **Profile users**: `User.is_profile`, `birthdate`, `gender` for
  household members who own items but never log in. The login screen
  filters them out via `?include_profiles=false`.
- **AI owner suggestion**: vision classifier returns
  `suggested_owner_id` + `owner_suggestion_reason` (admin toggle:
  `owner_suggestion_enabled`).
- **Outgrown view**: `Item.size_age_min_months` / `size_age_max_months`
  + new `GET /api/outgrown` endpoint with inherit-to suggestions.
  `POST /api/admin/recompute-size-ages` backfills age ranges for
  existing items.
- **Declutter / Triage**: `Item.triage_decision` + `triage_decided_at`
  + `triage_show_after`, plus the `/api/triage/*` family of endpoints
  (`next`, `decide`, `undo`, `mark-donated`, `filters`, `discard`).

### v1.0.0 (2025-12-09)

- Initial API release
- Home Assistant integration API (`/api/ha/*`)
- API key authentication
- Webhook support for real-time events
- Comprehensive inventory statistics
- QR code container lookup

---

## Support

- GitHub Issues: [Report bugs or request features](https://github.com/your-repo/storagehub/issues)
- Documentation: Check `/api/docs` for interactive OpenAPI documentation

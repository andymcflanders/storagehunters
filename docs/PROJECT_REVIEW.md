# Project Review — 2026-07-18

Full audit of the codebase, infrastructure, and documentation. Every finding below was
verified against the code (file:line references included). Findings are grouped by
severity; the documentation drift that was found has been **fixed in this same branch**,
so this file records only the code/infra issues that still need fixing.

## Fixed in this branch

A follow-up commit ("harden auth + fix broken endpoints + add smoke suite") resolved the
authorization holes and the never-exercised endpoints, and added the missing test/CI
safety net:

- **C1 / C2 / H1 — authorization.** `POST /api/users` and `DELETE /api/users/{id}` are
  now admin-only; `PATCH`/avatar are self-or-admin; first-boot bootstrap goes through the
  one-shot `POST /api/setup/complete`. Every previously open read endpoint (items,
  containers, locations, tags, search, printers, QR) now requires a session. `GET /api/users`
  stays public for the login card grid but returns a minimal PII-free projection
  (`PublicUserResponse`). Deploy tooling (`create-admin.sh`, `justfile`) updated to the
  setup endpoint.
- **C3 — public share links** no longer 500 (dropped the non-existent `quantity`, use
  `filepath`, eager-load `Item.images`, atomic view-count increment).
- **H6 — HA reminders** month-end crash fixed (`timedelta(days=7)`).
- **H7 — tag merge** now takes the `TagMerge` body the frontend sends.
- **H8 — JSON export** serializes `Decimal` value estimates.
- **H5 — `network_ipp` printers** creatable (migration `024`).
- **M12 — `UserUpdate`** no longer advertises `role`/`is_active` (admin-only concerns).
- **Tests/CI** — a pytest smoke suite (`backend/tests/`) now logs in and exercises all 158
  API routes once, with a coverage guard that fails if any route goes untested, regression
  tests for each bug above, and auth-enforcement tests. A GitHub Actions workflow
  (`.github/workflows/ci.yml`) runs it against Postgres + Redis, plus frontend
  `svelte-check`. A `frontend/package-lock.json` was committed (fixes M16).

The remaining findings below are **not yet fixed** and are the recommended next steps.

---

## Critical

### C1. Unauthenticated admin account creation (full takeover)
`backend/app/api/users.py:49` — `POST /api/users` has no auth dependency and honors
`role: "admin"` in the payload. Combined with `AuthService.login()` creating a session
with no password whenever `requires_password` is false
(`backend/app/services/auth.py:81`), any anonymous visitor can do:

```
POST /api/users  {"name":"x","role":"admin","requires_password":false}
POST /api/auth/login  {"user_id": "<returned id>"}
```

…and is now a full admin. The deploy tooling (`deploy/create-admin.sh`, `justfile`
`create-admin` recipe) relies on this open endpoint, so it can't simply be locked —
first-boot bootstrap needs a different mechanism (e.g. allow unauthenticated creation
only when zero users exist, like `/api/setup` already does).

### C2. Any authenticated user can hijack or delete any account
`backend/app/api/users.py:106` (PATCH) and `:165` (DELETE) require login but no
admin/self check. A passwordless card-tap household user can set an admin's password
(or clear `requires_password`) and log in as them, or delete the admin. Properly
guarded variants already exist in `admin.py` — these unguarded ones are leftovers.

### C3. Public share links are completely broken (500 on every view)
`backend/app/api/shares.py:275-276` reads `item.quantity` (no such column on `Item`)
and `item.images[0].url` (the column is `filepath`). Every share link with
`allow_item_view=True` — the default — crashes. Additionally the query at `:257`
doesn't eager-load `Item.images`, which would raise `MissingGreenlet` in async context
even after the attribute names are fixed.

### C4. Hard page reload bounces logged-in users to the login screen
`frontend/src/routes/+layout.svelte:18` fires `auth.initialize()` without awaiting it,
while every guarded page checks `$user` synchronously in `onMount` (which runs before
the layout's). On refresh or deep link, `$user` is still `null` → redirect to `/login`,
and the login page never reacts when the session restore completes. The auth store's
`initialized` flag exists but nothing consumes it.

---

## High

### H1. Most read endpoints require no authentication
Entire inventory + PII readable anonymously: `GET /api/items` (+detail),
`GET /api/containers` (list, by-QR incl. full item list, detail, QR PNG, path),
`GET /api/locations` (+stats/detail), `GET /api/tags`, `GET /api/search` (both),
`GET /api/users` (returns email, birthdate, gender, role — the login card grid only
needs id/name/avatar), and `GET /api/printers/*` including `/download` and `/preview`,
which invoke the **paid OpenAI summary generator** — anonymous callers can rack up API
spend. Unused `OptionalUser`/`AnyAuthUser` deps in `deps.py:118-218` look like the
intended-but-never-wired fix.

### H2. Webhook event system is dead code
`trigger_webhook_event` (`backend/app/services/webhook_service.py:172`) has **zero
production callers** — only the manual `/api/webhooks/{id}/test` endpoint delivers
anything. Users can subscribe to 17 documented event types that are never emitted.
No Celery task scans for due reminders either (beat schedule contains only
`check-scheduled-backups`).

### H3. SSRF via webhook URLs
`WebhookCreate.url` is an unvalidated string; the service POSTs to it and stores the
first 1000 bytes of the response (`webhook_service.py:113,119`), which the deliveries
API returns. Any authenticated user can probe internal-network services and read the
responses (cloud metadata, internal admin ports…). Needs scheme/private-IP validation.

### H4. Stored XSS via uploaded file extension
`image_storage.py:29` preserves the client-supplied file extension; the only guard is
the client-controlled `Content-Type` header. Upload HTML as `x.html` with
`Content-Type: image/png` → served from `/uploads` on the app origin with an HTML MIME
type → script execution against the cookie-authenticated app. Whitelist extensions and/or
verify magic bytes (Pillow is already a dependency).

### H5. `network_ipp` printer type missing from the DB enum
`backend/app/models/printer.py:21` defines `NETWORK_IPP` and the API/schemas/dispatch
expose it, but no migration ever ran `ALTER TYPE printer_type_enum ADD VALUE
'network_ipp'`. Creating an IPP printer fails at the database.

### H6. `/api/ha/reminders` crashes during the last week of every month
`homeassistant.py:241` — `today_start.replace(day=today_start.day + 7)` raises
`ValueError` whenever day+7 exceeds the month length. Use `+ timedelta(days=7)`.

### H7. Tag merge can never succeed (contract mismatch)
`tags.py:96` declares bare params → FastAPI expects a raw JSON array body +
`target_tag_id` query param; the frontend posts an object → guaranteed 422. The unused
`TagMerge` schema shows the intended body was never wired in.

### H8. JSON export 500s when any item has a value estimate
`export.py:102,111` — `json.dumps` on a `Decimal` from `Numeric(10,2)` raises
`TypeError`. (CSV path is fine.)

### H9. Backup schedule edits return 405 from the admin UI
`frontend/src/lib/api/backup.ts:328` uses `POST`; the backend route is
`PATCH /api/admin/backup/schedules/{id}`. Both call sites (edit + pause/resume toggle)
are broken.

### H10. Production env template cannot boot the stack
`deploy/.env.production.example` lacked the required `POSTGRES_PASSWORD`, carried a
placeholder `SECRET_KEY` that passes the compose guard, and defined ~10 variables
compose never reads. **Fixed in this branch** (regenerated from the working root
`.env.example`).

### H11. Backups: silent failure, DB-only, no restore path
`deploy/backup.sh` has no `set -e`/`pipefail` — an SSH or pg_dump failure still writes
a `.gz` and prints success. It hardcodes user/db names and never backs up the
`uploads_data` volume (all photos, for a photo-inventory app). No restore script exists.
The in-app backup system likewise exports only locations/containers/tags/items/image
metadata/users — not reminders, shares, activity, or settings.

### H12. Let's Encrypt machinery cannot work
`ssl_manager.py:198` shells out to certbot **inside the backend container**, where it
is not installed; it also reads `/etc/letsencrypt/live/…` while the certs volume is
mounted at `/app/certs`. The dedicated certbot container only runs `sleep 1d` — nothing
ever execs into it, so nothing renews. Any manually issued cert dies after 90 days.

---

## Medium

- **M1. Container→child navigation shows stale data** — `containers/[id]/+page.svelte`
  loads only in `onMount`; navigating to a child container (same route) keeps the old
  contents. Same class: item→item via search dropdown, and re-searching from `/search`.
- **M2. AI name-suggestion banner can never appear** —
  `items/[id]/+page.svelte:61` `$: aiSuggestedName = getAISuggestedName()` has no
  reactive deps, runs once while `item` is null. Banner + button are dead code.
- **M3. Celery workers cache AI settings forever** — settings/key changes made in the
  admin panel never reach a running worker (separate process-level cache, no
  invalidation); a worker that starts on the mock classifier stays on it until restart.
- **M4. AI task failures are swallowed** — classification errors return an error dict
  (task "succeeds", `max_retries=3` never used); malformed model responses are parsed
  to an empty result and the item is permanently marked `ai_processed=True`, blocking
  reprocessing while the API call was still paid for.
- **M5. Moving a container between locations orphans its descendants in God View** —
  children keep the old `location_id` and vanish from the tree
  (`inventory.py:262`, `containers.py` PATCH).
- **M6. Restore handshake breaks under multiple workers/restarts** — in-memory
  `_pending_restores` dict (`backup.py:961`); also Google Drive download temp dirs are
  never cleaned (`backup.py:1459` — `BackgroundTasks().add_task(...)` returns `None`).
- **M7. Deleting an item leaks its image files on disk** (`items.py:240` — DB cascade
  only; containers do clean up).
- **M8. `MAX_UPLOAD_SIZE_MB` is never enforced** — endpoints `await file.read()`
  unbounded; meanwhile nginx hardcodes `client_max_body_size 20M`, so the documented
  tunable silently caps at 20 MB anyway.
- **M9. HTTPS redirect only covers `/`** — with SSL enabled, `/api/`, `/uploads/`,
  `/docs` are still served over cleartext HTTP (`nginx/nginx.conf` — the redirect
  placeholder exists only in `location /`). Credentials can transit plain HTTP.
- **M10. Deploys are full outages with a fake health gate** — `deploy.sh` does
  `down` → `up -d` → `sleep 5` → prints success regardless; workers also start against
  the old schema while the backend runs migrations.
- **M11. Sign-out leaves a blank page** (no redirect after `auth.logout()`), and there
  is no global 401 handling when the 30-day session expires mid-use.
- **M12. `UserUpdate.role`/`is_active` accepted but silently ignored** by
  `PATCH /api/users/{id}`; item edit can never *clear* an owner (`owner_id: undefined`
  is dropped from the JSON, backend needs explicit `null`).
- **M13. Item page flashes a skeleton every 3 s while AI polling runs**
  (`loadItem()` sets `loading = true` on each tick).
- **M14. QR scanning silently breaks without the CDN** — jsQR is loaded from
  jsdelivr at runtime in an otherwise self-hosted app; if it fails, the camera runs
  and simply never scans. Vendor the library.
- **M15. Naive `datetime.utcnow()` vs `timestamptz` columns** in backup scheduling —
  schedules fire at shifted times when Postgres isn't running in UTC.
- **M16. Non-reproducible frontend builds** — no `package-lock.json` committed and the
  Dockerfile runs `npm install`; every image build resolves deps fresh.

## Low (abbreviated)

Share view-count increment race (`shares.py:264`); SSL PATCH wipes omitted fields;
plaintext session tokens in DB (API keys are hashed — sessions aren't) and no expired-
session purge; `verify_password` 500s on a corrupt hash; unused deps `python-jose`
(CVE history) and `openai` in requirements; dangling `primary_image_id` after image
delete; webhook `attempt_count` fabricated; semantic-search size regex matches the
possessive "s" (`"sonja's"` → size filter `s`) and bare numbers; O(N) web search loads
all matches per request; dead root `nginx.conf`; provisioning script creates unused
`/opt/storagehub/data/*` dirs; `justfile reset` (destroys all data) gated only by a
5-second sleep; migration 001 creates boolean columns nullable with no server default;
`frontend batch-pdf` client targets a nonexistent endpoint; autocomplete responses can
arrive out of order.

---

## Testing & CI: none

Zero test files exist in the repo. `pyproject.toml` configures pytest and
`requirements-dev.txt` pins pytest/pytest-asyncio/pytest-cov — all unused. There is no
`.github/` workflow. The only automated gate is `svelte-check` via an **opt-in**
pre-commit hook that swallows its own output. Nearly every Critical/High bug above
(broken shares, tag merge, JSON export, month-end HA crash, 405 on schedule edit) is
exactly the class of bug a thin API-level test suite would have caught on first run.

---

## Honest assessment

**The good.** The product surface is genuinely impressive for its size: a coherent
domain model, a polished bilingual UI with disciplined i18n (374 keys, perfectly
symmetric), thoughtful features (declutter triage, outgrown tracking, owner suggestion,
HA integration with ETag-friendly index endpoints), careful recent code (the HA module,
triage, admin, api-keys are well built), a tidy migration chain, and a sound
docker-compose topology. Frontend resource hygiene (streams, listeners, intervals) is
consistently good.

**The bad.** Two systemic problems dominate:

1. **Authorization was never designed, only sprinkled.** Write endpoints mostly check
   login but not privilege; many read endpoints check nothing. The result is C1/C2/H1 —
   remote full takeover. This needs one deliberate pass: a default-deny dependency on
   every router, an explicit public allowlist (login grid, setup, share tokens, health),
   and admin checks on user mutation.
2. **Nothing is ever executed before shipping.** No tests, no CI, and several features
   (shares, tag merge, JSON export, IPP printers, schedule editing) fail on their *first
   real use* — they cannot ever have been run end-to-end. The webhook system and the
   Let's Encrypt flow are wired on both ends but connected in the middle to nothing.

**Priority order if you do nothing else:**
1. Lock down auth (C1, C2, H1) — this is a remote-takeover hole today.
2. Add CI with a smoke-test suite that logs in and hits every endpoint once
   (would have caught ~10 of the findings above); commit a `package-lock.json`.
3. Fix the five "first-use" breaks: shares (C3), tag merge (H7), JSON export (H8),
   schedule PATCH (H9), HA month-end (H6).
4. Fix the auth-init race (C4) — it's the single worst daily UX defect.
5. Decide webhooks' fate: wire `trigger_webhook_event` into the CRUD paths + a
   reminder-due beat task, or remove the feature and its docs.
6. Make backups trustworthy: include uploads, fail loudly, write + test a restore doc.
7. Either fix or remove the in-container certbot flow (H12) and extend the HTTPS
   redirect to all locations (M9).

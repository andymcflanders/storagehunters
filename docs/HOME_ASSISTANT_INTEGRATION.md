# StorageHub Home Assistant Integration Guide

This guide helps you integrate StorageHub with Home Assistant for inventory tracking, automations, and voice-activated item search.

## Quick Start

### 1. Create an API Key

1. Log into StorageHub web UI as an admin
2. Open the Admin panel and select the **API Keys** tab
3. Create a new key with `read` and `search` scopes
4. Copy the key (starts with `shub_`)

### 2. Add to secrets.yaml

```yaml
# secrets.yaml
storagehub_api_key: shub_your-api-key-here
```

> The examples below hardcode `http://storagehub.local` as the base URL.
> Replace it with whatever URL your StorageHub instance is reachable at
> (e.g. `https://192.168.200.13` for a LAN IP behind self-signed HTTPS,
> or `https://storagehub.example.com` for a public domain). The API key
> is the part you actually want in `secrets.yaml`.

### 3. Basic Sensors

Add to your `configuration.yaml`:

```yaml
sensor:
  # Total inventory count
  - platform: rest
    name: StorageHub Total Items
    resource: http://storagehub.local/api/ha/stats
    headers:
      X-API-Key: !secret storagehub_api_key
    value_template: "{{ value_json.total_items }}"
    unit_of_measurement: "items"
    scan_interval: 300
    json_attributes:
      - total_locations
      - total_containers
      - total_photos
      - items_needing_review
      - items_by_condition
      - items_by_season

  # Overdue reminders
  - platform: rest
    name: StorageHub Overdue Reminders
    resource: http://storagehub.local/api/ha/reminders
    headers:
      X-API-Key: !secret storagehub_api_key
    value_template: "{{ value_json.overdue_reminders }}"
    unit_of_measurement: "reminders"
    scan_interval: 3600
    json_attributes:
      - total_reminders
      - pending_reminders
      - due_today
      - due_this_week
```

---

## Sensor Examples

### Inventory Statistics Dashboard

```yaml
sensor:
  - platform: rest
    name: StorageHub Stats
    resource: http://storagehub.local/api/ha/stats
    headers:
      X-API-Key: !secret storagehub_api_key
    value_template: "{{ value_json.total_items }}"
    json_attributes:
      - total_locations
      - total_containers
      - total_photos
      - total_tags
      - items_needing_review
      - items_by_condition
      - items_by_season
    scan_interval: 300

# Template sensors for dashboard
template:
  - sensor:
      - name: "Items Needing Attention"
        state: >
          {{ state_attr('sensor.storagehub_stats', 'items_needing_review') | int +
             state_attr('sensor.storagehub_stats', 'items_by_condition')['damaged'] | default(0) | int +
             state_attr('sensor.storagehub_stats', 'items_by_condition')['needs_repair'] | default(0) | int }}
        unit_of_measurement: "items"

      - name: "Winter Items Count"
        state: "{{ state_attr('sensor.storagehub_stats', 'items_by_season')['winter'] | default(0) }}"
        unit_of_measurement: "items"
```

### Location-Specific Sensors

Find a location's UUID by calling `GET /api/ha/locations` once with curl,
or copy it from the URL when viewing the location in the StorageHub web
UI (`/locations/<uuid>`).

```yaml
sensor:
  - platform: rest
    name: Garage Storage
    resource: http://storagehub.local/api/ha/locations/00000000-0000-0000-0000-000000000000
    headers:
      X-API-Key: !secret storagehub_api_key
    value_template: "{{ value_json.item_count }}"
    unit_of_measurement: "items"
    json_attributes:
      - name
      - container_count
```

### Reminder Notifications

```yaml
sensor:
  - platform: rest
    name: StorageHub Reminders
    resource: http://storagehub.local/api/ha/reminders
    headers:
      X-API-Key: !secret storagehub_api_key
    value_template: "{{ value_json.overdue_reminders }}"
    json_attributes:
      - total_reminders
      - pending_reminders
      - due_today
      - due_this_week
      - reminders_by_type
    scan_interval: 3600
```

---

## Automations

### Daily Reminder Check

```yaml
automation:
  - alias: "StorageHub Daily Reminder Check"
    trigger:
      - platform: time
        at: "09:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.storagehub_reminders
        above: 0
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "StorageHub Reminders"
          message: >
            You have {{ states('sensor.storagehub_reminders') }} overdue reminders
            and {{ state_attr('sensor.storagehub_reminders', 'due_today') }} due today.
          data:
            url: http://storagehub.local/reminders
```

### Seasonal Item Alert

```yaml
automation:
  - alias: "StorageHub Winter Clothes Reminder"
    trigger:
      - platform: template
        value_template: "{{ now().month == 10 and now().day == 1 }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Time for Winter Clothes!"
          message: >
            You have {{ state_attr('sensor.storagehub_stats', 'items_by_season')['winter'] | default(0) }}
            winter items in storage. Time to bring them out!
```

---

## Webhooks for Real-Time Updates

> StorageHub emits real events (`item.created`, `item.moved`,
> `reminder.due`, `reminder.overdue`, `reminder.completed`, etc.) and
> delivers them to your registered webhooks in the background. Point a
> webhook at your Home Assistant webhook URL — a LAN address like
> `http://homeassistant.local:8123/api/webhook/<id>` is fine; private LAN
> ranges are permitted. Use `POST /api/webhooks/{id}/test` to confirm
> connectivity before relying on it.

### 1. Create a Webhook in Home Assistant

Add a webhook automation trigger:

```yaml
automation:
  - alias: "StorageHub Item Created"
    trigger:
      - platform: webhook
        webhook_id: storagehub_events
        allowed_methods:
          - POST
    action:
      - choose:
          - conditions:
              - condition: template
                value_template: "{{ trigger.json.event == 'item.created' }}"
            sequence:
              - service: notify.mobile_app_your_phone
                data:
                  title: "New Item in StorageHub"
                  message: "{{ trigger.json.data.name }} added to {{ trigger.json.data.container_name }}"

          - conditions:
              - condition: template
                value_template: "{{ trigger.json.event == 'reminder.due' }}"
            sequence:
              - service: notify.mobile_app_your_phone
                data:
                  title: "StorageHub Reminder"
                  message: "{{ trigger.json.data.title }}"
```

### 2. Register Webhook in StorageHub

Via web UI or API:

```bash
curl -X POST http://storagehub.local/api/webhooks \
  -H "Cookie: session_token=YOUR-SESSION" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Home Assistant",
    "url": "http://homeassistant.local:8123/api/webhook/storagehub_events",
    "events": [
      "item.created",
      "item.updated",
      "item.moved",
      "reminder.due",
      "reminder.overdue"
    ],
    "secret": "optional-secret-for-verification"
  }'
```

---

## Voice Search with Google Assistant / Alexa

### REST Command for Search

```yaml
rest_command:
  storagehub_search:
    url: "http://storagehub.local/api/ha/search"
    method: GET
    headers:
      X-API-Key: !secret storagehub_api_key
    content_type: "application/json"
```

### Intent Script

```yaml
intent_script:
  FindItem:
    speech:
      text: >
        {% set items = state_attr('sensor.storagehub_search_results', 'items') %}
        {% if items and items | length > 0 %}
          Found {{ items[0].name }} in {{ items[0].container_name }} at {{ items[0].location_name }}.
        {% else %}
          Sorry, I couldn't find that item in your inventory.
        {% endif %}
    action:
      - service: rest_command.storagehub_search
        data:
          query: "{{ query }}"
```

### Example Voice Commands

- "Hey Google, where is my red jacket?"
- "Alexa, find my winter boots"
- "Hey Google, what's in the garage storage?"

---

## NFC/QR Code Scanning

Container QR codes are short URL-safe base64 tokens like `aOXfG4Td_nQ`,
embedded in URLs of the form `http://storagehub.local/c/<token>`. The
in-app QR generator produces stickers that resolve straight to the
container detail page; the same token can also be looked up via the
Home Assistant API.

### Android Automation with Tasker/NFC

1. Scan the QR code (you'll get a URL like `http://storagehub.local/c/aOXfG4Td_nQ`)
2. Extract the token after `/c/` and call StorageHub:
   ```
   GET http://storagehub.local/api/ha/containers/qr/aOXfG4Td_nQ
   ```
3. Display container contents

### Home Assistant NFC Tag

```yaml
automation:
  - alias: "StorageHub QR Scan"
    trigger:
      - platform: tag
        tag_id: storagehub-container-aoxfg4td
    action:
      - service: rest_command.get_container
        data:
          qr_code: "aOXfG4Td_nQ"
      - service: notify.mobile_app_your_phone
        data:
          title: "Container Contents"
          message: "{{ states('sensor.storagehub_container_scan') }}"
```

---

## Dashboard Card Examples

### Inventory Overview Card

```yaml
type: entities
title: StorageHub Inventory
entities:
  - entity: sensor.storagehub_total_items
    name: Total Items
  - entity: sensor.storagehub_stats
    type: attribute
    attribute: total_containers
    name: Containers
  - entity: sensor.storagehub_stats
    type: attribute
    attribute: total_locations
    name: Locations
  - entity: sensor.storagehub_stats
    type: attribute
    attribute: items_needing_review
    name: Needs Review
```

### Reminders Card

```yaml
type: entities
title: StorageHub Reminders
entities:
  - entity: sensor.storagehub_overdue_reminders
    name: Overdue
    icon: mdi:alert-circle
  - entity: sensor.storagehub_reminders
    type: attribute
    attribute: due_today
    name: Due Today
  - entity: sensor.storagehub_reminders
    type: attribute
    attribute: due_this_week
    name: Due This Week
```

### Conditional Alert Card

```yaml
type: conditional
conditions:
  - entity: sensor.storagehub_overdue_reminders
    state_not: "0"
card:
  type: markdown
  content: >
    ## ⚠️ Attention Required

    You have **{{ states('sensor.storagehub_overdue_reminders') }}** overdue reminders!

    [View Reminders](http://storagehub.local/reminders)
```

---

## Troubleshooting

### API Key Issues

1. Verify key is active in StorageHub UI
2. Check key has required scopes (`read`, `search`)
3. Test with curl:
   ```bash
   curl -H "X-API-Key: shub_xxx" http://storagehub.local/api/ha/status
   ```

### Webhook Not Receiving Events

1. Check the webhook is active in StorageHub and subscribed to the events you expect
2. Confirm delivery attempts under `GET /api/webhooks/{id}/deliveries` — a
   blocked entry means the SSRF policy refused the target (e.g. a loopback or
   metadata address; set `WEBHOOK_BLOCK_PRIVATE_NETWORKS=false`/default to
   allow LAN targets)
3. Verify the Home Assistant webhook URL is reachable from the StorageHub host
4. Make sure the Celery worker and beat scheduler are running (reminder
   due/overdue events come from the periodic scan)
3. Check webhook delivery history in StorageHub
4. Test webhook manually:
   ```bash
   curl -X POST http://storagehub.local/api/webhooks/{id}/test \
     -H "Cookie: session_token=xxx" \
     -H "Content-Type: application/json" \
     -d '{"event": "stats.updated"}'
   ```

### Sensor Not Updating

1. Check `scan_interval` setting
2. Verify API is accessible from Home Assistant
3. Check Home Assistant logs for errors
4. Manually test API endpoint

---

## API Endpoints Quick Reference

| Endpoint | Description |
|----------|-------------|
| `GET /api/ha/status` | System status (no auth) |
| `GET /api/ha/stats` | Inventory statistics |
| `GET /api/ha/reminders` | Reminder summary |
| `GET /api/ha/reminders/list` | Detailed reminder list |
| `GET /api/ha/locations` | All locations |
| `GET /api/ha/locations/{id}` | Single location |
| `GET /api/ha/containers` | All containers |
| `GET /api/ha/containers/{id}` | Single container |
| `GET /api/ha/containers/qr/{code}` | Container by QR code |
| `GET /api/ha/items` | All items |
| `GET /api/ha/items/index` | Lite item index (ETag-cached, includes `primary_image_url`) |
| `GET /api/ha/items/{id}` | Single item |
| `GET /api/ha/search?q=query` | Search items |
| `GET /api/ha/search/semantic?q=query` | Semantic search (owner pre-filter + synonym expansion) |
| `GET /api/ha/tags` | All tags |

All endpoints (except `/status`) require `X-API-Key` header. The
`/api/ha/search` and `/api/ha/search/semantic` endpoints additionally
require the API key to have the `search` scope (the rest need `read`).

---

## Getting Help

- Full API Documentation: See `API_DOCUMENTATION.md`
- Interactive API Docs: `http://storagehub.local/docs`
- Issues: Report on GitHub

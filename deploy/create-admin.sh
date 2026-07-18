#!/bin/bash
#
# Create the first admin account on a fresh instance.
#
# Uses the one-shot POST /api/setup/complete bootstrap endpoint, which
# refuses once any user exists — so this only works on a brand-new
# install. Admins sign in via email + password ("Administer this
# instance" on the login screen), so all three arguments are required.
#
# Usage:
#   ./deploy/create-admin.sh "Admin Name" "admin@example.com" "password123"
#
set -euo pipefail

SERVER_HOST="${STORAGEHUB_SERVER:-192.168.200.13}"
API_URL="https://${SERVER_HOST}"  # Uses HTTPS via nginx

NAME="${1:-}"
EMAIL="${2:-}"
PASSWORD="${3:-}"

if [[ -z "$NAME" || -z "$EMAIL" || -z "$PASSWORD" ]]; then
    echo "Usage: $0 <name> <email> <password>"
    echo ""
    echo "Example:"
    echo "  $0 'John Doe' 'john@example.com' 'secretpass'"
    echo ""
    echo "Note: only works on a fresh instance with no users yet."
    echo "On an existing instance, create users from Admin -> Users."
    exit 1
fi

JSON=$(python3 - "$NAME" "$EMAIL" "$PASSWORD" <<'PYEOF'
import json, sys
print(json.dumps({
    "admin_name": sys.argv[1],
    "admin_email": sys.argv[2],
    "admin_password": sys.argv[3],
    "admin_language": "en",
}))
PYEOF
)

echo "Creating admin account '${NAME}' on ${API_URL}..."
echo ""

# -k: the fresh instance serves a self-signed certificate on first boot.
RESPONSE=$(curl -sk -w "\n%{http_code}" -X POST "${API_URL}/api/setup/complete" \
    -H "Content-Type: application/json" \
    -d "${JSON}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [[ "$HTTP_CODE" == "200" ]]; then
    echo "Admin account created successfully!"
    echo ""
    echo "Response:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    echo ""
    echo "You can now log in at: https://${SERVER_HOST} (Administer this instance)"
else
    echo "Failed to create admin (HTTP ${HTTP_CODE})"
    echo ""
    echo "Response:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    echo ""
    echo "If the instance already has users, this bootstrap endpoint is"
    echo "closed by design — create users from Admin -> Users instead."
    exit 1
fi

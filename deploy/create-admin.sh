#!/bin/bash
#
# Create the first admin user
#
# Usage:
#   ./deploy/create-admin.sh "Admin Name" "admin@example.com" "password123"
#   ./deploy/create-admin.sh "Admin Name"  # No password (household mode)
#

SERVER_HOST="${STORAGEHUB_SERVER:-192.168.200.13}"
API_URL="https://${SERVER_HOST}"  # Uses HTTPS via nginx

NAME="${1:-Admin}"
EMAIL="${2:-}"
PASSWORD="${3:-}"

if [[ -z "$1" ]]; then
    echo "Usage: $0 <name> [email] [password]"
    echo ""
    echo "Examples:"
    echo "  $0 'John Doe' 'john@example.com' 'secretpass'  # With password"
    echo "  $0 'John Doe'                                   # No password (household mode)"
    exit 1
fi

# Build JSON payload
if [[ -n "$PASSWORD" ]]; then
    JSON=$(cat <<EOF
{
    "name": "${NAME}",
    "email": "${EMAIL}",
    "password": "${PASSWORD}",
    "requires_password": true,
    "role": "admin",
    "language": "en"
}
EOF
)
else
    JSON=$(cat <<EOF
{
    "name": "${NAME}",
    "email": ${EMAIL:+\"$EMAIL\"}${EMAIL:-null},
    "requires_password": false,
    "role": "admin",
    "language": "en"
}
EOF
)
fi

echo "Creating admin user '${NAME}' on ${API_URL}..."
echo ""

RESPONSE=$(curl -sk -w "\n%{http_code}" -X POST "${API_URL}/api/users" \
    -H "Content-Type: application/json" \
    -d "${JSON}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [[ "$HTTP_CODE" == "201" ]]; then
    echo "Admin user created successfully!"
    echo ""
    echo "Response:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    echo ""
    echo "You can now log in at: http://${SERVER_HOST}:3000"
else
    echo "Failed to create user (HTTP ${HTTP_CODE})"
    echo ""
    echo "Response:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    exit 1
fi

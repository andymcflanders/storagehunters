#!/bin/sh
set -e

CERT_DIR="/etc/nginx/certs"
CERT_FILE="$CERT_DIR/fullchain.pem"
KEY_FILE="$CERT_DIR/privkey.pem"
NGINX_CONF="/etc/nginx/nginx.conf"
NGINX_CONF_TEMPLATE="/etc/nginx/nginx.conf.template"
RELOAD_SIGNAL_FILE="$CERT_DIR/.reload_nginx"

# Function to check if certificates exist and are valid
check_certs() {
    if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
        # Check if certificate is valid (not expired)
        if openssl x509 -checkend 0 -noout -in "$CERT_FILE" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Function to configure nginx based on SSL availability
configure_nginx() {
    cp "$NGINX_CONF_TEMPLATE" "$NGINX_CONF"

    if check_certs; then
        echo "SSL certificates found and valid. Enabling HTTPS..."
        # Enable HTTPS redirect in HTTP block
        sed -i 's|# SSL_REDIRECT_PLACEHOLDER|return 301 https://$host$request_uri;|g' "$NGINX_CONF"
    else
        echo "No valid SSL certificates. Running HTTP only..."
        # Remove the HTTPS server block
        sed -i '/# SSL_SERVER_BLOCK_START/,/# SSL_SERVER_BLOCK_END/d' "$NGINX_CONF"
        # Remove the redirect placeholder comment
        sed -i '/# SSL_REDIRECT_PLACEHOLDER/d' "$NGINX_CONF"
    fi
}

# Function to reload nginx
reload_nginx() {
    echo "Reloading nginx configuration..."
    nginx -t && nginx -s reload
}

# Function to watch for certificate changes
watch_certs() {
    while true; do
        # Check for reload signal file
        if [ -f "$RELOAD_SIGNAL_FILE" ]; then
            echo "Reload signal detected..."
            rm -f "$RELOAD_SIGNAL_FILE"
            configure_nginx
            reload_nginx
        fi

        sleep 5
    done
}

# Initial configuration
echo "Configuring nginx..."
configure_nginx

# Start certificate watcher in background
watch_certs &

# Start nginx
echo "Starting nginx..."
exec nginx -g "daemon off;"

#!/bin/bash
# Run this script to request or renew certificates for your Django app.
# Set DOMAIN and EMAIL environment variables before running.

set -e

DOMAIN="${DOMAIN:-example.com}"
EMAIL="${EMAIL:-admin@example.com}"
WEBROOT="${WEBROOT:-/var/www/letsencrypt}"

sudo mkdir -p "$WEBROOT"

sudo certbot certonly \
    --webroot -w "$WEBROOT" \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email

sudo certbot renew --quiet --post-hook "systemctl reload nginx"

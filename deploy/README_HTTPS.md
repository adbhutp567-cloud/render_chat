# HTTPS Deployment Guide

## Django production settings

1. Use environment variables for secrets and deploy configuration:
   - `DJANGO_SECRET_KEY`
   - `DJANGO_DEBUG=false`
   - `DJANGO_ALLOWED_HOSTS=example.com www.example.com`
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com https://www.example.com`
   - `DJANGO_SECURE_SSL_REDIRECT=true`
   - `DJANGO_DB_ENGINE=django.db.backends.mysql`
   - `DJANGO_DB_NAME=chat`
   - `DJANGO_DB_USER=...`
   - `DJANGO_DB_PASSWORD=...`
   - `DJANGO_DB_HOST=127.0.0.1`
   - `DJANGO_DB_PORT=3306`

2. Secure cookie and HTTPS settings are enabled in `_core/settings.py`:
   - `SESSION_COOKIE_SECURE = True`
   - `CSRF_COOKIE_SECURE = True`
   - `SESSION_COOKIE_HTTPONLY = True`
   - `CSRF_COOKIE_HTTPONLY = True`
   - `SECURE_HSTS_SECONDS = 31536000`
   - `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
   - `SECURE_HSTS_PRELOAD = True`
   - `SECURE_SSL_REDIRECT = True`
   - `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`
   - `X_FRAME_OPTIONS = 'DENY'`

## Nginx configuration

Use `deploy/nginx_chatting.conf` as a template for your server block.
Replace `example.com` and the static/media alias paths before enabling it.

Key points:
- HTTP traffic is redirected to HTTPS.
- TLS termination occurs in Nginx.
- Secure headers are applied (`HSTS`, `X-Frame-Options`, `X-Content-Type-Options`).
- WebSocket proxying is enabled for `/ws/`.

## Let's Encrypt automation

1. Install Certbot and the Nginx plugin on your server.
2. Use `deploy/letsencrypt_renewal.sh` to request certificates and configure renewals.
3. Add a cron job or systemd timer to run renewal automatically:

```bash
0 3 * * * /bin/bash /path/to/chatting/deploy/letsencrypt_renewal.sh >> /var/log/letsencrypt/renew.log 2>&1
```

4. Ensure `systemctl reload nginx` is executed after renewal.

## Security best practices

- Never store production secrets in version control.
- Enable `DEBUG=False` in production.
- Use a strong `SECRET_KEY` from the environment.
- Limit `ALLOWED_HOSTS` to your actual domain names.
- Keep your server up to date and monitor logs.
- Use automated Renewals via Certbot and verify certificate expiry.

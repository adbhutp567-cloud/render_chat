# Render deployment guide

## 1. Environment variables
Set these in Render:
- `DJANGO_SECRET_KEY`
- `DATABASE_URL`
- `DJANGO_ALLOWED_HOSTS=your-app-name.onrender.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://your-app-name.onrender.com`
- `DJANGO_DEBUG=False`

## 2. Build and start commands
- Build: `./build.sh`
- Start: `gunicorn _core.wsgi:application`

## 3. Notes
- Render will serve static files with WhiteNoise.
- Use the PostgreSQL database addon or external Postgres URL.

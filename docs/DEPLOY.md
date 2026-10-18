# Deployment guide

## Backend → Render

1. Push this repo to GitHub.
2. In Render: **New → Blueprint** and select the repo (uses [`render.yaml`](../render.yaml)), **or** create a Web Service manually:
   - Root directory: `backend`
   - Runtime: Python 3.12
   - Build: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - Start: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
3. Attach a Postgres database (or use SQLite for a quick demo — not recommended for multi-instance).
4. Optional: add Redis and set `REDIS_URL`.
5. Env vars:
   - `DJANGO_ENV=prod`
   - `DJANGO_SECRET_KEY` (generate)
   - `ALLOWED_HOSTS=<your-service>.onrender.com`
   - `CORS_ALLOWED_ORIGINS=https://<your-vercel-app>.vercel.app`
   - `ORS_API_KEY` (free key from openrouteservice.org — recommended)
   - `DATABASE_URL` (from Render Postgres)
   - `REDIS_URL` (optional)

Free-tier cold starts: hit `GET /api/v1/healthz` before demos / Loom recording.

## Frontend → Vercel

1. Import the GitHub repo in Vercel.
2. Framework: Vite · Root directory: `frontend`
3. Install command: `pnpm install` (or `npm install`)
4. Build: `pnpm build`
5. Output: `dist`
6. Env: `VITE_API_BASE_URL=https://<your-render-api>.onrender.com`

[`frontend/vercel.json`](../frontend/vercel.json) already rewrites SPA routes to `index.html`.

## Loom

See [LOOM_SCRIPT.md](LOOM_SCRIPT.md). Pre-seed trips against the hosted API and open `https://<frontend>/?trip=<id>`.

## Checklist

- [ ] GitHub repo public (or shared with reviewers)
- [ ] Render API healthy at `/api/v1/healthz`
- [ ] Vercel frontend loads and plans a trip
- [ ] CORS allows the Vercel origin
- [ ] Loom 5–10 min recorded

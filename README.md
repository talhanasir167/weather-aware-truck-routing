# Weather-Aware Truck Routing

Full-stack assessment app: a truck driver enters origin, destination, departure time, and load weight; the app returns up to **3 route options**, samples weather along each route, scores risk with the assessment rules, recommends the safest route, and shows a **0–48h weather heatmap** along the corridor.

**Stack:** React + Vite + MapLibre · Django + DRF · Open-Meteo · OpenRouteService / OSRM · Photon · OpenFreeMap

## Quick start (local)

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
python manage.py migrate
python manage.py runserver
```

Optional: start Redis/Postgres with `docker compose up -d redis db`.

**ORS API key (recommended):** copy `.env.example` → `.env`, then get a free key at
[openrouteservice.org](https://openrouteservice.org/dev/#/signup) and set `ORS_API_KEY`.
The header badge shows **ORS truck routing** when configured; otherwise OSRM fallback
still returns up to 3 routes via via-point perturbation.

**Storm demo:** use **Load storm demo** in the UI (Chicago → Minneapolis + synthetic
High/Severe weather band) when the live forecast is calm — ideal for Loom walkthroughs.

### Frontend

```bash
cd frontend
pnpm install   # or npm install
pnpm dev
```

Open http://localhost:5173 — Vite proxies `/api` to the Django server.

### Tests

```bash
cd backend && source .venv/bin/activate && pytest
cd frontend && pnpm test
```

## API

See [docs/API.md](docs/API.md). Main endpoints:

- `POST /api/v1/trips/plan`
- `GET /api/v1/trips/{id}`
- `GET /api/v1/trips/{id}/heatmap`
- `GET /api/v1/geocode?q=`

## Docs

- [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md) — edge-case decisions
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/API.md](docs/API.md)
- [docs/LOOM_SCRIPT.md](docs/LOOM_SCRIPT.md) — walkthrough outline

## Deploy

Step-by-step: [docs/DEPLOY.md](docs/DEPLOY.md)

| Piece | Target |
|-------|--------|
| Frontend | Vercel (`frontend/`, Vite, env `VITE_API_BASE_URL`) |
| Backend | Render web service (`backend/`, Python 3.12 / Docker) |
| Database | Render Postgres (SQLite OK for local demos) |
| Cache | Upstash / Render Redis (`REDIS_URL`) |

`render.yaml` is a Render blueprint. After deploy, set `CORS_ALLOWED_ORIGINS` to the Vercel URL.

## Risk rules (summary)

| | Low | Moderate | High | Severe | No Travel |
|--|--|--|--|--|--|
| Wind | &lt;25 mph | 25–34 | 35–44 | 45–54 | ≥55 |
| Rain | &lt;0.10 in/hr | 0.10–0.25 | 0.25–0.50 | 0.50–1.00 | &gt;1.00 |
| Snow | &lt;0.5 in/hr | 0.5–1.0 | 1.0–2.0 | 2.0–3.0 | &gt;3.0 |

Load escalation: ≥55 mph → No Travel; 45–54 + &gt;30k lb → No Travel; 35–44 + &gt;40k lb → Severe.

Recommendation order: fewest Severe miles → fewest High → lowest avg risk → shortest time (No Travel routes demoted).

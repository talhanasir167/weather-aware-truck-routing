# Loom walkthrough script (5–10 min)

Pre-seed 1–2 trips via the API before recording so cold starts don't eat the clock:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/trips/plan \
  -H 'Content-Type: application/json' \
  -d '{
    "origin":"Chicago, IL","destination":"Detroit, MI",
    "departure":"2026-10-18T14:00:00Z","load_lb":20000,"interval_mi":25,
    "origin_lat":41.8781,"origin_lon":-87.6298,
    "destination_lat":42.3314,"destination_lon":-83.0458
  }'
```

Open the returned `?trip=<id>` URL in the hosted frontend.

## Outline

1. **Intro (30s)** — What the app does: safest truck route by weather + load + time.
2. **Inputs (1 min)** — Show form: origin, destination, departure, load, 10/25/50 interval. Point at ORS badge in the header.
3. **Three routes (2 min)** — Map with 3 alternatives; recommended badge; severe/high miles; avg risk. Note ETA labels on checkpoints.
4. **Why this one won (1 min)** — Read `recommendation.reasons` aloud.
5. **Checkpoint drill-down (1–2 min)** — Click a checkpoint; show ETA, wind/rain/snow, band reason.
6. **Heatmap slider (2 min)** — Play 0–48h; toggle risk/wind; note no network on scrub.
7. **Storm demo (1–2 min)** — Click **Load storm demo** (Chicago → Minneapolis). Show High/Severe miles differing by route and a glowing heatmap. Optional: raise load above 40k lb if you want load-escalation / No Travel.
8. **Close (30s)** — Repo link, stack (React + Django + Open-Meteo + ORS/OSRM), thanks.

## Hosted demo tips

- Hit `/api/v1/healthz` once before recording to wake Render free tier.
- Prefer pre-seeded `trip_id` links over live planning on camera.

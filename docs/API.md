# API Reference

Base URL (local): `http://127.0.0.1:8000`

## `GET /api/v1/healthz`

Returns `{ "status": "ok" }`.

## `GET /api/v1/geocode?q=`

Geocode a place name (or `lat,lon`). Requires 3+ characters unless comma-separated coordinates.

```json
{
  "results": [
    { "label": "Chicago, Illinois, United States", "lat": 41.88, "lon": -87.63 }
  ]
}
```

## `POST /api/v1/trips/plan`

Plan a weather-aware trip.

**Body**

| Field | Type | Notes |
|-------|------|-------|
| origin | string | Required |
| destination | string | Required |
| departure | string | Timezone-aware ISO 8601 (e.g. `2026-10-17T12:00:00Z`) |
| load_lb | int | 1–200000 |
| interval_mi | 10\|25\|50 | Default 25 |
| origin_lat / origin_lon | float | Optional; skips geocode when set |
| destination_lat / destination_lon | float | Optional |

**Response** `201` — full trip plan with up to 3 routes, checkpoints, metrics, and recommendation.

## `GET /api/v1/trips/{id}`

Reload a persisted plan.

## `GET /api/v1/trips/{id}/heatmap`

Returns the corridor grid and all 49 hourly frames:

```json
{
  "grid_points": [{ "lat": 41.9, "lon": -87.6 }],
  "hours": ["2026-10-17T12:00:00Z", "..."],
  "frames": {
    "risk": [[...]],
    "wind": [[...]],
    "rain": [[...]],
    "snow": [[...]]
  }
}
```

# Architecture

```
React (Vercel) ──POST /trips/plan──▶ Django/DRF (Render)
                                      ├─ geo (Photon / Nominatim)
                                      ├─ routing (ORS → OSRM + via-point top-up)
                                      ├─ weather (Open-Meteo + Redis cache)
                                      ├─ risk (pure functions)
                                      ├─ planner (persist Trip / RoutePlan / Checkpoint)
                                      └─ heatmap (corridor grid × 49 hours)
```

## Backend apps

| App | Responsibility |
|-----|----------------|
| `core` | healthz, exception handler |
| `geo` | geocoding, haversine, polylines |
| `routing` | provider adapters, 3-route guarantee, sampling, ETA |
| `weather` | Open-Meteo, grid dedupe, cache |
| `risk` | thresholds, load rules, aggregate, recommend (**no I/O**) |
| `planner` | orchestration + persistence |
| `heatmap` | corridor + 49-frame payload |

## Frontend features

| Feature | UI |
|---------|-----|
| `trip-form` | Origin/destination autocomplete, departure, load, interval |
| `route-map` | MapLibre + OpenFreeMap, route lines, checkpoint markers |
| `route-list` | Summary cards + recommendation reasons |
| `checkpoints` | Detail panel + timeline |
| `heatmap` | GPU heatmap layer + 0–48h slider |

## Key invariants

1. `apps.risk` imports nothing from Django, httpx, or the clock.
2. Segment miles sum to route distance.
3. Heatmap slider never triggers network I/O (all 49 frames prefetched).

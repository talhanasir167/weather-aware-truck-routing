# Assumptions & Design Decisions

Decisions made where the assessment brief is underspecified.

## Risk classification

- Band boundaries: **lower inclusive, upper exclusive**, evaluated highest-first.
- Wind No Travel uses `≥55` mph; rain/snow No Travel use strict `>` (so rain exactly 1.00 and snow exactly 3.0 are Severe).
- Wind 54.0–54.9 mph is Severe (No Travel begins at 55).
- Checkpoint base band = `max(wind, rain, snow)`.
- Load escalation applied after base; never downgrades.
- **Sustained wind** (`wind_speed_10m`) is classified; gusts are informational.
- **`rain`** (not `precipitation`) feeds the rain band to avoid double-counting snow.

## Sampling

- Interval is **user-selectable**: 10 / 25 / 50 miles (default **25**).
- Exact-distance interpolation between polyline vertices.
- Destination always included as a checkpoint.

## Mileage attribution

- Each checkpoint owns the midpoint-split segment between neighbors.
- Segment miles sum to exactly the route distance.

## Recommendation

- Sort key: `(blocked, no_travel_miles, severe_miles, high_miles, avg_risk, duration_s)`.
- `avg_risk` = distance-weighted mean of band scores 0–4.
- Routes with No Travel miles are `blocked` and sorted last.
- If all routes are blocked, least-bad is still returned with a warning.
- Values rounded (0.1 mi, 3 decimals on avg_risk) before comparison.

## Routing / 3-route guarantee

- Primary: OpenRouteService `driving-hgv` with `alternative_routes`.
- Fallback: public OSRM.
- If fewer than 3 distinct routes: via-point perturbation (±30/±60 mi lateral offsets at midpoint) + geometry overlap dedupe (>70% rejected).
- If still fewer than 3: return what exists with `meta.degraded: ["fewer_than_3_routes"]`.

### ORS spike findings (Phase 0)

- ORS requires a free API key (`ORS_API_KEY`). Without it the app uses OSRM.
- Free-tier `alternative_routes` rejects trips longer than ~100 km (error 2004). We
  retry a single HGV route, then top up to 3 distinct corridors with via-points.
- Public OSRM often returns only 2 alternatives for long-haul US pairs; via-point top-up is required to meet the "3 route options" requirement.
- Recorded during planning: Chicago→Detroit OSRM returned 2 routes; via-point perturbation produced a valid third (352 mi vs 282 mi direct).
- Re-run of `scripts/ors_spike.py` (no ORS key): Chicago→Detroit **OSRM=2**, Dallas→Houston **OSRM=1**, Denver→KansasCity **OSRM=1**. Confirms via-point top-up is mandatory for the 3-route requirement on free OSRM.

## Weather

- Open-Meteo, keyless, `wind_speed_unit=mph`, `precipitation_unit=inch`.
- Grid snap ~0.1° + hour bucket before fetch; Redis/locmem cache.
- Checkpoints past forecast horizon marked `forecast_unavailable`, excluded from avg risk numerics as Low with a flag.

## Heatmap

- 48-hour window starts at **departure time** (not "now").
- 49 hourly frames (hours 0–48) delivered in one response.
- Corridor grid distinct from route checkpoints (~20 mi spacing, ±25 mi lateral, capped at 150 points).

## Load weight vs routing

- `load_lb` drives risk escalation only.
- Not sent to ORS as an HGV weight restriction by default, so the 3 routes stay comparable.

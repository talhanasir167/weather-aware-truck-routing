export interface GeocodeResult {
  label: string
  lat: number
  lon: number
  city?: string | null
  state?: string | null
  country?: string | null
}

export interface Checkpoint {
  index: number
  lat: number
  lon: number
  distance_mi: number
  eta_utc: string
  segment_miles: number
  band: string
  wind_mph: number
  wind_gusts_mph: number
  rain_in_hr: number
  snow_in_hr: number
  weather_available: boolean
  reasons: Record<string, unknown>
}

export interface RouteMetrics {
  severe_miles: number
  high_miles: number
  moderate_miles: number
  low_miles: number
  no_travel_miles: number
  avg_risk: number
  worst_band: string
  blocked: boolean
  total_miles: number
  band_miles?: Record<string, number>
}

export interface RouteOption {
  id: string
  provider: string
  distance_m: number
  distance_mi: number
  duration_s: number
  duration_h: number
  geometry: [number, number][]
  metrics: RouteMetrics
  summary: string
  is_recommended: boolean
  rank: number
  checkpoints: Checkpoint[]
}

export interface TripPlan {
  id: string
  origin: { label: string; lat: number; lon: number }
  destination: { label: string; lat: number; lon: number }
  departure_utc: string
  load_lb: number
  interval_mi: number
  recommendation: { route_id: string; reasons: string[] }
  degraded: string[]
  meta: Record<string, unknown>
  routes: RouteOption[]
  created_at: string
}

export interface HeatmapData {
  trip_id: string
  grid_points: { lat: number; lon: number }[]
  hours: string[]
  frames: {
    risk: number[][]
    wind: number[][]
    rain: number[][]
    snow: number[][]
  }
  meta: Record<string, unknown>
}

export interface PlanRequest {
  origin: string
  destination: string
  departure: string
  load_lb: number
  interval_mi: 10 | 25 | 50
  origin_lat?: number
  origin_lon?: number
  destination_lat?: number
  destination_lon?: number
  /** Inject synthetic storm corridor for Loom / calm forecasts */
  demo_storm?: boolean
}

export interface ApiStatus {
  status: string
  ors_configured: boolean
  routing: { primary: string; fallback: string }
  weather: string
  geocoding: string
  demo_storm_available: boolean
}

import { create } from 'zustand'
import type { Checkpoint, HeatmapData, RouteOption, TripPlan } from '../api/types'

interface TripState {
  trip: TripPlan | null
  selectedRouteId: string | null
  selectedCheckpoint: Checkpoint | null
  heatmap: HeatmapData | null
  /** Hours after departure; may be fractional while playing for smooth truck motion. */
  heatmapHourIndex: number
  heatmapMetric: 'risk' | 'wind' | 'rain' | 'snow'
  heatmapPlaying: boolean
  loading: boolean
  error: string | null
  setTrip: (trip: TripPlan | null) => void
  setSelectedRouteId: (id: string | null) => void
  setSelectedCheckpoint: (cp: Checkpoint | null) => void
  setHeatmap: (h: HeatmapData | null) => void
  setHeatmapHourIndex: (i: number) => void
  setHeatmapMetric: (m: 'risk' | 'wind' | 'rain' | 'snow') => void
  setHeatmapPlaying: (p: boolean) => void
  setLoading: (v: boolean) => void
  setError: (e: string | null) => void
  selectedRoute: () => RouteOption | null
}

export const useTripStore = create<TripState>((set, get) => ({
  trip: null,
  selectedRouteId: null,
  selectedCheckpoint: null,
  heatmap: null,
  heatmapHourIndex: 0,
  heatmapMetric: 'risk',
  heatmapPlaying: false,
  loading: false,
  error: null,
  setTrip: (trip) =>
    set({
      trip,
      selectedRouteId: trip?.recommendation.route_id ?? trip?.routes[0]?.id ?? null,
      selectedCheckpoint: null,
      heatmap: null,
      heatmapHourIndex: 0,
      error: null,
    }),
  setSelectedRouteId: (id) => set({ selectedRouteId: id, selectedCheckpoint: null }),
  setSelectedCheckpoint: (cp) => set({ selectedCheckpoint: cp }),
  setHeatmap: (h) => set({ heatmap: h }),
  setHeatmapHourIndex: (i) => set({ heatmapHourIndex: i }),
  setHeatmapMetric: (m) => set({ heatmapMetric: m }),
  setHeatmapPlaying: (p) => set({ heatmapPlaying: p }),
  setLoading: (v) => set({ loading: v }),
  setError: (e) => set({ error: e }),
  selectedRoute: () => {
    const { trip, selectedRouteId } = get()
    if (!trip || !selectedRouteId) return null
    return trip.routes.find((r) => r.id === selectedRouteId) ?? null
  },
}))

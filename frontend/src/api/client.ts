import type { ApiStatus, GeocodeResult, HeatmapData, PlanRequest, TripPlan } from './types'

const BASE = import.meta.env.VITE_API_BASE_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
  if (!res.ok) {
    let message = res.statusText
    try {
      const body = await res.json()
      message = body?.error?.message ?? body?.detail ?? JSON.stringify(body)
    } catch {
      /* ignore */
    }
    throw new Error(message)
  }
  return res.json() as Promise<T>
}

export function geocode(q: string): Promise<{ results: GeocodeResult[] }> {
  return request(`/api/v1/geocode?q=${encodeURIComponent(q)}`)
}

export function planTrip(body: PlanRequest): Promise<TripPlan> {
  return request('/api/v1/trips/plan', { method: 'POST', body: JSON.stringify(body) })
}

export function getTrip(id: string): Promise<TripPlan> {
  return request(`/api/v1/trips/${id}`)
}

export function getHeatmap(id: string): Promise<HeatmapData> {
  return request(`/api/v1/trips/${id}/heatmap`)
}

export function getStatus(): Promise<ApiStatus> {
  return request('/api/v1/status')
}

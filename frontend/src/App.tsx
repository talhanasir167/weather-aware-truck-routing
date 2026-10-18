import { useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TripForm } from './features/trip-form/TripForm'
import { RouteSummaryList } from './features/route-list/RouteSummaryList'
import { CheckpointPanel } from './features/checkpoints/CheckpointPanel'
import { RouteMap } from './features/route-map/RouteMap'
import { RoutingStatus } from './components/RoutingStatus'
import { getHeatmap, getTrip } from './api/client'
import { useTripStore } from './store/tripStore'
import './App.css'

const queryClient = new QueryClient()

function Shell() {
  const error = useTripStore((s) => s.error)
  const trip = useTripStore((s) => s.trip)
  const setTrip = useTripStore((s) => s.setTrip)
  const setHeatmap = useTripStore((s) => s.setHeatmap)
  const setError = useTripStore((s) => s.setError)

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get('trip')
    if (!id) return
    getTrip(id)
      .then((t) => {
        setTrip(t)
        return getHeatmap(t.id)
      })
      .then(setHeatmap)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load trip'))
  }, [setTrip, setHeatmap, setError])

  const isStormDemo = Boolean(trip?.meta?.demo_storm)

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Weather-Aware Truck Routing</h1>
          <p>Safest route by weather risk, load weight, and travel time</p>
        </div>
        <div className="header-actions">
          <RoutingStatus />
          {isStormDemo && <span className="storm-badge">Storm demo</span>}
          {trip && (
            <a className="share-link" href={`?trip=${trip.id}`}>
              Share plan
            </a>
          )}
        </div>
      </header>
      <div className="layout">
        <aside className="sidebar">
          <TripForm />
          {error && <div className="error-banner">{error}</div>}
          <RouteSummaryList />
          <CheckpointPanel />
        </aside>
        <main className="main-map">
          <RouteMap />
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Shell />
    </QueryClientProvider>
  )
}

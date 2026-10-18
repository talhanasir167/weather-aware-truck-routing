import { useEffect, useState } from 'react'
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

type SidebarTab = 'plan' | 'results'

function Shell() {
  const error = useTripStore((s) => s.error)
  const trip = useTripStore((s) => s.trip)
  const loading = useTripStore((s) => s.loading)
  const setTrip = useTripStore((s) => s.setTrip)
  const setHeatmap = useTripStore((s) => s.setHeatmap)
  const setError = useTripStore((s) => s.setError)
  const [tab, setTab] = useState<SidebarTab>('plan')

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get('trip')
    if (!id) return
    getTrip(id)
      .then((t) => {
        setTrip(t)
        setTab('results')
        return getHeatmap(t.id)
      })
      .then(setHeatmap)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load trip'))
  }, [setTrip, setHeatmap, setError])

  const isStormDemo = Boolean(trip?.meta?.demo_storm)
  const routeCount = trip?.routes.length ?? 0

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Weather-Aware Truck Routing</h1>
          <p>Compare up to 3 corridors · pick the safest by weather risk</p>
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
          <nav className="sidebar-tabs" aria-label="Sidebar sections">
            <button
              type="button"
              className={tab === 'plan' ? 'active' : ''}
              onClick={() => setTab('plan')}
            >
              <span className="tab-step">1</span>
              Plan
            </button>
            <button
              type="button"
              className={tab === 'results' ? 'active' : ''}
              onClick={() => setTab('results')}
              disabled={!trip && !loading}
            >
              <span className="tab-step">2</span>
              Routes
              {routeCount > 0 && <span className="tab-count">{routeCount}</span>}
            </button>
          </nav>

          {error && <div className="error-banner">{error}</div>}

          {tab === 'plan' && (
            <>
              <TripForm onPlanned={() => setTab('results')} />
              {!trip && (
                <ol className="howto">
                  <li>
                    <strong>Plan</strong> — origin, destination, departure, load
                  </li>
                  <li>
                    <strong>Compare</strong> — up to 3 routes ranked by risk
                  </li>
                  <li>
                    <strong>Scrub weather</strong> — 0–48h corridor on the map
                  </li>
                </ol>
              )}
            </>
          )}

          {tab === 'results' && (
            <>
              {!trip && loading && (
                <p className="muted sidebar-empty">Planning routes…</p>
              )}
              {!trip && !loading && (
                <p className="muted sidebar-empty">
                  No plan yet — switch to <button type="button" className="text-link" onClick={() => setTab('plan')}>Plan</button> and run a trip.
                </p>
              )}
              {trip && (
                <>
                  <RouteSummaryList onEditPlan={() => setTab('plan')} />
                  <CheckpointPanel />
                </>
              )}
            </>
          )}
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

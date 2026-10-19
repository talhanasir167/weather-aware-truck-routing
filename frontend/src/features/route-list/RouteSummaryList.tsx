import { colorForBand } from '../../lib/riskColors'
import { useTripStore } from '../../store/tripStore'

type Props = {
  onEditPlan?: () => void
}

export function RouteSummaryList({ onEditPlan }: Props) {
  const trip = useTripStore((s) => s.trip)
  const selectedRouteId = useTripStore((s) => s.selectedRouteId)
  const setSelectedRouteId = useTripStore((s) => s.setSelectedRouteId)

  if (!trip) return null

  const ordered = [...trip.routes].sort((a, b) => a.rank - b.rank)
  const otherNotes = trip.degraded.filter(
    (d) => !['ors_auth', 'ors_error', 'weather_partial'].includes(d),
  )

  return (
    <section className="route-list">
      <header className="route-list-header">
        <div className="route-list-title-row">
          <h2>Compare routes</h2>
          {onEditPlan && (
            <button type="button" className="text-link" onClick={onEditPlan}>
              Edit plan
            </button>
          )}
        </div>
        {trip.recommendation.reasons.length > 0 && (
          <p className="rec-reasons">
            <span className="rec-label">Why recommended</span>
            {trip.recommendation.reasons.join(' · ')}
          </p>
        )}
        {trip.meta?.demo_storm ? (
          <p className="storm-note">Synthetic storm band on — risk differences are demo weather.</p>
        ) : null}
        {trip.degraded.includes('weather_partial') ? (
          <p className="degraded">
            Some forecasts were unavailable — try again, or use <strong>Load storm demo</strong> for
            the Loom.
          </p>
        ) : null}
        {trip.degraded.includes('ors_error') && trip.meta?.routing_provider !== 'ors' ? (
          <p className="ors-note">Truck routing fell back to OSRM for this trip.</p>
        ) : null}
        {otherNotes.length > 0 && (
          <p className="degraded">Note: {otherNotes.join(', ')}</p>
        )}
      </header>
      <ul>
        {ordered.map((route) => {
          const selected = selectedRouteId === route.id
          return (
            <li key={route.id}>
              <button
                type="button"
                className={`route-card ${selected ? 'selected' : ''} ${
                  route.is_recommended ? 'recommended' : ''
                }`}
                onClick={() => setSelectedRouteId(route.id)}
              >
                <div className="route-card-top">
                  <strong>{route.id.replace('_', ' ')}</strong>
                  {route.is_recommended && <span className="badge">Best</span>}
                  {route.metrics.blocked && <span className="badge danger">No Travel</span>}
                </div>
                <div className="route-stats">
                  <span>{route.distance_mi.toFixed(0)} mi</span>
                  <span>{route.duration_h.toFixed(1)} h</span>
                  <span
                    className="band-pill"
                    style={{ color: colorForBand(route.metrics.worst_band) }}
                  >
                    {route.metrics.worst_band}
                  </span>
                </div>
                {selected && (
                  <div className="route-metrics">
                    <span>Severe {route.metrics.severe_miles.toFixed(1)} mi</span>
                    <span>High {route.metrics.high_miles.toFixed(1)} mi</span>
                    <span>Avg {route.metrics.avg_risk.toFixed(2)}</span>
                  </div>
                )}
              </button>
            </li>
          )
        })}
      </ul>
      <p className="section-hint">Select a route to highlight it on the map. Click a green/yellow/red checkpoint for weather at that mile.</p>
    </section>
  )
}

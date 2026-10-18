import { colorForBand } from '../../lib/riskColors'
import { useTripStore } from '../../store/tripStore'

export function RouteSummaryList() {
  const trip = useTripStore((s) => s.trip)
  const selectedRouteId = useTripStore((s) => s.selectedRouteId)
  const setSelectedRouteId = useTripStore((s) => s.setSelectedRouteId)

  if (!trip) return null

  const ordered = [...trip.routes].sort((a, b) => a.rank - b.rank)

  return (
    <section className="route-list">
      <header className="route-list-header">
        <h2>Route options</h2>
        {trip.recommendation.reasons.length > 0 && (
          <p className="rec-reasons">
            Recommended because: {trip.recommendation.reasons.join('; ')}
          </p>
        )}
        {trip.meta?.demo_storm ? (
          <p className="storm-note">Storm demo active — synthetic High/Severe band on corridors</p>
        ) : null}
        {trip.meta?.ors_configured === false || trip.degraded.includes('ors_auth') ? (
          <p className="degraded">
            Routing via OSRM. For truck-aware ORS routes, set <code>ORS_API_KEY</code> in{' '}
            <code>backend/.env</code> (free at openrouteservice.org).
          </p>
        ) : trip.meta?.routing_provider === 'ors' ? (
          <p className="ors-note">OpenRouteService driving-hgv · truck profile</p>
        ) : null}
        {trip.degraded.filter((d) => d !== 'ors_auth').length > 0 && (
          <p className="degraded">
            Note: {trip.degraded.filter((d) => d !== 'ors_auth').join(', ')}
          </p>
        )}
      </header>
      <ul>
        {ordered.map((route) => (
          <li key={route.id}>
            <button
              type="button"
              className={`route-card ${selectedRouteId === route.id ? 'selected' : ''} ${
                route.is_recommended ? 'recommended' : ''
              }`}
              onClick={() => setSelectedRouteId(route.id)}
            >
              <div className="route-card-top">
                <strong>{route.id.replace('_', ' ')}</strong>
                {route.is_recommended && <span className="badge">Recommended</span>}
                {route.metrics.blocked && <span className="badge danger">No Travel</span>}
              </div>
              <div className="route-stats">
                <span>{route.distance_mi.toFixed(0)} mi</span>
                <span>{route.duration_h.toFixed(1)} h</span>
                <span
                  style={{ color: colorForBand(route.metrics.worst_band) }}
                  title="Worst band"
                >
                  {route.metrics.worst_band}
                </span>
              </div>
              <div className="route-metrics">
                <span>Severe: {route.metrics.severe_miles.toFixed(1)} mi</span>
                <span>High: {route.metrics.high_miles.toFixed(1)} mi</span>
                <span>Avg risk: {route.metrics.avg_risk.toFixed(2)}</span>
              </div>
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}

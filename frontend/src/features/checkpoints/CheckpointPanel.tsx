import { colorForBand } from '../../lib/riskColors'
import { useTripStore } from '../../store/tripStore'

export function CheckpointPanel() {
  const selected = useTripStore((s) => s.selectedCheckpoint)
  const route = useTripStore((s) => s.selectedRoute())
  const setSelectedCheckpoint = useTripStore((s) => s.setSelectedCheckpoint)

  if (!route) return null

  return (
    <section className="checkpoint-panel">
      <header className="checkpoint-header">
        <h3>Along the route</h3>
        <span className="muted small">{route.checkpoints.length} samples</span>
      </header>

      <div className="checkpoint-timeline" role="list" aria-label="Checkpoint risk strip">
        {route.checkpoints.map((cp) => (
          <button
            key={cp.index}
            type="button"
            role="listitem"
            className={`cp-dot ${selected?.index === cp.index ? 'active' : ''}`}
            style={{ background: colorForBand(cp.band) }}
            title={`${cp.band} · ${cp.distance_mi.toFixed(0)} mi · ${new Date(cp.eta_utc).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`}
            onClick={() => setSelectedCheckpoint(cp)}
          />
        ))}
      </div>

      {selected ? (
        <div className="checkpoint-detail">
          <div className="checkpoint-detail-top">
            <strong style={{ color: colorForBand(selected.band) }}>{selected.band}</strong>
            <span>
              #{selected.index} · {selected.distance_mi.toFixed(0)} mi
            </span>
          </div>
          <p className="checkpoint-eta">
            ETA {new Date(selected.eta_utc).toLocaleString(undefined, {
              month: 'short',
              day: 'numeric',
              hour: 'numeric',
              minute: '2-digit',
            })}
            {!selected.weather_available && ' · forecast unavailable'}
          </p>
          <ul className="wx-grid">
            <li>
              <span>Wind</span>
              <strong>{selected.wind_mph.toFixed(0)} mph</strong>
            </li>
            <li>
              <span>Gusts</span>
              <strong>{selected.wind_gusts_mph.toFixed(0)}</strong>
            </li>
            <li>
              <span>Rain</span>
              <strong>{selected.rain_in_hr.toFixed(2)} in/h</strong>
            </li>
            <li>
              <span>Snow</span>
              <strong>{selected.snow_in_hr.toFixed(1)} in/h</strong>
            </li>
          </ul>
        </div>
      ) : (
        <p className="muted small checkpoint-prompt">Tap a dot or a map checkpoint for details.</p>
      )}
    </section>
  )
}

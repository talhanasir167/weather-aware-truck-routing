import { colorForBand } from '../../lib/riskColors'
import { useTripStore } from '../../store/tripStore'

export function CheckpointPanel() {
  const selected = useTripStore((s) => s.selectedCheckpoint)
  const route = useTripStore((s) => s.selectedRoute())

  if (!route) return null

  return (
    <section className="checkpoint-panel">
      <h3>Checkpoints — {route.id.replace('_', ' ')}</h3>
      {selected ? (
        <div className="checkpoint-detail">
          <p>
            <strong>#{selected.index}</strong> at {selected.distance_mi.toFixed(1)} mi
          </p>
          <p>
            ETA: {new Date(selected.eta_utc).toLocaleString()}
          </p>
          <p style={{ color: colorForBand(selected.band) }}>
            Risk: <strong>{selected.band}</strong>
            {!selected.weather_available && ' (forecast unavailable)'}
          </p>
          <ul>
            <li>Wind: {selected.wind_mph.toFixed(1)} mph (gusts {selected.wind_gusts_mph.toFixed(1)})</li>
            <li>Rain: {selected.rain_in_hr.toFixed(3)} in/hr</li>
            <li>Snow: {selected.snow_in_hr.toFixed(2)} in/hr</li>
          </ul>
        </div>
      ) : (
        <p className="muted">Click a checkpoint on the map for details.</p>
      )}
      <div className="checkpoint-timeline">
        {route.checkpoints.map((cp) => (
          <button
            key={cp.index}
            type="button"
            className={`cp-dot ${selected?.index === cp.index ? 'active' : ''}`}
            style={{ background: colorForBand(cp.band) }}
            title={`${cp.band} @ ${cp.distance_mi.toFixed(0)} mi`}
            onClick={() => useTripStore.getState().setSelectedCheckpoint(cp)}
          />
        ))}
      </div>
    </section>
  )
}

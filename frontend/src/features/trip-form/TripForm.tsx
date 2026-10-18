import { useState } from 'react'
import { planTrip, getHeatmap } from '../../api/client'
import { useTripStore } from '../../store/tripStore'
import { LocationAutocomplete } from './LocationAutocomplete'

function defaultDeparture(): string {
  const d = new Date()
  d.setMinutes(0, 0, 0)
  d.setHours(d.getHours() + 1)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/** Chicago → Minneapolis — longer Midwest corridor works well for storm demo. */
const STORM_DEMO = {
  origin: 'Chicago, IL',
  originLat: 41.8781,
  originLon: -87.6298,
  dest: 'Minneapolis, MN',
  destLat: 44.9778,
  destLon: -93.265,
  loadLb: 42000,
  interval: 25 as const,
}

type Props = {
  onPlanned?: () => void
}

export function TripForm({ onPlanned }: Props) {
  const { setTrip, setHeatmap, setLoading, setError, loading } = useTripStore()
  const [origin, setOrigin] = useState('Chicago, IL')
  const [originLat, setOriginLat] = useState<number | undefined>(41.8781)
  const [originLon, setOriginLon] = useState<number | undefined>(-87.6298)
  const [dest, setDest] = useState('Detroit, MI')
  const [destLat, setDestLat] = useState<number | undefined>(42.3314)
  const [destLon, setDestLon] = useState<number | undefined>(-83.0458)
  const [departureLocal, setDepartureLocal] = useState(defaultDeparture)
  const [loadLb, setLoadLb] = useState(20000)
  const [interval, setInterval] = useState<10 | 25 | 50>(25)
  const [showAdvanced, setShowAdvanced] = useState(false)

  async function runPlan(opts: {
    demoStorm?: boolean
    origin?: string
    originLat?: number
    originLon?: number
    dest?: string
    destLat?: number
    destLon?: number
    loadLb?: number
    interval?: 10 | 25 | 50
  } = {}) {
    setLoading(true)
    setError(null)
    try {
      const local = new Date(departureLocal)
      if (Number.isNaN(local.getTime())) throw new Error('Invalid departure time')
      const departure = local.toISOString()

      const trip = await planTrip({
        origin: opts.origin ?? origin,
        destination: opts.dest ?? dest,
        departure,
        load_lb: opts.loadLb ?? loadLb,
        interval_mi: opts.interval ?? interval,
        origin_lat: opts.originLat ?? originLat,
        origin_lon: opts.originLon ?? originLon,
        destination_lat: opts.destLat ?? destLat,
        destination_lon: opts.destLon ?? destLon,
        demo_storm: opts.demoStorm ?? false,
      })
      setTrip(trip)
      onPlanned?.()
      getHeatmap(trip.id)
        .then(setHeatmap)
        .catch((err) => console.warn('Heatmap fetch failed', err))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Plan failed')
    } finally {
      setLoading(false)
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    await runPlan()
  }

  async function onStormDemo() {
    setOrigin(STORM_DEMO.origin)
    setOriginLat(STORM_DEMO.originLat)
    setOriginLon(STORM_DEMO.originLon)
    setDest(STORM_DEMO.dest)
    setDestLat(STORM_DEMO.destLat)
    setDestLon(STORM_DEMO.destLon)
    setLoadLb(STORM_DEMO.loadLb)
    setInterval(STORM_DEMO.interval)
    await runPlan({
      demoStorm: true,
      ...STORM_DEMO,
      loadLb: STORM_DEMO.loadLb,
      interval: STORM_DEMO.interval,
    })
  }

  return (
    <form className="trip-form" onSubmit={onSubmit}>
      <h2>Trip inputs</h2>
      <LocationAutocomplete
        label="Origin"
        value={origin}
        placeholder="City or lat,lon"
        onChange={(label, lat, lon) => {
          setOrigin(label)
          setOriginLat(lat)
          setOriginLon(lon)
        }}
      />
      <LocationAutocomplete
        label="Destination"
        value={dest}
        placeholder="City or lat,lon"
        onChange={(label, lat, lon) => {
          setDest(label)
          setDestLat(lat)
          setDestLon(lon)
        }}
      />
      <label className="field">
        <span>Departure</span>
        <input
          type="datetime-local"
          value={departureLocal}
          onChange={(e) => setDepartureLocal(e.target.value)}
          required
        />
      </label>
      <label className="field">
        <span>Load weight (lb)</span>
        <input
          type="number"
          min={1}
          max={200000}
          value={loadLb}
          onChange={(e) => setLoadLb(Number(e.target.value))}
          required
        />
      </label>

      <button
        type="button"
        className="advanced-toggle"
        aria-expanded={showAdvanced}
        onClick={() => setShowAdvanced((v) => !v)}
      >
        {showAdvanced ? 'Hide' : 'Show'} sampling options
      </button>
      {showAdvanced && (
        <label className="field">
          <span>Weather sample interval</span>
          <select
            value={interval}
            onChange={(e) => setInterval(Number(e.target.value) as 10 | 25 | 50)}
          >
            <option value={10}>Every 10 miles</option>
            <option value={25}>Every 25 miles</option>
            <option value={50}>Every 50 miles</option>
          </select>
        </label>
      )}

      <button type="submit" className="primary" disabled={loading}>
        {loading ? 'Planning…' : 'Find safest routes'}
      </button>
      <button
        type="button"
        className="secondary-btn"
        disabled={loading}
        onClick={onStormDemo}
        title="Chicago → Minneapolis with a synthetic storm band"
      >
        Load storm demo
      </button>
      <p className="form-hint">
        Storm demo uses CHI→MSP plus fake High/Severe weather — best for demos when the real forecast is calm.
      </p>
    </form>
  )
}

import { useEffect, useMemo, useRef, type CSSProperties } from 'react'
import { useTripStore } from '../../store/tripStore'
import './HeatmapControls.css'

/** Hours advanced per tick while playing (fractional = smoother truck). */
const STEP_H = 0.2
const TICK_MS = 100
const FORECAST_H = 48

export function HeatmapControls() {
  const heatmap = useTripStore((s) => s.heatmap)
  const hourIndex = useTripStore((s) => s.heatmapHourIndex)
  const setHour = useTripStore((s) => s.setHeatmapHourIndex)
  const metric = useTripStore((s) => s.heatmapMetric)
  const setMetric = useTripStore((s) => s.setHeatmapMetric)
  const playing = useTripStore((s) => s.heatmapPlaying)
  const setPlaying = useTripStore((s) => s.setHeatmapPlaying)
  const trip = useTripStore((s) => s.trip)
  const selectedRouteId = useTripStore((s) => s.selectedRouteId)

  /** Continuous playhead (hours). Heatmap uses Math.floor; truck uses full value. */
  const playheadRef = useRef(hourIndex)
  if (!playing) playheadRef.current = hourIndex

  const tripHours = useMemo(() => {
    const route = trip?.routes.find((r) => r.id === selectedRouteId)
    return Math.max(route?.duration_h ?? 0, 0.25)
  }, [trip, selectedRouteId])

  useEffect(() => {
    if (!playing || !heatmap) return
    if (playheadRef.current >= FORECAST_H) playheadRef.current = 0

    const id = window.setInterval(() => {
      let next = playheadRef.current + STEP_H
      if (next >= FORECAST_H) {
        playheadRef.current = FORECAST_H
        setHour(FORECAST_H)
        setPlaying(false)
        return
      }
      playheadRef.current = next
      // Store integer hour for heatmap frames; truck reads playhead via same setter path
      setHour(next)
    }, TICK_MS)
    return () => window.clearInterval(id)
  }, [playing, heatmap, setHour, setPlaying])

  const frameStats = useMemo(() => {
    if (!heatmap) return null
    const hi = Math.min(Math.floor(hourIndex), heatmap.hours.length - 1)
    const values = heatmap.frames[metric][hi] ?? []
    if (!values.length) return { avg: 0, max: 0 }
    const sum = values.reduce((a, b) => a + b, 0)
    return { avg: sum / values.length, max: Math.max(...values) }
  }, [heatmap, metric, hourIndex])

  if (!heatmap) return null

  const maxH = FORECAST_H
  const clampedHour = Math.min(Math.max(hourIndex, 0), maxH)
  const progressPct = (clampedHour / maxH) * 100
  const arrivalPct = Math.min(100, (tripHours / maxH) * 100)
  const truckPct = Math.min(arrivalPct, progressPct) // pin sticks at arrival after trip ends
  const arrived = clampedHour >= tripHours - 1e-6

  const frameIdx = Math.min(Math.floor(clampedHour), heatmap.hours.length - 1)
  const hourLabel = heatmap.hours[frameIdx]
    ? new Date(heatmap.hours[frameIdx]).toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : ''

  const unit =
    metric === 'risk' ? '' : metric === 'wind' ? ' mph' : metric === 'rain' ? ' in/hr' : ' in/hr'
  const avgLabel =
    metric === 'risk'
      ? `avg risk ${frameStats?.avg.toFixed(2) ?? '0'}`
      : `avg ${frameStats?.avg.toFixed(1) ?? '0'}${unit}`

  function togglePlay() {
    if (playing) {
      setPlaying(false)
      return
    }
    if (clampedHour >= maxH - 0.05) {
      playheadRef.current = 0
      setHour(0)
    }
    setPlaying(true)
  }

  return (
    <div className={`heatmap-controls ${playing ? 'is-playing' : ''}`}>
      <div className="heatmap-row">
        <div className="heatmap-title">
          <span className={`play-dot ${playing ? 'on' : ''}`} />
          <strong>Weather corridor</strong>
          {playing && <span className="live-badge">LIVE</span>}
        </div>
        <select
          value={metric}
          onChange={(e) => setMetric(e.target.value as typeof metric)}
          aria-label="Heatmap metric"
        >
          <option value="risk">Composite risk</option>
          <option value="wind">Wind</option>
          <option value="rain">Rain</option>
          <option value="snow">Snow</option>
        </select>
        <button type="button" className="play-btn" onClick={togglePlay}>
          {playing ? 'Pause' : 'Play'}
        </button>
      </div>

      <div className="slider-meta">
        <span className="hour-chip">+{clampedHour.toFixed(1)}h</span>
        <span>{hourLabel}</span>
        <span className="trip-phase">
          {arrived
            ? `Arrived (${tripHours.toFixed(1)}h) · forecast continues`
            : `Truck ${Math.min(100, (clampedHour / tripHours) * 100).toFixed(0)}% to destination`}
        </span>
        <span className="frame-stat">{avgLabel}</span>
      </div>

      <div
        className="scrubber"
        style={
          {
            '--progress': `${progressPct}%`,
            '--arrival': `${arrivalPct}%`,
            '--truck': `${truckPct}%`,
          } as CSSProperties
        }
      >
        {/* Trip segment (0 → arrival) vs post-arrival forecast */}
        <div className="scrubber__trip" />
        <div className="scrubber__arrival-line" title={`Arrival ~${tripHours.toFixed(1)}h`} />
        <div className="scrubber__truck-pin" title="Truck on timeline">
          🚛
        </div>
        <input
          className="forecast-slider"
          type="range"
          min={0}
          max={maxH}
          step={0.1}
          value={clampedHour}
          onChange={(e) => {
            setPlaying(false)
            const v = Number(e.target.value)
            playheadRef.current = v
            setHour(v)
          }}
          aria-label="Forecast hour 0 to 48"
        />
      </div>

      <div className="slider-ends">
        <span>0h departure</span>
        <span className="arrival-label">Arrival {tripHours.toFixed(1)}h</span>
        <span>+48h</span>
      </div>
    </div>
  )
}

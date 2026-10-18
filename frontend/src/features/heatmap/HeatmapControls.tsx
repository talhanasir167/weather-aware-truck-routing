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

  const playheadRef = useRef(hourIndex)

  useEffect(() => {
    if (!playing) playheadRef.current = hourIndex
  }, [hourIndex, playing])

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
  const truckPct = Math.min(arrivalPct, progressPct)
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
          <div className="heatmap-title-text">
            <strong>Time scrubber</strong>
            <span className="heatmap-sub">Truck drives until arrival · weather continues to +48h</span>
          </div>
          {playing && <span className="live-badge">PLAYING</span>}
        </div>
        <select
          value={metric}
          onChange={(e) => setMetric(e.target.value as typeof metric)}
          aria-label="Heatmap metric"
        >
          <option value="risk">Risk heatmap</option>
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
        <span className={`trip-phase ${arrived ? 'arrived' : ''}`}>
          {arrived
            ? `Truck parked · weather hour ${clampedHour.toFixed(0)}`
            : `Truck en route · ${Math.min(100, (clampedHour / tripHours) * 100).toFixed(0)}%`}
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
        <div className="scrubber__trip" title="Driving window" />
        <div className="scrubber__arrival-line" title={`Arrival ~${tripHours.toFixed(1)}h`} />
        <div className="scrubber__truck-pin" title="Truck position on trip">
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
          aria-label="Hours after departure, 0 to 48"
        />
      </div>

      <div className="slider-ends">
        <span>Depart 0h</span>
        <span className="arrival-label">Arrive {tripHours.toFixed(1)}h</span>
        <span>Weather +48h</span>
      </div>

      {metric === 'risk' && (frameStats?.max ?? 0) < 0.5 && (
        <p className="calm-hint">
          This hour is calm (avg risk {frameStats?.avg.toFixed(2) ?? '0'}) — soft glow = Low along the
          corridor. Switch metric to <strong>Wind</strong>, or run <strong>Load storm demo</strong> for
          High/Severe heat.
        </p>
      )}
    </div>
  )
}

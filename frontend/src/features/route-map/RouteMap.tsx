import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import Map, {
  Layer,
  Marker,
  NavigationControl,
  Popup,
  Source,
  type MapRef,
} from 'react-map-gl/maplibre'
import type { MapLayerMouseEvent } from 'maplibre-gl'
import { colorForBand } from '../../lib/riskColors'
import { pointAtFraction } from '../../lib/routeProgress'
import { useTripStore } from '../../store/tripStore'
import { HeatmapLayer } from '../heatmap/HeatmapLayer'
import { HeatmapControls } from '../heatmap/HeatmapControls'
import type { Checkpoint } from '../../api/types'
import './RouteMap.css'
import '../heatmap/HeatmapControls.css'

/** Dark basemap (free, MapLibre-compatible). */
const STYLE = 'https://tiles.openfreemap.org/styles/dark'

const ALT_COLORS = ['#38d4e0', '#8b5cf6', '#60a5fa']

export function RouteMap() {
  const mapRef = useRef<MapRef>(null)
  const wrapRef = useRef<HTMLDivElement>(null)
  const [mapReady, setMapReady] = useState(false)
  const [mapError, setMapError] = useState<string | null>(null)
  const [popupCp, setPopupCp] = useState<Checkpoint | null>(null)

  // Never leave the UI stuck on "Loading map…" if the style/worker fails.
  useEffect(() => {
    if (mapReady || mapError) return
    const t = window.setTimeout(() => {
      if (!mapReady) {
        setMapError('Map base layer timed out. Check console / network, then hard-refresh.')
      }
    }, 8000)
    return () => window.clearTimeout(t)
  }, [mapReady, mapError])

  const trip = useTripStore((s) => s.trip)
  const selectedRouteId = useTripStore((s) => s.selectedRouteId)
  const setSelectedCheckpoint = useTripStore((s) => s.setSelectedCheckpoint)
  const selectedCheckpoint = useTripStore((s) => s.selectedCheckpoint)
  const heatmap = useTripStore((s) => s.heatmap)
  const hourIndex = useTripStore((s) => s.heatmapHourIndex)
  const metric = useTripStore((s) => s.heatmapMetric)
  const playing = useTripStore((s) => s.heatmapPlaying)

  const selectedRoute = useMemo(
    () => trip?.routes.find((r) => r.id === selectedRouteId) ?? null,
    [trip, selectedRouteId],
  )

  // Shared clock: hours after departure (same as checkpoint ETAs + forecast hour).
  const tripDurationH = Math.max(selectedRoute?.duration_h || 1, 0.25)

  const truckPos = useMemo(() => {
    if (!selectedRoute?.geometry?.length) return null
    // Truck = where the vehicle is N hours after departure (clamped at destination).
    const t = Math.min(1, Math.max(0, hourIndex / tripDurationH))
    const [lon, lat] = pointAtFraction(
      selectedRoute.geometry as [number, number][],
      t,
    )
    return { lon, lat, t }
  }, [selectedRoute, hourIndex, tripDurationH])

  // Exactly one checkpoint: nearest to the truck along the route (no cluster ahead).
  const activeCheckpointIndexes = useMemo(() => {
    if (!selectedRoute?.checkpoints.length) return new Set<number>()
    const cps = selectedRoute.checkpoints
    const totalMi =
      selectedRoute.distance_mi ||
      cps[cps.length - 1]?.distance_mi ||
      1
    const t = Math.min(1, Math.max(0, hourIndex / tripDurationH))
    const targetMi = t * totalMi
    let best = cps[0]
    let bestDiff = Infinity
    for (const cp of cps) {
      const diff = Math.abs(cp.distance_mi - targetMi)
      if (diff < bestDiff) {
        bestDiff = diff
        best = cp
      }
    }
    return new Set([best.index])
  }, [selectedRoute, hourIndex, tripDurationH])

  const bounds = useMemo(() => {
    if (!trip) return null
    const coords = trip.routes.flatMap((r) => r.geometry)
    if (!coords.length) return null
    let minLon = Infinity
    let minLat = Infinity
    let maxLon = -Infinity
    let maxLat = -Infinity
    for (const [lon, lat] of coords) {
      minLon = Math.min(minLon, lon)
      maxLon = Math.max(maxLon, lon)
      minLat = Math.min(minLat, lat)
      maxLat = Math.max(maxLat, lat)
    }
    return [
      [minLon, minLat],
      [maxLon, maxLat],
    ] as [[number, number], [number, number]]
  }, [trip])

  const fitRoute = useCallback(() => {
    const map = mapRef.current
    if (!map || !bounds) return
    map.fitBounds(bounds, { padding: 72, duration: 900, maxZoom: 9 })
    ;[0, 150, 450].forEach((delay) =>
      setTimeout(() => {
        map.resize()
        map.getMap().triggerRepaint()
      }, delay),
    )
  }, [bounds])

  useEffect(() => {
    if (mapReady && bounds) fitRoute()
  }, [mapReady, bounds, fitRoute])

  // Keep GL canvas sized to the panel.
  useEffect(() => {
    const el = wrapRef.current
    if (!el) return
    const ro = new ResizeObserver(() => {
      mapRef.current?.resize()
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  const routeFeatures = useMemo(() => {
    if (!trip) return []
    return [...trip.routes]
      .sort((a, b) => {
        // Draw selected / recommended on top
        if (a.id === selectedRouteId) return 1
        if (b.id === selectedRouteId) return -1
        if (a.is_recommended) return 1
        if (b.is_recommended) return -1
        return a.rank - b.rank
      })
      .map((route, i) => {
        const selected = route.id === selectedRouteId
        const color = route.is_recommended
          ? '#f4a338'
          : ALT_COLORS[i % ALT_COLORS.length]
        return {
          id: route.id,
          color,
          width: selected ? 6 : route.is_recommended ? 5 : 3.5,
          opacity: selected || route.is_recommended ? 0.95 : 0.4,
          data: {
            type: 'Feature' as const,
            properties: { id: route.id },
            geometry: { type: 'LineString' as const, coordinates: route.geometry },
          },
        }
      })
  }, [trip, selectedRouteId])

  const onMapClick = useCallback(
    (e: MapLayerMouseEvent) => {
      const feats = e.features
      if (!feats?.length || !selectedRoute) return
      const idx = feats[0].properties?.index
      if (idx == null) return
      const cp = selectedRoute.checkpoints.find((c) => c.index === Number(idx))
      if (cp) {
        setSelectedCheckpoint(cp)
        setPopupCp(cp)
      }
    },
    [selectedRoute, setSelectedCheckpoint],
  )

  useEffect(() => {
    setPopupCp(selectedCheckpoint)
  }, [selectedCheckpoint])

  const initialView = {
    longitude: -87.0,
    latitude: 42.1,
    zoom: 5.2,
  }

  return (
    <div className="route-map" ref={wrapRef}>
      <Map
        ref={mapRef}
        initialViewState={initialView}
        mapStyle={STYLE}
        style={{ width: '100%', height: '100%' }}
        interactiveLayerIds={['checkpoint-circles']}
        onClick={onMapClick}
        onLoad={() => {
          setMapError(null)
          setMapReady(true)
          fitRoute()
        }}
        onError={(e) => {
          const msg = e.error?.message ?? 'Map failed to load'
          console.error('[maplibre]', msg)
          // Worker errors prevent onLoad; surface them instead of spinning forever.
          if (/worker/i.test(msg)) {
            setMapError(
              'Map worker failed to load. Hard-refresh the page (Cmd+Shift+R). If it persists, restart `pnpm dev`.',
            )
          }
        }}
        attributionControl={{ compact: true }}
        cursor={selectedRoute ? 'pointer' : undefined}
      >
        <NavigationControl position="top-right" showCompass={false} />

        {mapReady && heatmap && (
          <HeatmapLayer
            heatmap={heatmap}
            hourIndex={hourIndex}
            metric={metric}
            playing={playing}
          />
        )}

        {mapReady &&
          routeFeatures.map((rc) => (
            <Source key={rc.id} id={`route-${rc.id}`} type="geojson" data={rc.data}>
              <Layer
                id={`route-casing-${rc.id}`}
                type="line"
                layout={{ 'line-join': 'round', 'line-cap': 'round' }}
                paint={{
                  'line-color': '#0a0e14',
                  'line-width': rc.width + 3,
                  'line-opacity': rc.opacity * 0.85,
                }}
              />
              <Layer
                id={`route-line-${rc.id}`}
                type="line"
                layout={{ 'line-join': 'round', 'line-cap': 'round' }}
                paint={{
                  'line-color': rc.color,
                  'line-width': rc.width,
                  'line-opacity': rc.opacity,
                  'line-blur': 0.3,
                }}
              />
            </Source>
          ))}

        {mapReady && selectedRoute && (
          <Source
            id="checkpoints"
            type="geojson"
            data={{
              type: 'FeatureCollection',
              features: (() => {
                const cps = selectedRoute.checkpoints
                // Dense routes: label every Nth + ends so ETAs stay glanceable
                const step = cps.length > 14 ? 3 : cps.length > 8 ? 2 : 1
                return cps.map((cp, i) => {
                  const eta = new Date(cp.eta_utc)
                  const etaLabel = eta.toLocaleTimeString(undefined, {
                    hour: 'numeric',
                    minute: '2-digit',
                  })
                  const showEta =
                    i === 0 ||
                    i === cps.length - 1 ||
                    i % step === 0 ||
                    activeCheckpointIndexes.has(cp.index) ||
                    selectedCheckpoint?.index === cp.index
                  return {
                    type: 'Feature' as const,
                    properties: {
                      index: cp.index,
                      band: cp.band,
                      color: colorForBand(cp.band),
                      active: activeCheckpointIndexes.has(cp.index) ? 1 : 0,
                      eta_label: showEta ? etaLabel : '',
                      eta_mi: showEta ? `${cp.distance_mi.toFixed(0)} mi` : '',
                    },
                    geometry: {
                      type: 'Point' as const,
                      coordinates: [cp.lon, cp.lat],
                    },
                  }
                })
              })(),
            }}
          >
            <Layer
              id="checkpoint-circles"
              type="circle"
              paint={{
                'circle-radius': [
                  'case',
                  ['==', ['get', 'active'], 1],
                  10,
                  ['==', ['get', 'index'], selectedCheckpoint?.index ?? -1],
                  9,
                  6,
                ],
                'circle-color': ['get', 'color'],
                'circle-stroke-width': [
                  'case',
                  ['==', ['get', 'active'], 1],
                  3,
                  2,
                ],
                'circle-stroke-color': [
                  'case',
                  ['==', ['get', 'active'], 1],
                  '#f4a338',
                  '#0a0e14',
                ],
                'circle-opacity': 0.95,
              }}
            />
            {/* Glanceable ETAs on the map (not only after click) */}
            <Layer
              id="checkpoint-eta-labels"
              type="symbol"
              filter={['!=', ['get', 'eta_label'], '']}
              layout={{
                'text-field': ['concat', ['get', 'eta_label'], '\n', ['get', 'eta_mi']],
                'text-size': 11,
                'text-font': ['Noto Sans Regular'],
                'text-offset': [0, 1.35],
                'text-anchor': 'top',
                'text-line-height': 1.15,
                'text-allow-overlap': true,
                'text-ignore-placement': true,
                'symbol-sort-key': ['get', 'index'],
              }}
              paint={{
                'text-color': '#f1f5f9',
                'text-halo-color': '#0a0e14',
                'text-halo-width': 1.6,
                'text-halo-blur': 0.2,
              }}
            />
          </Source>
        )}

        {trip && (
          <>
            <Marker longitude={trip.origin.lon} latitude={trip.origin.lat} anchor="center">
              <div className="map-pin map-pin--origin" title={trip.origin.label}>
                A
              </div>
            </Marker>
            <Marker
              longitude={trip.destination.lon}
              latitude={trip.destination.lat}
              anchor="center"
            >
              <div className="map-pin map-pin--dest" title={trip.destination.label}>
                B
              </div>
            </Marker>
          </>
        )}

        {truckPos && (
          <Marker longitude={truckPos.lon} latitude={truckPos.lat} anchor="center">
            <div
              className={`map-truck ${playing ? 'is-moving' : ''}`}
              title={
                hourIndex >= tripDurationH
                  ? `Arrived · +${hourIndex}h forecast`
                  : `+${hourIndex}h into trip · ${(truckPos.t * 100).toFixed(0)}% to destination`
              }
            >
              🚛
            </div>
          </Marker>
        )}

        {popupCp && (
          <Popup
            longitude={popupCp.lon}
            latitude={popupCp.lat}
            anchor="bottom"
            offset={16}
            closeOnClick={false}
            onClose={() => setPopupCp(null)}
            className="cp-popup"
          >
            <div className="cp-popup-body">
              <strong style={{ color: colorForBand(popupCp.band) }}>{popupCp.band}</strong>
              <span>
                #{popupCp.index} · {popupCp.distance_mi.toFixed(0)} mi
              </span>
              <span className="cp-popup-meta">
                {new Date(popupCp.eta_utc).toLocaleString()} · wind{' '}
                {popupCp.wind_mph.toFixed(0)} mph
              </span>
            </div>
          </Popup>
        )}
      </Map>

      {trip && (
        <div className="map-legend">
          <span className="legend-item">
            <i style={{ background: '#f4a338' }} /> Recommended
          </span>
          <span className="legend-item">
            <i style={{ background: '#38d4e0' }} /> Alternate
          </span>
          <span className="legend-item">
            <i style={{ background: '#22c55e' }} /> Low
          </span>
          <span className="legend-item">
            <i style={{ background: '#eab308' }} /> Mod
          </span>
          <span className="legend-item">
            <i style={{ background: '#f97316' }} /> High
          </span>
          <span className="legend-item">
            <i style={{ background: '#ef4444' }} /> Severe
          </span>
        </div>
      )}

      {heatmap && <HeatmapControls />}

      {!trip && (
        <div className="map-empty">
          <strong>Plan a trip to see routes</strong>
          <span>Origin, destination, departure, and load weight → safest corridor on the map.</span>
        </div>
      )}

      {trip && !mapReady && !mapError && (
        <div className="map-loading">
          <span className="map-spinner" />
          Loading map…
        </div>
      )}

      {mapError && (
        <div className="map-loading map-loading--error">
          <strong>Map couldn’t load</strong>
          <span>{mapError}</span>
          <small>Routes and risk scores in the sidebar are still valid.</small>
        </div>
      )}
    </div>
  )
}

import { useMemo } from 'react'
import { Layer, Source } from 'react-map-gl/maplibre'
import type { FeatureCollection } from 'geojson'
import type { HeatmapData } from '../../api/types'

interface Props {
  heatmap: HeatmapData
  hourIndex: number
  metric: 'risk' | 'wind' | 'rain' | 'snow'
  playing?: boolean
}

function normalize(value: number, metric: Props['metric']): number {
  if (metric === 'risk') return Math.min(1, value / 4)
  if (metric === 'wind') return Math.min(1, value / 45)
  if (metric === 'rain') return Math.min(1, value / 0.6)
  return Math.min(1, value / 2.0)
}

export function HeatmapLayer({ heatmap, hourIndex, metric, playing = false }: Props) {
  const frames = useMemo(() => {
    const values = heatmap.frames[metric]
    return heatmap.hours.map((_, hi) => {
      const fc: FeatureCollection = {
        type: 'FeatureCollection',
        features: heatmap.grid_points.map((pt, pi) => {
          const raw = values[hi]?.[pi] ?? 0
          const weight = normalize(raw, metric)
          // Skip near-zero samples so calm hours don't spray cyan "sky dots"
          if (weight < 0.05) return null
          return {
            type: 'Feature' as const,
            properties: { weight, raw },
            geometry: { type: 'Point' as const, coordinates: [pt.lon, pt.lat] },
          }
        }).filter(Boolean) as GeoJSON.Feature[],
      }
      return fc
    })
  }, [heatmap, metric])

  const frameIdx = Math.max(0, Math.min(Math.floor(hourIndex), frames.length - 1))
  const data = frames[frameIdx]

  return (
    <Source id="weather-heatmap" type="geojson" data={data}>
      <Layer
        id="weather-heatmap-layer"
        type="heatmap"
        paint={{
          'heatmap-weight': ['get', 'weight'],
          'heatmap-intensity': playing ? 1.5 : 1.2,
          'heatmap-radius': playing ? 52 : 42,
          'heatmap-opacity': playing ? 0.72 : 0.55,
          'heatmap-color': [
            'interpolate',
            ['linear'],
            ['heatmap-density'],
            0,
            'rgba(0,0,0,0)',
            0.2,
            'rgba(74, 222, 128, 0.35)',
            0.4,
            '#eab308',
            0.6,
            '#f97316',
            0.8,
            '#ef6461',
            1,
            '#7f1d1d',
          ],
        }}
      />
    </Source>
  )
}

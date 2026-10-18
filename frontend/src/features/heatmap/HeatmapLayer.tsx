import { useMemo } from 'react'
import { Layer, Source } from 'react-map-gl/maplibre'
import type { FeatureCollection, Feature } from 'geojson'
import type { HeatmapData } from '../../api/types'

interface Props {
  heatmap: HeatmapData
  hourIndex: number
  metric: 'risk' | 'wind' | 'rain' | 'snow'
  playing?: boolean
}

/** Map raw sample → heatmap weight 0–1. Risk Low still gets a floor so calm hours glow. */
function weightFor(raw: number, metric: Props['metric']): number {
  if (metric === 'risk') {
    // Bands 0–4; Low (0) uses a soft floor so the corridor is still visible
    return Math.min(1, Math.max(0.16, raw / 4))
  }
  if (metric === 'wind') return Math.min(1, raw / 40)
  if (metric === 'rain') return Math.min(1, raw / 0.5)
  return Math.min(1, raw / 1.5)
}

function includeSample(raw: number, metric: Props['metric']): boolean {
  // Risk always paints the corridor (calm = soft green).
  if (metric === 'risk') return true
  // Skip empty weather so we don't spray sky dots on calm frames
  if (metric === 'wind') return raw >= 4
  if (metric === 'rain') return raw >= 0.02
  return raw >= 0.05
}

export function HeatmapLayer({ heatmap, hourIndex, metric, playing = false }: Props) {
  const frames = useMemo(() => {
    const values = heatmap.frames[metric]
    return heatmap.hours.map((_, hi) => {
      const features: Feature[] = []
      for (let pi = 0; pi < heatmap.grid_points.length; pi++) {
        const pt = heatmap.grid_points[pi]
        const raw = values[hi]?.[pi] ?? 0
        if (!includeSample(raw, metric)) continue
        features.push({
          type: 'Feature',
          properties: { weight: weightFor(raw, metric), raw },
          geometry: { type: 'Point', coordinates: [pt.lon, pt.lat] },
        })
      }
      const fc: FeatureCollection = { type: 'FeatureCollection', features }
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
          'heatmap-intensity': playing ? 1.85 : 1.45,
          'heatmap-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            4,
            playing ? 28 : 22,
            7,
            playing ? 56 : 44,
            10,
            playing ? 80 : 64,
          ],
          'heatmap-opacity': playing ? 0.78 : 0.62,
          'heatmap-color': [
            'interpolate',
            ['linear'],
            ['heatmap-density'],
            0,
            'rgba(0,0,0,0)',
            0.15,
            'rgba(56, 212, 224, 0.25)',
            0.3,
            'rgba(74, 222, 128, 0.55)',
            0.45,
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

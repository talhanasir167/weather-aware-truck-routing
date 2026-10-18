/**
 * MapLibre + Vite: the default worker blob URL often fails in dev
 * ("Worker failed to load"). Point MapLibre at the packaged worker module.
 */
import { setWorkerUrl } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'

setWorkerUrl(workerUrl)

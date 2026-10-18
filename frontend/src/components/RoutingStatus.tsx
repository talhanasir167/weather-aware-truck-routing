import { useEffect, useState } from 'react'
import { getStatus } from '../api/client'
import type { ApiStatus } from '../api/types'

export function RoutingStatus() {
  const [status, setStatus] = useState<ApiStatus | null>(null)

  useEffect(() => {
    getStatus()
      .then(setStatus)
      .catch(() => setStatus(null))
  }, [])

  if (!status) return null

  return (
    <div
      className={`routing-status ${status.ors_configured ? 'ok' : 'warn'}`}
      title={
        status.ors_configured
          ? 'OpenRouteService driving-hgv is configured'
          : 'Add ORS_API_KEY to backend .env for truck-aware routing (free at openrouteservice.org)'
      }
    >
      <span className="routing-status__dot" />
      {status.ors_configured ? 'ORS truck routing' : 'OSRM fallback · set ORS_API_KEY'}
    </div>
  )
}

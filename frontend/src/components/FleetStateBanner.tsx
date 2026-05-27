import { api } from '../api/client'
import { usePolling } from '../hooks/usePolling'

export function FleetStateBanner() {
  const { data, error } = usePolling(api.getFleetState)

  if (error) return <div className="banner banner--error">Fleet state unavailable</div>
  if (!data) return <div className="banner">Loading fleet state…</div>

  return (
    <div className="banner">
      <span>Total: <strong>{data.total}</strong></span>
      <span className="status-idle">Idle: <strong>{data.idle}</strong></span>
      <span className="status-moving">Moving: <strong>{data.moving}</strong></span>
      <span className="status-charging">Charging: <strong>{data.charging}</strong></span>
      <span className="status-fault">Fault: <strong>{data.fault}</strong></span>
    </div>
  )
}

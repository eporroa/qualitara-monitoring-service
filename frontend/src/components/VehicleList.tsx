import { api } from '../api/client'
import { usePolling } from '../hooks/usePolling'
import type { VehicleStatus } from '../types'

const STATUS_LABEL: Record<VehicleStatus, string> = {
  idle: 'Idle',
  moving: 'Moving',
  charging: 'Charging',
  fault: 'Fault',
}

function BatteryBar({ pct }: { pct: number }) {
  const color = pct < 10 ? '#ef4444' : pct < 20 ? '#f97316' : '#22c55e'
  return (
    <span className="battery-bar" title={`${pct.toFixed(0)}%`}>
      <span style={{ width: `${pct}%`, backgroundColor: color }} />
    </span>
  )
}

export function VehicleList() {
  const { data: vehicles, error } = usePolling(api.getVehicles)

  if (error) return <p className="error">{error}</p>
  if (!vehicles) return <p>Loading vehicles…</p>

  return (
    <table className="vehicle-table">
      <thead>
        <tr>
          <th>Vehicle</th>
          <th>Status</th>
          <th>Battery</th>
          <th>Latest Anomaly</th>
        </tr>
      </thead>
      <tbody>
        {vehicles.map((v) => (
          <tr key={v.vehicle_id} className={v.current_status === 'fault' ? 'row-fault' : ''}>
            <td><strong>{v.vehicle_id}</strong></td>
            <td>
              <span className={`status-badge status-${v.current_status}`}>
                {STATUS_LABEL[v.current_status]}
              </span>
            </td>
            <td>
              <BatteryBar pct={v.current_battery_pct} />
              <span className="battery-pct">{v.current_battery_pct.toFixed(0)}%</span>
            </td>
            <td className="anomaly-cell">
              {v.latest_anomaly ? (
                <span className="anomaly-badge" title={v.latest_anomaly.detected_at}>
                  {v.latest_anomaly.anomaly_type}
                </span>
              ) : (
                <span className="no-anomaly">—</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

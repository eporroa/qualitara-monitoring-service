import { api } from '../api/client'
import { usePolling } from '../hooks/usePolling'

export function ZoneCounts() {
  const { data: zones, error } = usePolling(api.getZoneCounts)

  if (error) return <p className="error">{error}</p>
  if (!zones) return <p>Loading zones…</p>

  const sorted = [...zones].sort((a, b) => b.entry_count - a.entry_count)

  return (
    <div className="zone-grid">
      {sorted.map((z) => (
        <div key={z.zone_id} className="zone-card">
          <span className="zone-name">{z.zone_id.replace(/_/g, ' ')}</span>
          <span className="zone-count">{z.entry_count}</span>
        </div>
      ))}
    </div>
  )
}

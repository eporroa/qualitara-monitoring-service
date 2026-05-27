export type VehicleStatus = 'idle' | 'moving' | 'charging' | 'fault'

export interface Anomaly {
  id: number
  vehicle_id: string
  detected_at: string
  anomaly_type: string
  details: Record<string, unknown>
}

export interface Vehicle {
  vehicle_id: string
  current_status: VehicleStatus
  current_battery_pct: number
  updated_at: string | null
  latest_anomaly: Anomaly | null
}

export interface ZoneCount {
  zone_id: string
  entry_count: number
}

export interface FleetState {
  idle: number
  moving: number
  charging: number
  fault: number
  total: number
}

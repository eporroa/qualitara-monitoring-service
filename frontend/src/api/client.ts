import type { Anomaly, FleetState, Vehicle, ZoneCount } from '../types'

const BASE = '/api'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export const api = {
  getVehicles: () => get<Vehicle[]>('/vehicles'),
  getFleetState: () => get<FleetState>('/fleet/state'),
  getZoneCounts: () => get<ZoneCount[]>('/zones/counts'),
  getAnomalies: (vehicleId?: string) =>
    get<Anomaly[]>(vehicleId ? `/anomalies?vehicle_id=${vehicleId}` : '/anomalies'),
}

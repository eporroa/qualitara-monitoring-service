import { FleetStateBanner } from './components/FleetStateBanner'
import { VehicleList } from './components/VehicleList'
import { ZoneCounts } from './components/ZoneCounts'
import './index.css'

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Fleet Telemetry Monitor</h1>
        <FleetStateBanner />
      </header>
      <main className="app-body">
        <section className="panel panel-vehicles">
          <h2>Vehicles</h2>
          <VehicleList />
        </section>
        <section className="panel panel-zones">
          <h2>Zone Entry Counts</h2>
          <ZoneCounts />
        </section>
      </main>
    </div>
  )
}

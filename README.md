# Qualitara Fleet Telemetry Monitoring Service

A fleet monitoring system for 50 autonomous industrial vehicles emitting telemetry at 1 Hz. Built as a full-stack take-home assessment.

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI + SQLAlchemy + SQLite (WAL mode) |
| Frontend | React 19 + TypeScript + Vite |
| Persistence | SQLite with WAL mode (zero-setup, handles 50 veh × 1 Hz) |

## Requirements

- Python 3.11+
- Node 18+

## Running the backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

On first start, the app seeds 50 vehicles (`v-1` … `v-50`) and all 20 warehouse zones automatically.

## Running the frontend

```bash
cd frontend
npm install
npm run dev
# Dashboard at http://localhost:5173
```

The Vite dev server proxies `/api/*` to `http://localhost:8000`, so both services need to be running.

## API endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/telemetry` | Ingest a telemetry event |
| `GET` | `/vehicles` | All vehicles with status, battery, and latest anomaly |
| `POST` | `/vehicles/{id}/status` | Update vehicle status (fault triggers atomic mission cancel) |
| `GET` | `/fleet/state` | Aggregate per-status counts across all vehicles |
| `GET` | `/zones/counts` | Per-zone entry counts |
| `GET` | `/anomalies` | Recent anomalies; filter by `vehicle_id`, `from_time`, `to_time` |

### Example: send a telemetry event

```bash
curl -X POST http://localhost:8000/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "v-12",
    "timestamp": "2026-05-27T10:00:00Z",
    "lat": 37.41,
    "lon": -122.08,
    "battery_pct": 8,
    "speed_mps": 1.2,
    "status": "moving",
    "error_codes": ["E101"],
    "zone_entered": "charging_bay_1"
  }'
```

## Anomaly detection

Anomalies are detected inline on every `POST /telemetry`:

| Type | Condition |
|---|---|
| `battery_critical` | battery_pct < 10% |
| `battery_low` | battery_pct < 20% |
| `fault_status` | status == "fault" |
| `phantom_motion` | speed_mps > 0.5 while idle |
| `overspeed` | speed_mps > 5.0 m/s |
| `error_reported` | error_codes non-empty |

## Concurrency notes

- **Zone counts**: `UPDATE zones SET entry_count = entry_count + 1` — atomic under SQLite's serialized write model; no lost updates even with concurrent vehicle events
- **Fault transitions**: `BEGIN IMMEDIATE` transaction acquires the write lock before checking and modifying mission/vehicle state — prevents two concurrent fault events from double-creating maintenance records

## Docs

- [Architecture Decision Record](docs/adr.md) — key decisions, assumptions, scale-out plan, deliberate omissions

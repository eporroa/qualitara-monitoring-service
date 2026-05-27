# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`qualitara-monitoring-service` — fleet telemetry monitoring for 50 autonomous industrial vehicles (1 Hz). FastAPI + SQLite backend, React + Vite + TypeScript frontend.

## Commands

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload        # dev server on :8000
uvicorn app.main:app --reload --port 8001  # alternate port
```

Database file (`fleet.db`) is created on first run. Delete it to reset all state.

### Frontend

```bash
cd frontend
npm install
npm run dev          # dev server on :5173 (proxies /api → :8000)
npm run build        # production build
npm run lint
```

## Architecture

### Backend (`backend/app/`)

- **`main.py`** — FastAPI app, CORS (`localhost:5173`), lifespan startup that creates tables and seeds 50 vehicles + 20 zones if absent
- **`database.py`** — SQLAlchemy engine; WAL mode set via `event.listens_for(engine, "connect")`; `get_db()` session dependency
- **`models.py`** — ORM models: `Vehicle`, `Telemetry`, `Anomaly`, `Zone`, `Mission`, `MaintenanceRecord`
- **`schemas.py`** — Pydantic v2 schemas for all endpoints
- **`constants.py`** — `ZONES` (20 named zones), `VEHICLE_IDS` (v-1…v-50), `ANOMALY_RULES`
- **`routers/telemetry.py`** — ingestion: persist → upsert vehicle → detect anomalies → increment zone count
- **`routers/vehicles.py`** — list vehicles with latest anomaly; fault-transition with `BEGIN IMMEDIATE`
- **`routers/fleet.py`** — `GROUP BY current_status` aggregate
- **`routers/zones.py`** — ordered zone entry counts
- **`routers/anomalies.py`** — filterable anomaly log

### Frontend (`frontend/src/`)

- **`api/client.ts`** — typed `fetch` wrappers; no extra HTTP library
- **`hooks/usePolling.ts`** — generic poll hook; uses `useRef` on fetcher to avoid stale closures
- **`components/VehicleList.tsx`** — table of 50 vehicles, color-coded status badge, battery bar, latest anomaly
- **`components/ZoneCounts.tsx`** — zone cards sorted by count descending
- **`components/FleetStateBanner.tsx`** — header bar with per-status totals
- Vite proxy: `/api/*` → `http://localhost:8000` (strips `/api` prefix)

### Concurrency model

SQLite WAL mode allows concurrent reads alongside a single writer. Zone counts use `UPDATE zones SET entry_count = entry_count + 1` — atomic under SQLite's write serialization. Fault-status transitions use `db.execute(text("BEGIN IMMEDIATE"))` to hold the write lock across the read-check-write sequence (cancel missions + create maintenance record).

### Data model

| Table | Purpose |
|---|---|
| `vehicles` | Current state per vehicle (status, battery) |
| `telemetry` | Raw event log |
| `anomalies` | Detected anomalies with type + details JSON |
| `zones` | Zone entry counts (20 rows, seeded at startup) |
| `missions` | Active/cancelled missions per vehicle |
| `maintenance_records` | Created on fault transition |

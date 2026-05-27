# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`qualitara-monitoring-service` — fleet telemetry monitoring for 50 autonomous industrial vehicles. FastAPI + SQLite backend, React + Vite + TypeScript frontend.

## Commands

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload       # dev server on :8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev       # dev server on :5173
npm run build     # production build
npm run lint
```

## Architecture

### Backend (`backend/app/`)

- **`main.py`** — FastAPI app with CORS and lifespan startup (seeds 50 vehicles + 20 zones)
- **`database.py`** — SQLAlchemy engine with SQLite WAL mode; `get_db` session dependency
- **`models.py`** — ORM models: `Vehicle`, `Telemetry`, `Anomaly`, `Zone`, `Mission`, `MaintenanceRecord`
- **`schemas.py`** — Pydantic request/response schemas
- **`constants.py`** — `ZONES` list (20 named warehouse zones)
- **`routers/`** — one file per domain: `telemetry`, `vehicles`, `fleet`, `zones`, `anomalies`

### Frontend (`frontend/src/`)

- **`api/client.ts`** — typed fetch wrappers for all backend endpoints
- **`hooks/usePolling.ts`** — generic polling hook (3-second interval)
- **`components/`** — `VehicleList`, `ZoneCounts`, `FleetStateBanner`
- Vite proxy routes `/api/*` → `http://localhost:8000`

### Concurrency model

SQLite runs in WAL mode (`PRAGMA journal_mode=WAL`). Zone entry counts use a single atomic `UPDATE zones SET entry_count = entry_count + 1` — safe under SQLite's serialized writes. Fault-status transitions use `BEGIN IMMEDIATE` to prevent races on mission cancellation.

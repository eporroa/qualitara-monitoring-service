# Qualitara Fleet Telemetry Monitoring Service

A fleet monitoring system for 50 autonomous industrial vehicles emitting telemetry at 1 Hz.

## Stack

- **Backend**: FastAPI + SQLite (WAL mode) + SQLAlchemy
- **Frontend**: React + TypeScript + Vite

## Project Structure

```
qualitara-monitoring-service/
├── backend/       # FastAPI service
├── frontend/      # React + Vite SPA
└── docs/          # ADR and AI interaction log
```

## Docs

- [Architecture Decision Record](docs/adr.md)
- [AI Interaction Log](docs/ai-interaction-log.md)

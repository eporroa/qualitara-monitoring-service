# Architecture Decision Record — Fleet Telemetry Monitoring Service

## Decision 1: FastAPI + SQLite (WAL mode)

**FastAPI** was chosen over Django REST for speed of scaffolding and because its async-native design handles concurrent I/O without blocking threads. Pydantic validation and automatic OpenAPI docs come for free.

**SQLite with WAL mode** was chosen over Postgres because:
- Zero infrastructure setup — appropriate for a time-boxed take-home
- 50 vehicles × 1 Hz = 50 writes/sec, well within SQLite's throughput ceiling under WAL
- WAL mode (`PRAGMA journal_mode=WAL`) enables concurrent readers alongside the single writer, so dashboard polls never block telemetry ingestion
- SQLite's serialized write model is an asset here: zone entry counts increment with a single `UPDATE entry_count = entry_count + 1` — correct under concurrent writes without optimistic locking

If scale grew to thousands of vehicles or required horizontal API deployment, the migration path is: swap SQLite for Postgres, add a connection pool (asyncpg + SQLAlchemy async), and use Postgres advisory locks or `SELECT ... FOR UPDATE SKIP LOCKED` for the fault-transition pattern.

---

## Decision 2: 3-second polling (not WebSockets)

The dashboard polls every 3 seconds. Reasons:
- Fleet operations at 1 Hz don't require sub-second UI updates; 3s lag is operationally invisible
- Polling is stateless — no reconnect logic, no connection registry, no CORS complexity beyond standard headers
- WebSockets would require the server to push to all connected clients on each telemetry event, coupling the ingestion path to the UI delivery path. At 50 vehicles × 1 Hz, that's manageable, but adds a component (broadcast layer) with no benefit at this scale

If scale grew significantly (100+ concurrent operators, real-time alerts), WebSockets or SSE with a Redis pub/sub layer would be the right upgrade.

---

## Decision 3: Anomaly definition

The spec deliberately left "anomaly" open. I defined five types, each with a distinct operational signal:

| Type | Condition | Why it matters |
|---|---|---|
| `battery_critical` | battery_pct < 10 | Imminent shutdown risk |
| `battery_low` | battery_pct < 20 | Needs routing to charging |
| `fault_status` | status == "fault" | Hard operational stop |
| `phantom_motion` | speed_mps > 0.5 while `idle` | Sensor or control anomaly |
| `overspeed` | speed_mps > 5.0 m/s | Safety threshold breach |
| `error_reported` | error_codes non-empty | Any device-level fault code |

Thresholds are hardcoded constants, easy to make configurable without changing the detection logic.

---

## Unclear constraints and assumptions

- **Mission data model**: The spec mentions "active mission must be atomically cancelled" but defines no mission schema. I invented a minimal `missions` table (`vehicle_id`, `status`, `created_at`, `cancelled_at`). In production this would be driven by a mission-planning service.
- **Zone geometry**: Assumed the edge client correctly populates `zone_entered` — no server-side geometry validation performed.
- **Vehicle pre-seeding**: The spec says 50 vehicles but doesn't specify how they're registered. I seed `v-1` through `v-50` at startup if they don't exist; any unknown `vehicle_id` in a telemetry event is auto-registered.
- **Anomaly deduplication**: I emit a new anomaly record on every event that triggers a rule, which can produce many records for a sustained low-battery condition. A production system would deduplicate (e.g., suppress repeats within a window).

---

## What would change at significant scale

"Significantly" = 10,000 vehicles × 1 Hz = 10,000 writes/sec, 50+ concurrent dashboard operators.

- **Database**: Replace SQLite with Postgres + connection pooling. Use `SELECT ... FOR UPDATE` for fault transitions.
- **Ingestion**: Move to an async message queue (Kafka or SQS) to decouple ingestion throughput from DB write latency.
- **Anomaly detection**: Move out of the ingestion path into a stream-processing worker to avoid blocking writes.
- **Dashboard**: Replace polling with WebSocket push backed by Redis pub/sub.
- **Fleet state**: Cache the aggregate in Redis, invalidated on each telemetry write, rather than recomputing on every dashboard poll.

---

## Deliberate omissions

- **Authentication / authorization**: No auth layer — not in scope for a monitoring slice demo
- **Pagination UI**: API supports `limit`, but the dashboard renders all 50 vehicles in a scrollable table
- **Unit tests**: Omitted to stay within the 5-6 hour budget; the ADR and AI log are weighted equally per the spec
- **Zone geometry model**: Edge client is trusted as the source of truth for `zone_entered`
- **Anomaly deduplication / alerting**: No throttling of repeat anomalies, no notification system

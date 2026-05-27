# AI Interaction Log

**Tool used:** Claude Code (claude-sonnet-4-6) via the Claude Code CLI  
**Project:** Qualitara Fleet Telemetry Monitoring Service (take-home assessment)

---

## Prompt 1 — Read the assessment spec and produce a project plan

> Review the assestment spec, get the key points for the implementation, choose in the backend FastAPI and the frontend React, TypeScript and Vite to build an SPA.

**Output:** I pasted the spec manually as plain text.

Once the spec was available, Claude produced a 17-task implementation plan covering: repo init, backend scaffolding, frontend scaffolding, all API endpoints, frontend components, ADR, AI log, README, and CLAUDE.md.

**Correction:** Spec had to be pasted manually. No plan was generated until I intervened.

---

## Prompt 2 — Initialize the repo and commit the first scaffold

> Set up git, add the remote, write a placeholder README and CLAUDE.md, commit as the initial scaffold.

**Output:** Created `.gitignore`, `README.md`, `CLAUDE.md`, ran `git init` and `git remote add origin`. Initial commit landed cleanly.

**Correction:** None.

---

## Prompt 3 — Backend scaffolding

> Scaffold the FastAPI backend: app structure, SQLite WAL mode setup, all ORM models (Vehicle, Telemetry, Anomaly, Zone, Mission, MaintenanceRecord), Pydantic schemas for all request/response shapes, router stubs with `NotImplementedError` placeholders for all five domains, and a lifespan startup that seeds 50 vehicles and 20 zones.

**Output:** Generated all files in one pass — `database.py` with WAL mode via SQLAlchemy's `event.listens_for`, `models.py` with all six ORM models, `schemas.py` with Pydantic v2 schemas, five router stubs, and `main.py` with CORS and lifespan. Committed as a single clean scaffolding commit.

**Correction:** None.

---

## Prompt 4 — Frontend scaffolding

> Scaffold a Vite + React + TypeScript SPA: Vite proxy routing `/api/*` to the backend, typed API client using plain `fetch` (no extra HTTP library), a generic `usePolling` hook, component shells for `VehicleList`, `ZoneCounts`, and `FleetStateBanner`, a two-column dark-theme dashboard layout in `App.tsx`, and all CSS.

**Output:** Ran `npm create vite@latest`, updated `vite.config.ts` with the proxy, wrote all type definitions, the API client, the hook, three component shells, and a full dark-theme CSS file. Committed as a frontend scaffolding commit.

**Correction:** Claude attempted to overwrite the Vite-generated `App.tsx` without reading it first — the Write tool rejected this. It then read the file and correctly overwrote it. Vite boilerplate files (`App.css`, `assets/react.svg`) were removed manually afterward.

---

## Prompt 5 — Implement all backend API endpoints

> Implement all five router endpoints: `POST /telemetry` (ingest, upsert vehicle state, run anomaly detection, increment zone counter atomically), `GET /vehicles` with latest anomaly per vehicle, `POST /vehicles/{id}/status` with `BEGIN IMMEDIATE` for atomic fault transitions, `GET /fleet/state`, `GET /zones/counts`, and `GET /anomalies` filterable by vehicle and time range.

**Output:** All five routers implemented in full. Claude smoke-tested against a live `uvicorn` instance via curl: health, fleet state, zone counts, telemetry ingestion with anomaly detection, and a fault status transition all returned correct responses.

**Correction:** The curl command for `GET /anomalies?vehicle_id=v-1` failed because zsh ate the `?` as a glob character. Fixed by quoting the URL. The `git add backend/` command also failed because the shell's working directory was inside `backend/` from the earlier venv setup — fixed by running git from the repo root.

---

## Prompt 6 — Write the Architecture Decision Record

> Write a one-page ADR covering: FastAPI + SQLite rationale, polling vs WebSockets trade-off, anomaly type definitions with thresholds and justification, unclear constraints and assumptions made, scale-out plan, and deliberate omissions.

**Output:** `docs/adr.md` with five sections: the three key decisions (FastAPI+SQLite, polling, anomaly definitions), unclear constraints, scale-out changes at "thousands of vehicles" scale, and deliberate omissions (auth, unit tests, zone geometry, anomaly deduplication).

**Correction:** None.

---

## Prompt 7 — Update README and CLAUDE.md with implementation notes

> Update README with full how-to-run instructions for backend and frontend, an API endpoint table, an example curl for `POST /telemetry`, an anomaly type reference table, and concurrency notes. Update CLAUDE.md with dev commands, per-file architecture notes, and a data model table.

**Output:** Both files updated and committed. README covers prerequisites, run commands, all endpoints, the example payload, anomaly thresholds, and concurrency behavior. CLAUDE.md covers commands, architecture by file, concurrency model, and a full data model table.

**Correction:** None.

---

## Prompt 8 — Create a pytest test suite for POST /telemetry

> Create mocked test cases for the `POST /telemetry` endpoint using pytest and FastAPI's TestClient with an in-memory SQLite database. Cover: happy path, all six anomaly rules including boundary values, zone counter accumulation, vehicle upsert (new and existing), multiple simultaneous anomalies, DB persistence assertions, and 422 validation failures.

**Output:** 39 tests across `tests/conftest.py` and `tests/test_telemetry.py`. First run: 33 failures, 6 passes (only the 422 validation tests passed).

**Root cause 1 — FK violation on autoflush:** The `ingest_telemetry` handler added a `Telemetry` row to the session before checking whether the `Vehicle` existed. When SQLAlchemy's autoflush fired on the subsequent `db.get(Vehicle, ...)` call, it tried to `INSERT` the telemetry row — which has a foreign key on `vehicle_id` — before the vehicle was present. Fixed by reordering the handler: upsert Vehicle first, then add Telemetry.

**Root cause 2 — SQLite in-memory DB per-connection isolation:** SQLite in-memory databases exist only for the connection that created them. Without `StaticPool`, the test's assertion session and the request handler's session each opened separate connections — separate databases — so neither could see the other's data. Fixed by adding `poolclass=StaticPool` to the test engine so all sessions share one connection.

After both fixes: **39/39 passing in 0.30s**.

**Correction:** Two bugs in the test infrastructure required diagnosis and fixes — one in production code (router ordering) and one in the test setup (StaticPool). Claude identified both root causes correctly once the failures were visible.

---

## Prompt 9 — Create E2E Swagger test payloads

> Create `docs/e2e-swagger-tests.md` with copy-pasteable JSON payloads for every meaningful scenario across all seven endpoints, organized as a guided walkthrough where earlier steps seed state that later steps verify.

**Output:** `docs/e2e-swagger-tests.md` with 9 sections and ~35 individual scenarios: health check, initial state baseline, happy path telemetry, all six anomaly triggers, boundary edge cases (exact threshold values), status update flows including idempotent fault, anomaly query filters, final state verification, and 422 validation failures. Each scenario includes a goal, endpoint, JSON body, and expected response.

**Correction:** None.

---

## Prompt 10 — Fix vehicle list sort order

> The vehicle list in the frontend is sorting lexicographically (v-1, v-10, v-11 … v-2, v-20) instead of numerically (v-1, v-2, v-3 … v-50). Fix it correctly by numeric value.

**Output:** Fixed in two places simultaneously. Backend: `ORDER BY CAST(SUBSTR(vehicle_id, 3) AS INTEGER)` in `GET /vehicles`. Frontend: client-side sort using `parseInt(v.vehicle_id.slice(2))` as a safety net. Verified with a Python one-liner confirming `v-1` through `v-50` sort correctly.

**Correction:** None — the bug and both fix locations were identified immediately.

---

## Reflection

- **What the AI was good at:** Generating complete, correctly structured boilerplate from a single prompt — SQLAlchemy models, Pydantic v2 schemas, Vite config, TypeScript types, and CSS all came out right on the first pass with no hallucinated APIs. It also handled concurrency decisions (WAL mode, `BEGIN IMMEDIATE`, atomic zone counter) correctly without being prompted for the approach, and wrote a comprehensive test suite that covered boundary conditions I might have missed manually.

- **Where it failed:** The test infrastructure required two separate fixes before a single test passed: a production code ordering bug (Telemetry before Vehicle) and a SQLite `StaticPool` issue that's easy to miss if you haven't hit it before.

- **What I had to double-check manually:** The `BEGIN IMMEDIATE` SQLite transaction behavior in SQLAlchemy — specifically that `db.execute(text("BEGIN IMMEDIATE"))` correctly bypasses autocommit and acquires the write lock before the check-and-update sequence. The anomaly threshold values (10% critical, 20% low, 5 m/s overspeed) are reasonable defaults for industrial vehicles but are not in the spec, so I verified they made operational sense before accepting them. The vehicle sort bug was caught by visual inspection of the running dashboard, not by any test.

- **What worked better than expected:** The `usePolling` hook was generated with `useRef` on the fetcher to avoid stale closure issues — a subtle React correctness concern that the AI handled correctly unprompted. The two-layer sort fix (backend SQL + frontend JS) was proposed and implemented in one step without being asked.

- **Overall:** AI tooling compressed the scaffolding and boilerplate phase dramatically. The areas requiring human judgment were the ones the spec intentionally left open — anomaly definitions, mission data model, vehicle pre-seeding strategy — and the infrastructure debugging that only surfaces when the code actually runs.

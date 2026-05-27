# E2E Swagger Test Payloads

Interactive end-to-end tests for the Fleet Telemetry Monitoring Service API.
Run these in order — earlier steps seed state that later steps verify.

## Prerequisites

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** in your browser.

On first startup the app automatically seeds **50 vehicles** (`v-1` … `v-50`) and all **20 warehouse zones** with `entry_count = 0`.

---

## 1. Health Check

**Goal:** Confirm the server is up before running anything else.

`GET /health`

**Expected:** `200 OK`
```json
{ "status": "ok" }
```

---

## 2. Read Initial State

Run these before sending any telemetry so you have a baseline to compare against.

### 2a. Fleet state

`GET /fleet/state`

**Expected:** All 50 vehicles are `idle`, nothing else.
```json
{ "idle": 50, "moving": 0, "charging": 0, "fault": 0, "total": 50 }
```

### 2b. Zone counts

`GET /zones/counts`

**Expected:** 20 zones, every `entry_count` is `0`.

### 2c. Vehicle list

`GET /vehicles`

**Expected:** Array of 50 vehicles, all with `current_status: "idle"` and `latest_anomaly: null`.

---

## 3. POST /telemetry — Happy Path (No Anomalies)

### 3a. Normal moving vehicle

**Goal:** Ingest a clean telemetry event — no zone, no anomalies.

`POST /telemetry`
```json
{
  "vehicle_id": "v-1",
  "timestamp": "2026-05-27T10:00:00Z",
  "lat": 37.4100,
  "lon": -122.0800,
  "battery_pct": 75,
  "speed_mps": 1.2,
  "status": "moving",
  "error_codes": [],
  "zone_entered": null
}
```

**Expected:** `201 Created`
```json
{
  "id": 1,
  "vehicle_id": "v-1",
  "timestamp": "2026-05-27T10:00:00",
  "anomalies_detected": []
}
```

---

### 3b. Vehicle entering a zone

**Goal:** Confirm that `zone_entered` increments the zone counter.

`POST /telemetry`
```json
{
  "vehicle_id": "v-2",
  "timestamp": "2026-05-27T10:00:01Z",
  "lat": 37.4150,
  "lon": -122.0820,
  "battery_pct": 68,
  "speed_mps": 0.8,
  "status": "moving",
  "error_codes": [],
  "zone_entered": "charging_bay_1"
}
```

**Expected:** `201 Created`, `anomalies_detected: []`

**Verify:** `GET /zones/counts` → `charging_bay_1` should now have `entry_count: 1`.

---

### 3c. Charging vehicle entering a second zone

**Goal:** Charging status with a zone entry — verify both state update and counter.

`POST /telemetry`
```json
{
  "vehicle_id": "v-3",
  "timestamp": "2026-05-27T10:00:02Z",
  "lat": 37.4200,
  "lon": -122.0840,
  "battery_pct": 42,
  "speed_mps": 0.0,
  "status": "charging",
  "error_codes": [],
  "zone_entered": "charging_bay_2"
}
```

**Expected:** `201 Created`, `anomalies_detected: []`

**Verify:** `GET /vehicles` → `v-3` should show `current_status: "charging"`, `current_battery_pct: 42`.

---

### 3d. Idle vehicle, zero speed

**Goal:** Idle + zero speed produces no phantom_motion anomaly.

`POST /telemetry`
```json
{
  "vehicle_id": "v-4",
  "timestamp": "2026-05-27T10:00:03Z",
  "lat": 37.4050,
  "lon": -122.0760,
  "battery_pct": 91,
  "speed_mps": 0.0,
  "status": "idle",
  "error_codes": [],
  "zone_entered": null
}
```

**Expected:** `201 Created`, `anomalies_detected: []`

---

## 4. POST /telemetry — Anomaly Triggers

### 4a. battery_critical (battery < 10%)

**Goal:** Trip the `battery_critical` anomaly rule.

`POST /telemetry`
```json
{
  "vehicle_id": "v-5",
  "timestamp": "2026-05-27T10:01:00Z",
  "lat": 37.4110,
  "lon": -122.0810,
  "battery_pct": 5,
  "speed_mps": 0.5,
  "status": "moving",
  "error_codes": [],
  "zone_entered": null
}
```

**Expected:** `201 Created`
```json
{ "anomalies_detected": ["battery_critical"] }
```

**Verify:** `GET /anomalies?vehicle_id=v-5` → one record with `anomaly_type: "battery_critical"`.

---

### 4b. battery_low (10% ≤ battery < 20%)

**Goal:** Trip `battery_low` without triggering `battery_critical`.

`POST /telemetry`
```json
{
  "vehicle_id": "v-6",
  "timestamp": "2026-05-27T10:01:01Z",
  "lat": 37.4120,
  "lon": -122.0812,
  "battery_pct": 15,
  "speed_mps": 1.0,
  "status": "moving",
  "error_codes": [],
  "zone_entered": null
}
```

**Expected:** `201 Created`
```json
{ "anomalies_detected": ["battery_low"] }
```

---

### 4c. fault_status (status == "fault")

**Goal:** A fault status event always generates a `fault_status` anomaly.

`POST /telemetry`
```json
{
  "vehicle_id": "v-7",
  "timestamp": "2026-05-27T10:01:02Z",
  "lat": 37.4130,
  "lon": -122.0814,
  "battery_pct": 50,
  "speed_mps": 0.0,
  "status": "fault",
  "error_codes": [],
  "zone_entered": null
}
```

**Expected:** `201 Created`
```json
{ "anomalies_detected": ["fault_status"] }
```

---

### 4d. phantom_motion (status == "idle" and speed > 0.5 m/s)

**Goal:** A vehicle reporting motion while idle triggers `phantom_motion`.

`POST /telemetry`
```json
{
  "vehicle_id": "v-8",
  "timestamp": "2026-05-27T10:01:03Z",
  "lat": 37.4140,
  "lon": -122.0816,
  "battery_pct": 80,
  "speed_mps": 2.0,
  "status": "idle",
  "error_codes": [],
  "zone_entered": null
}
```

**Expected:** `201 Created`
```json
{ "anomalies_detected": ["phantom_motion"] }
```

---

### 4e. overspeed (speed > 5.0 m/s)

**Goal:** Speed above the 5 m/s safety threshold triggers `overspeed`.

`POST /telemetry`
```json
{
  "vehicle_id": "v-9",
  "timestamp": "2026-05-27T10:01:04Z",
  "lat": 37.4150,
  "lon": -122.0818,
  "battery_pct": 70,
  "speed_mps": 6.5,
  "status": "moving",
  "error_codes": [],
  "zone_entered": null
}
```

**Expected:** `201 Created`
```json
{ "anomalies_detected": ["overspeed"] }
```

---

### 4f. error_reported (non-empty error_codes)

**Goal:** Any device-level error code triggers `error_reported`.

`POST /telemetry`
```json
{
  "vehicle_id": "v-10",
  "timestamp": "2026-05-27T10:01:05Z",
  "lat": 37.4160,
  "lon": -122.0820,
  "battery_pct": 65,
  "speed_mps": 1.1,
  "status": "moving",
  "error_codes": ["E101", "SENSOR_FAIL"],
  "zone_entered": null
}
```

**Expected:** `201 Created`
```json
{ "anomalies_detected": ["error_reported"] }
```

---

### 4g. Multiple anomalies simultaneously

**Goal:** Confirm all fired rules are returned in a single response.
Battery 5% + fault status + error codes → three anomalies at once.

`POST /telemetry`
```json
{
  "vehicle_id": "v-11",
  "timestamp": "2026-05-27T10:01:06Z",
  "lat": 37.4170,
  "lon": -122.0822,
  "battery_pct": 5,
  "speed_mps": 0.0,
  "status": "fault",
  "error_codes": ["CRITICAL_FAILURE"],
  "zone_entered": null
}
```

**Expected:** `201 Created`
```json
{ "anomalies_detected": ["battery_critical", "fault_status", "error_reported"] }
```

---

## 5. POST /telemetry — Boundary / Edge Cases

### 5a. Battery exactly at 20 — no anomaly

`POST /telemetry`
```json
{
  "vehicle_id": "v-12",
  "timestamp": "2026-05-27T10:02:00Z",
  "lat": 37.4100,
  "lon": -122.0800,
  "battery_pct": 20,
  "speed_mps": 1.0,
  "status": "moving",
  "error_codes": [],
  "zone_entered": null
}
```

**Expected:** `anomalies_detected: []` — 20% is the boundary, not below it.

---

### 5b. Battery exactly at 10 — battery_low, not battery_critical

`POST /telemetry`
```json
{
  "vehicle_id": "v-13",
  "timestamp": "2026-05-27T10:02:01Z",
  "lat": 37.4101,
  "lon": -122.0801,
  "battery_pct": 10,
  "speed_mps": 1.0,
  "status": "moving",
  "error_codes": [],
  "zone_entered": null
}
```

**Expected:** `anomalies_detected: ["battery_low"]` — 10% is `< 20` but not `< 10`.

---

### 5c. Speed exactly at 5.0 m/s — no overspeed

`POST /telemetry`
```json
{
  "vehicle_id": "v-14",
  "timestamp": "2026-05-27T10:02:02Z",
  "lat": 37.4102,
  "lon": -122.0802,
  "battery_pct": 60,
  "speed_mps": 5.0,
  "status": "moving",
  "error_codes": [],
  "zone_entered": null
}
```

**Expected:** `anomalies_detected: []` — rule fires at `> 5.0`, not `>= 5.0`.

---

### 5d. Idle with speed exactly 0.5 — no phantom_motion

`POST /telemetry`
```json
{
  "vehicle_id": "v-15",
  "timestamp": "2026-05-27T10:02:03Z",
  "lat": 37.4103,
  "lon": -122.0803,
  "battery_pct": 85,
  "speed_mps": 0.5,
  "status": "idle",
  "error_codes": [],
  "zone_entered": null
}
```

**Expected:** `anomalies_detected: []` — rule fires at `> 0.5`, not `>= 0.5`.

---

### 5e. Zone entered that doesn't exist in the warehouse

**Goal:** Unknown zone IDs are silently ignored — request still succeeds.

`POST /telemetry`
```json
{
  "vehicle_id": "v-16",
  "timestamp": "2026-05-27T10:02:04Z",
  "lat": 37.4104,
  "lon": -122.0804,
  "battery_pct": 72,
  "speed_mps": 1.3,
  "status": "moving",
  "error_codes": [],
  "zone_entered": "nonexistent_zone"
}
```

**Expected:** `201 Created`, `anomalies_detected: []` — UPDATE affects 0 rows, no error.

---

### 5f. Same vehicle entering the same zone twice

**Goal:** Zone counter accumulates across multiple events.

Send this payload **twice** (identical):

`POST /telemetry`
```json
{
  "vehicle_id": "v-2",
  "timestamp": "2026-05-27T10:02:05Z",
  "lat": 37.4150,
  "lon": -122.0820,
  "battery_pct": 65,
  "speed_mps": 0.9,
  "status": "moving",
  "error_codes": [],
  "zone_entered": "charging_bay_1"
}
```

**Expected after second POST:** `GET /zones/counts` → `charging_bay_1` = `3`
(1 from step 3b + 2 from this step).

---

## 6. POST /vehicles/{vehicle_id}/status — Status Updates

### 6a. Transition to fault (atomic mission cancel)

**Goal:** Fault transition atomically cancels active missions and creates a maintenance record.

`POST /vehicles/v-5/status`
```json
{ "new_status": "fault" }
```

**Expected:** `200 OK` with `current_status: "fault"`

**Verify:** `GET /vehicles` → `v-5` shows `current_status: "fault"`.

---

### 6b. Transition to charging

`POST /vehicles/v-3/status`
```json
{ "new_status": "charging" }
```

**Expected:** `200 OK` with `current_status: "charging"`

---

### 6c. Transition to idle

`POST /vehicles/v-4/status`
```json
{ "new_status": "idle" }
```

**Expected:** `200 OK` with `current_status: "idle"`

---

### 6d. Fault transition on already-faulted vehicle (idempotent)

**Goal:** Sending fault to a vehicle already in fault should not double-create records.

`POST /vehicles/v-5/status`
```json
{ "new_status": "fault" }
```

**Expected:** `200 OK` — no duplicate maintenance record created.

---

### 6e. Unknown vehicle — 404

`POST /vehicles/v-999/status`
```json
{ "new_status": "idle" }
```

**Expected:** `404 Not Found`
```json
{ "detail": "Vehicle not found" }
```

---

## 7. GET /anomalies — Query Filters

### 7a. No filters — all recent anomalies

`GET /anomalies`

**Expected:** Up to 200 records, newest first. Should include anomalies from steps 4a–4g.

---

### 7b. Filter by vehicle_id

`GET /anomalies?vehicle_id=v-11`

**Expected:** Only anomalies for `v-11` (`battery_critical`, `fault_status`, `error_reported`).

---

### 7c. Filter by time range

`GET /anomalies?from_time=2026-05-27T10:00:00Z&to_time=2026-05-27T10:01:59Z`

**Expected:** Anomalies detected within that window only.

---

### 7d. Combined: vehicle + time range

`GET /anomalies?vehicle_id=v-5&from_time=2026-05-27T10:00:00Z`

**Expected:** Only `v-5` anomalies from that time forward.

---

## 8. Read Final Fleet State

After running all scenarios above, verify the fleet state reflects the changes.

`GET /fleet/state`

**Expected:** Several vehicles moved out of `idle` (moving, charging, fault) — total always = 50.

`GET /zones/counts`

**Expected:** `charging_bay_1` ≥ 3, `charging_bay_2` = 1, all others = 0.

---

## 9. Validation Failures — 422 Responses

These should all return `422 Unprocessable Entity`.

### 9a. Invalid status value

`POST /telemetry`
```json
{
  "vehicle_id": "v-1",
  "timestamp": "2026-05-27T10:00:00Z",
  "lat": 37.41,
  "lon": -122.08,
  "battery_pct": 75,
  "speed_mps": 1.2,
  "status": "driving",
  "error_codes": [],
  "zone_entered": null
}
```

**Expected:** `422` — `status` must match `idle | moving | charging | fault`.

---

### 9b. Battery above 100

`POST /telemetry`
```json
{
  "vehicle_id": "v-1",
  "timestamp": "2026-05-27T10:00:00Z",
  "lat": 37.41,
  "lon": -122.08,
  "battery_pct": 150,
  "speed_mps": 1.2,
  "status": "moving",
  "error_codes": [],
  "zone_entered": null
}
```

**Expected:** `422` — `battery_pct` must be ≤ 100.

---

### 9c. Negative speed

`POST /telemetry`
```json
{
  "vehicle_id": "v-1",
  "timestamp": "2026-05-27T10:00:00Z",
  "lat": 37.41,
  "lon": -122.08,
  "battery_pct": 75,
  "speed_mps": -1.0,
  "status": "moving",
  "error_codes": [],
  "zone_entered": null
}
```

**Expected:** `422` — `speed_mps` must be ≥ 0.

---

### 9d. Missing required field

`POST /telemetry`
```json
{
  "timestamp": "2026-05-27T10:00:00Z",
  "lat": 37.41,
  "lon": -122.08,
  "battery_pct": 75,
  "speed_mps": 1.2,
  "status": "moving",
  "error_codes": []
}
```

**Expected:** `422` — `vehicle_id` is required.

---

### 9e. Invalid status update value

`POST /vehicles/v-1/status`
```json
{ "new_status": "parked" }
```

**Expected:** `422` — `new_status` must match `idle | moving | charging | fault`.

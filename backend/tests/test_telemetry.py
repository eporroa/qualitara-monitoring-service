"""
Tests for POST /telemetry

Covers:
  - Happy path persistence (telemetry record, vehicle upsert)
  - All six anomaly detection rules
  - Zone entry counter increment
  - Multiple simultaneous anomalies
  - Edge cases at rule boundaries
  - Input validation (422 responses)
"""

import pytest

from app.models import Anomaly, Telemetry, Vehicle, Zone

TIMESTAMP = "2026-05-27T10:00:00Z"

BASE = {
    "vehicle_id": "v-1",
    "timestamp": TIMESTAMP,
    "lat": 37.41,
    "lon": -122.08,
    "battery_pct": 75,
    "speed_mps": 1.2,
    "status": "moving",
    "error_codes": [],
    "zone_entered": None,
}


def post(client, overrides: dict):
    return client.post("/telemetry", json={**BASE, **overrides})


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_normal_event_returns_201(client):
    res = post(client, {})
    assert res.status_code == 201


def test_normal_event_returns_telemetry_id(client):
    res = post(client, {})
    body = res.json()
    assert "id" in body
    assert body["id"] > 0


def test_normal_event_no_anomalies_detected(client):
    res = post(client, {})
    assert res.json()["anomalies_detected"] == []


def test_telemetry_record_is_persisted(client, db_session):
    post(client, {"vehicle_id": "v-99", "lat": 10.0, "lon": 20.0, "speed_mps": 2.5})
    row = db_session.query(Telemetry).filter_by(vehicle_id="v-99").first()
    assert row is not None
    assert row.lat == 10.0
    assert row.lon == 20.0
    assert row.speed_mps == 2.5


def test_new_vehicle_is_auto_registered(client, db_session):
    post(client, {"vehicle_id": "v-unknown"})
    v = db_session.query(Vehicle).filter_by(vehicle_id="v-unknown").first()
    assert v is not None


def test_existing_vehicle_state_is_updated(client, db_session):
    db_session.add(Vehicle(vehicle_id="v-5", current_status="idle", current_battery_pct=90.0))
    db_session.commit()

    post(client, {"vehicle_id": "v-5", "status": "charging", "battery_pct": 55.0})

    db_session.expire_all()
    v = db_session.query(Vehicle).filter_by(vehicle_id="v-5").first()
    assert v.current_status == "charging"
    assert v.current_battery_pct == 55.0


# ---------------------------------------------------------------------------
# Zone entry counter
# ---------------------------------------------------------------------------

def test_zone_entry_increments_counter(client, db_session):
    post(client, {"zone_entered": "charging_bay_1"})
    db_session.expire_all()
    zone = db_session.query(Zone).filter_by(zone_id="charging_bay_1").first()
    assert zone.entry_count == 1


def test_zone_entry_accumulates_across_events(client, db_session):
    post(client, {"zone_entered": "aisle_a"})
    post(client, {"zone_entered": "aisle_a"})
    post(client, {"zone_entered": "aisle_a"})
    db_session.expire_all()
    zone = db_session.query(Zone).filter_by(zone_id="aisle_a").first()
    assert zone.entry_count == 3


def test_null_zone_entered_does_not_change_counts(client, db_session):
    post(client, {"zone_entered": None})
    db_session.expire_all()
    total = sum(z.entry_count for z in db_session.query(Zone).all())
    assert total == 0


def test_unknown_zone_id_is_silently_ignored(client, db_session):
    # No zone row to update — the UPDATE affects 0 rows, not an error
    res = post(client, {"zone_entered": "nonexistent_zone"})
    assert res.status_code == 201


# ---------------------------------------------------------------------------
# Anomaly: battery_critical  (battery_pct < 10)
# ---------------------------------------------------------------------------

def test_battery_critical_detected_below_10(client):
    res = post(client, {"battery_pct": 9})
    assert "battery_critical" in res.json()["anomalies_detected"]


def test_battery_critical_detected_at_boundary_9(client):
    res = post(client, {"battery_pct": 9.9})
    assert "battery_critical" in res.json()["anomalies_detected"]


def test_battery_critical_not_triggered_at_10(client):
    # battery_pct == 10 is NOT < 10 → no critical, but < 20 → battery_low
    res = post(client, {"battery_pct": 10})
    assert "battery_critical" not in res.json()["anomalies_detected"]


def test_battery_critical_suppresses_battery_low(client):
    # elif logic: critical fires, low must NOT also fire
    anomalies = post(client, {"battery_pct": 5}).json()["anomalies_detected"]
    assert "battery_critical" in anomalies
    assert "battery_low" not in anomalies


def test_battery_critical_persisted_to_db(client, db_session):
    post(client, {"vehicle_id": "v-1", "battery_pct": 5})
    row = db_session.query(Anomaly).filter_by(
        vehicle_id="v-1", anomaly_type="battery_critical"
    ).first()
    assert row is not None


# ---------------------------------------------------------------------------
# Anomaly: battery_low  (10 <= battery_pct < 20)
# ---------------------------------------------------------------------------

def test_battery_low_detected_between_10_and_20(client):
    res = post(client, {"battery_pct": 15})
    assert "battery_low" in res.json()["anomalies_detected"]


def test_battery_low_detected_at_boundary_10(client):
    res = post(client, {"battery_pct": 10})
    assert "battery_low" in res.json()["anomalies_detected"]


def test_battery_low_not_triggered_at_20(client):
    res = post(client, {"battery_pct": 20})
    assert "battery_low" not in res.json()["anomalies_detected"]


def test_no_battery_anomaly_above_20(client):
    anomalies = post(client, {"battery_pct": 75}).json()["anomalies_detected"]
    assert "battery_low" not in anomalies
    assert "battery_critical" not in anomalies


# ---------------------------------------------------------------------------
# Anomaly: fault_status  (status == "fault")
# ---------------------------------------------------------------------------

def test_fault_status_detected(client):
    res = post(client, {"status": "fault"})
    assert "fault_status" in res.json()["anomalies_detected"]


def test_fault_status_not_triggered_for_other_statuses(client):
    for status in ("idle", "moving", "charging"):
        anomalies = post(client, {"status": status}).json()["anomalies_detected"]
        assert "fault_status" not in anomalies, f"unexpected fault_status for status={status}"


# ---------------------------------------------------------------------------
# Anomaly: phantom_motion  (status == "idle" and speed_mps > 0.5)
# ---------------------------------------------------------------------------

def test_phantom_motion_detected(client):
    res = post(client, {"status": "idle", "speed_mps": 1.0})
    assert "phantom_motion" in res.json()["anomalies_detected"]


def test_phantom_motion_not_triggered_at_threshold(client):
    # speed_mps == 0.5 is NOT > 0.5
    res = post(client, {"status": "idle", "speed_mps": 0.5})
    assert "phantom_motion" not in res.json()["anomalies_detected"]


def test_phantom_motion_not_triggered_when_moving(client):
    # High speed while moving is legitimate — no phantom_motion
    res = post(client, {"status": "moving", "speed_mps": 2.0})
    assert "phantom_motion" not in res.json()["anomalies_detected"]


# ---------------------------------------------------------------------------
# Anomaly: overspeed  (speed_mps > 5.0)
# ---------------------------------------------------------------------------

def test_overspeed_detected_above_5(client):
    res = post(client, {"speed_mps": 5.1})
    assert "overspeed" in res.json()["anomalies_detected"]


def test_overspeed_not_triggered_at_exactly_5(client):
    res = post(client, {"speed_mps": 5.0})
    assert "overspeed" not in res.json()["anomalies_detected"]


def test_overspeed_not_triggered_below_5(client):
    res = post(client, {"speed_mps": 3.0})
    assert "overspeed" not in res.json()["anomalies_detected"]


# ---------------------------------------------------------------------------
# Anomaly: error_reported  (error_codes non-empty)
# ---------------------------------------------------------------------------

def test_error_reported_with_single_code(client):
    res = post(client, {"error_codes": ["E101"]})
    assert "error_reported" in res.json()["anomalies_detected"]


def test_error_reported_with_multiple_codes(client):
    res = post(client, {"error_codes": ["E101", "E202", "E303"]})
    assert "error_reported" in res.json()["anomalies_detected"]


def test_no_error_reported_for_empty_list(client):
    res = post(client, {"error_codes": []})
    assert "error_reported" not in res.json()["anomalies_detected"]


# ---------------------------------------------------------------------------
# Multiple simultaneous anomalies
# ---------------------------------------------------------------------------

def test_multiple_anomalies_at_once(client):
    # battery_critical + fault_status + error_reported all fire together
    anomalies = post(client, {
        "battery_pct": 5,
        "status": "fault",
        "error_codes": ["CRITICAL"],
    }).json()["anomalies_detected"]

    assert "battery_critical" in anomalies
    assert "fault_status" in anomalies
    assert "error_reported" in anomalies


def test_overspeed_and_fault_status_together(client):
    anomalies = post(client, {
        "status": "fault",
        "speed_mps": 6.0,
    }).json()["anomalies_detected"]

    assert "fault_status" in anomalies
    assert "overspeed" in anomalies


def test_multiple_anomaly_rows_persisted(client, db_session):
    post(client, {"vehicle_id": "v-1", "battery_pct": 5, "status": "fault"})
    rows = db_session.query(Anomaly).filter_by(vehicle_id="v-1").all()
    types = {r.anomaly_type for r in rows}
    assert "battery_critical" in types
    assert "fault_status" in types


# ---------------------------------------------------------------------------
# Input validation (422)
# ---------------------------------------------------------------------------

def test_missing_vehicle_id_returns_422(client):
    payload = {k: v for k, v in BASE.items() if k != "vehicle_id"}
    assert client.post("/telemetry", json=payload).status_code == 422


def test_missing_timestamp_returns_422(client):
    payload = {k: v for k, v in BASE.items() if k != "timestamp"}
    assert client.post("/telemetry", json=payload).status_code == 422


def test_invalid_status_returns_422(client):
    assert post(client, {"status": "driving"}).status_code == 422


def test_battery_above_100_returns_422(client):
    assert post(client, {"battery_pct": 101}).status_code == 422


def test_battery_below_0_returns_422(client):
    assert post(client, {"battery_pct": -1}).status_code == 422


def test_negative_speed_returns_422(client):
    assert post(client, {"speed_mps": -0.1}).status_code == 422

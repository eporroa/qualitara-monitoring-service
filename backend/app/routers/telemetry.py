import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Anomaly, Mission, Telemetry, Vehicle
from ..schemas import TelemetryIn, TelemetryOut

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


def _detect_anomalies(payload: TelemetryIn) -> list[dict]:
    found = []

    if payload.battery_pct < 10:
        found.append({"type": "battery_critical", "details": {"battery_pct": payload.battery_pct}})
    elif payload.battery_pct < 20:
        found.append({"type": "battery_low", "details": {"battery_pct": payload.battery_pct}})

    if payload.status == "fault":
        found.append({"type": "fault_status", "details": {"status": payload.status}})

    if payload.status == "idle" and payload.speed_mps > 0.5:
        found.append({"type": "phantom_motion", "details": {"speed_mps": payload.speed_mps, "status": payload.status}})

    if payload.speed_mps > 5.0:
        found.append({"type": "overspeed", "details": {"speed_mps": payload.speed_mps}})

    if payload.error_codes:
        found.append({"type": "error_reported", "details": {"error_codes": payload.error_codes}})

    return found


@router.post("", response_model=TelemetryOut, status_code=201)
def ingest_telemetry(payload: TelemetryIn, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)

    record = Telemetry(
        vehicle_id=payload.vehicle_id,
        timestamp=payload.timestamp,
        lat=payload.lat,
        lon=payload.lon,
        battery_pct=payload.battery_pct,
        speed_mps=payload.speed_mps,
        status=payload.status,
        error_codes=json.dumps(payload.error_codes),
        zone_entered=payload.zone_entered,
    )
    db.add(record)

    vehicle = db.get(Vehicle, payload.vehicle_id)
    if vehicle:
        vehicle.current_status = payload.status
        vehicle.current_battery_pct = payload.battery_pct
        vehicle.updated_at = now
    else:
        db.add(Vehicle(
            vehicle_id=payload.vehicle_id,
            current_status=payload.status,
            current_battery_pct=payload.battery_pct,
            updated_at=now,
        ))

    anomaly_types = []
    for a in _detect_anomalies(payload):
        db.add(Anomaly(
            vehicle_id=payload.vehicle_id,
            detected_at=now,
            anomaly_type=a["type"],
            details=json.dumps(a["details"]),
        ))
        anomaly_types.append(a["type"])

    if payload.zone_entered:
        db.execute(
            text("UPDATE zones SET entry_count = entry_count + 1 WHERE zone_id = :zid"),
            {"zid": payload.zone_entered},
        )

    db.flush()
    db.commit()
    db.refresh(record)

    return TelemetryOut(
        id=record.id,
        vehicle_id=record.vehicle_id,
        timestamp=record.timestamp,
        anomalies_detected=anomaly_types,
    )

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import SessionLocal, get_db
from ..models import Anomaly, MaintenanceRecord, Mission, Vehicle
from ..schemas import AnomalyOut, VehicleOut, VehicleStatusUpdate

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def _latest_anomaly(db: Session, vehicle_id: str) -> AnomalyOut | None:
    row = (
        db.query(Anomaly)
        .filter(Anomaly.vehicle_id == vehicle_id)
        .order_by(Anomaly.detected_at.desc())
        .first()
    )
    if not row:
        return None
    return AnomalyOut(
        id=row.id,
        vehicle_id=row.vehicle_id,
        detected_at=row.detected_at,
        anomaly_type=row.anomaly_type,
        details=json.loads(row.details),
    )


@router.get("", response_model=list[VehicleOut])
def list_vehicles(db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).order_by(
        text("CAST(SUBSTR(vehicle_id, 3) AS INTEGER)")
    ).all()
    return [
        VehicleOut(
            vehicle_id=v.vehicle_id,
            current_status=v.current_status,
            current_battery_pct=v.current_battery_pct,
            updated_at=v.updated_at,
            latest_anomaly=_latest_anomaly(db, v.vehicle_id),
        )
        for v in vehicles
    ]


@router.post("/{vehicle_id}/status", response_model=VehicleOut)
def update_vehicle_status(
    vehicle_id: str,
    payload: VehicleStatusUpdate,
    db: Session = Depends(get_db),
):
    if payload.new_status == "fault":
        # BEGIN IMMEDIATE prevents another writer from sneaking in between our
        # read (is it already fault?) and our writes (cancel missions).
        db.execute(text("BEGIN IMMEDIATE"))
        try:
            vehicle = db.get(Vehicle, vehicle_id)
            if not vehicle:
                raise HTTPException(status_code=404, detail="Vehicle not found")

            if vehicle.current_status != "fault":
                now = datetime.now(timezone.utc)

                db.query(Mission).filter(
                    Mission.vehicle_id == vehicle_id,
                    Mission.status == "active",
                ).update({"status": "cancelled", "cancelled_at": now})

                db.add(MaintenanceRecord(
                    vehicle_id=vehicle_id,
                    created_at=now,
                    reason="vehicle transitioned to fault status",
                ))

                vehicle.current_status = "fault"
                vehicle.updated_at = now

            db.commit()
        except Exception:
            db.rollback()
            raise
    else:
        vehicle = db.get(Vehicle, vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        vehicle.current_status = payload.new_status
        vehicle.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(vehicle)

    db.refresh(vehicle)
    return VehicleOut(
        vehicle_id=vehicle.vehicle_id,
        current_status=vehicle.current_status,
        current_battery_pct=vehicle.current_battery_pct,
        updated_at=vehicle.updated_at,
        latest_anomaly=_latest_anomaly(db, vehicle_id),
    )

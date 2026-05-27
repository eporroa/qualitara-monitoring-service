from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Vehicle
from ..schemas import FleetStateOut

router = APIRouter(prefix="/fleet", tags=["fleet"])


@router.get("/state", response_model=FleetStateOut)
def get_fleet_state(db: Session = Depends(get_db)):
    rows = (
        db.query(Vehicle.current_status, func.count(Vehicle.vehicle_id))
        .group_by(Vehicle.current_status)
        .all()
    )
    counts: dict[str, int] = {status: count for status, count in rows}
    total = sum(counts.values())
    return FleetStateOut(
        idle=counts.get("idle", 0),
        moving=counts.get("moving", 0),
        charging=counts.get("charging", 0),
        fault=counts.get("fault", 0),
        total=total,
    )

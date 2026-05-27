import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Anomaly
from ..schemas import AnomalyOut

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[AnomalyOut])
def list_anomalies(
    vehicle_id: Optional[str] = Query(None),
    from_time: Optional[datetime] = Query(None),
    to_time: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Anomaly)

    if vehicle_id:
        q = q.filter(Anomaly.vehicle_id == vehicle_id)
    if from_time:
        q = q.filter(Anomaly.detected_at >= from_time)
    if to_time:
        q = q.filter(Anomaly.detected_at <= to_time)

    rows = q.order_by(Anomaly.detected_at.desc()).limit(200).all()

    return [
        AnomalyOut(
            id=r.id,
            vehicle_id=r.vehicle_id,
            detected_at=r.detected_at,
            anomaly_type=r.anomaly_type,
            details=json.loads(r.details),
        )
        for r in rows
    ]

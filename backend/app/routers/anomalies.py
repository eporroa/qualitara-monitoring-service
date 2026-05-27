from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import AnomalyOut

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("", response_model=list[AnomalyOut])
def list_anomalies(
    vehicle_id: Optional[str] = Query(None),
    from_time: Optional[datetime] = Query(None),
    to_time: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    # TODO: implement
    raise NotImplementedError

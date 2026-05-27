from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import TelemetryIn, TelemetryOut

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("", response_model=TelemetryOut, status_code=201)
def ingest_telemetry(payload: TelemetryIn, db: Session = Depends(get_db)):
    # TODO: implement
    raise NotImplementedError

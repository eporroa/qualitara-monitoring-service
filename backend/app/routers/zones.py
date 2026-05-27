from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Zone
from ..schemas import ZoneCountOut

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("/counts", response_model=list[ZoneCountOut])
def get_zone_counts(db: Session = Depends(get_db)):
    zones = db.query(Zone).order_by(Zone.zone_id).all()
    return [ZoneCountOut(zone_id=z.zone_id, entry_count=z.entry_count) for z in zones]

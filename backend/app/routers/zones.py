from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ZoneCountOut

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("/counts", response_model=list[ZoneCountOut])
def get_zone_counts(db: Session = Depends(get_db)):
    # TODO: implement
    raise NotImplementedError

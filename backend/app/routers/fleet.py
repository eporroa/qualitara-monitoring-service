from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import FleetStateOut

router = APIRouter(prefix="/fleet", tags=["fleet"])


@router.get("/state", response_model=FleetStateOut)
def get_fleet_state(db: Session = Depends(get_db)):
    # TODO: implement
    raise NotImplementedError

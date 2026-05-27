from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import VehicleOut, VehicleStatusUpdate

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleOut])
def list_vehicles(db: Session = Depends(get_db)):
    # TODO: implement
    raise NotImplementedError


@router.post("/{vehicle_id}/status", response_model=VehicleOut)
def update_vehicle_status(
    vehicle_id: str,
    payload: VehicleStatusUpdate,
    db: Session = Depends(get_db),
):
    # TODO: implement
    raise NotImplementedError

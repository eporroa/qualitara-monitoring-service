from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class TelemetryIn(BaseModel):
    vehicle_id: str
    timestamp: datetime
    lat: float
    lon: float
    battery_pct: float = Field(ge=0, le=100)
    speed_mps: float = Field(ge=0)
    status: str = Field(pattern="^(idle|moving|charging|fault)$")
    error_codes: list[str] = []
    zone_entered: Optional[str] = None


class TelemetryOut(BaseModel):
    id: int
    vehicle_id: str
    timestamp: datetime
    anomalies_detected: list[str] = []

    model_config = {"from_attributes": True}


class AnomalyOut(BaseModel):
    id: int
    vehicle_id: str
    detected_at: datetime
    anomaly_type: str
    details: dict[str, Any]

    model_config = {"from_attributes": True}


class ZoneCountOut(BaseModel):
    zone_id: str
    entry_count: int

    model_config = {"from_attributes": True}


class FleetStateOut(BaseModel):
    idle: int = 0
    moving: int = 0
    charging: int = 0
    fault: int = 0
    total: int = 0


class VehicleOut(BaseModel):
    vehicle_id: str
    current_status: str
    current_battery_pct: float
    updated_at: Optional[datetime]
    latest_anomaly: Optional[AnomalyOut] = None

    model_config = {"from_attributes": True}


class VehicleStatusUpdate(BaseModel):
    new_status: str = Field(pattern="^(idle|moving|charging|fault)$")

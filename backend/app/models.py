import json
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


def _now():
    return datetime.now(timezone.utc)


class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(String, primary_key=True, index=True)
    current_status = Column(String, nullable=False, default="idle")
    current_battery_pct = Column(Float, nullable=False, default=100.0)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)

    telemetry = relationship("Telemetry", back_populates="vehicle", lazy="dynamic")
    anomalies = relationship("Anomaly", back_populates="vehicle", lazy="dynamic")
    missions = relationship("Mission", back_populates="vehicle", lazy="dynamic")
    maintenance_records = relationship("MaintenanceRecord", back_populates="vehicle", lazy="dynamic")


class Telemetry(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String, ForeignKey("vehicles.vehicle_id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    battery_pct = Column(Float, nullable=False)
    speed_mps = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    error_codes = Column(Text, nullable=False, default="[]")  # JSON array
    zone_entered = Column(String, nullable=True)

    vehicle = relationship("Vehicle", back_populates="telemetry")

    @property
    def error_codes_list(self):
        return json.loads(self.error_codes)


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String, ForeignKey("vehicles.vehicle_id"), nullable=False, index=True)
    detected_at = Column(DateTime(timezone=True), default=_now, nullable=False, index=True)
    anomaly_type = Column(String, nullable=False)
    details = Column(Text, nullable=False, default="{}")  # JSON object

    vehicle = relationship("Vehicle", back_populates="anomalies")


class Zone(Base):
    __tablename__ = "zones"

    zone_id = Column(String, primary_key=True)
    entry_count = Column(Integer, nullable=False, default=0)


class Mission(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String, ForeignKey("vehicles.vehicle_id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="active")  # active | cancelled
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    vehicle = relationship("Vehicle", back_populates="missions")


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String, ForeignKey("vehicles.vehicle_id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    reason = Column(String, nullable=False)

    vehicle = relationship("Vehicle", back_populates="maintenance_records")

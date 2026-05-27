from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, SessionLocal, engine
from .routers import anomalies, fleet, telemetry, vehicles, zones


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _seed_db()
    yield


def _seed_db():
    from .constants import VEHICLE_IDS, ZONES
    from .models import Vehicle, Zone

    db = SessionLocal()
    try:
        for vid in VEHICLE_IDS:
            if not db.get(Vehicle, vid):
                db.add(Vehicle(vehicle_id=vid))

        for zone_id in ZONES:
            if not db.get(Zone, zone_id):
                db.add(Zone(zone_id=zone_id, entry_count=0))

        db.commit()
    finally:
        db.close()


app = FastAPI(title="Fleet Telemetry Monitoring Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry.router)
app.include_router(vehicles.router)
app.include_router(fleet.router)
app.include_router(zones.router)
app.include_router(anomalies.router)


@app.get("/health")
def health():
    return {"status": "ok"}

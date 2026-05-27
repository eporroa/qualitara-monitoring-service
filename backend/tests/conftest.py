import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.constants import ZONES
from app.database import Base, get_db
from app.main import app
from app.models import Zone


@pytest.fixture
def db_engine():
    """
    In-memory SQLite engine shared across all sessions in a test.

    StaticPool reuses a single connection so every sessionmaker call
    (the request handler's and the test's assertion session) sees the
    same database — required because SQLite in-memory DBs are
    per-connection by default.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    with Session() as seed:
        for zone_id in ZONES:
            seed.add(Zone(zone_id=zone_id, entry_count=0))
        seed.commit()

    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """Session used inside tests for setup and assertions."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client(db_engine):
    """
    TestClient wired to the isolated test engine.
    Each request gets its own session (same engine, same StaticPool connection).
    Lifespan is intentionally skipped to avoid seeding the real fleet.db.
    """
    RequestSession = sessionmaker(bind=db_engine)

    def override_get_db():
        db = RequestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app, raise_server_exceptions=True)
    app.dependency_overrides.clear()

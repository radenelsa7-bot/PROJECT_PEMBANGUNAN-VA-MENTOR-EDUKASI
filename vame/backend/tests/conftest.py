import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.client import AIClient, get_ai_client  # noqa: E402
from app.ai.providers import MockProvider  # noqa: E402
from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.ratelimit import ai_limiter, login_limiter  # noqa: E402
from app.routers.curricula import import_curriculum  # noqa: E402
from app.schemas import CurriculumImport  # noqa: E402
from app.security import hash_password  # noqa: E402
from app.seed_data import PYTHON  # noqa: E402


@pytest.fixture()
def env(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path/'test.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def _db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    ai = AIClient(MockProvider(), max_retries=0, backoff_base=0)
    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_ai_client] = lambda: ai
    ai_limiter.reset()
    login_limiter.reset()
    with Session() as db:
        db.add(User(name="Admin", email="admin@t.id", password_hash=hash_password("admin1234"), role="admin"))
        import_curriculum(db, CurriculumImport(**PYTHON))
    yield TestClient(app)
    app.dependency_overrides.clear()


def login(client, email, password):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def learner(env):
    r = env.post("/api/v1/auth/register", json={"name": "Budi Test", "email": "budi@t.id", "password": "rahasia123"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def admin(env):
    return login(env, "admin@t.id", "admin1234")

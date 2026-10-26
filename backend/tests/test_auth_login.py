from pydantic import ValidationError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import User
from app.schemas import LoginRequest
from app.security import hash_password


def test_login_schema_accepts_legacy_local_demo_email():
    request = LoginRequest(
        email="demo@aegisos.local",
        password="AegisOS-demo-password-2026",
    )
    assert request.email == "demo@aegisos.local"


def test_login_schema_normalizes_regular_email():
    request = LoginRequest(email=" Demo@AegisOS.dev ", password="pass")
    assert request.email == "demo@aegisos.dev"


def test_login_schema_rejects_malformed_email():
    try:
        LoginRequest(email="not-an-email", password="pass")
    except ValidationError:
        return
    raise AssertionError("Malformed email should be rejected")


def test_login_endpoint_authenticates_local_demo_account():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestSession() as db:
            db.add(User(
                email="demo@aegisos.local",
                password_hash=hash_password("AegisOS-demo-password-2026"),
            ))
            db.commit()

        with TestClient(app) as client:
            response = client.post(
                "/api/auth/login",
                json={
                    "email": "demo@aegisos.local",
                    "password": "AegisOS-demo-password-2026",
                },
            )
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["access_token"]
        assert body["token_type"] == "bearer"
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(engine)
        engine.dispose()

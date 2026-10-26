from fastapi.testclient import TestClient
from app.main import app

def test_health():
    c=TestClient(app); r=c.get("/health")
    assert r.status_code==200 and r.json()["status"]=="ok"
def test_openapi_present():
    c=TestClient(app); assert c.get("/openapi.json").status_code==200


def test_private_endpoint_requires_auth():
    c=TestClient(app)
    r=c.get("/api/dashboard")
    assert r.status_code==401

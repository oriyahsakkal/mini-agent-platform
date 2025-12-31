from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_whoami_requires_key():
    r = client.get("/whoami")
    assert r.status_code == 401

def test_whoami_with_key():
    r = client.get("/whoami", headers={"X-API-Key": "key_tenant_a"})
    assert r.status_code == 200
    assert r.json()["tenant_id"] == "tenant_a"

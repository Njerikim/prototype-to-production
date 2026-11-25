import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.delenv("API_KEY", raising=False)
    from app.main import app
    with TestClient(app) as c:
        yield c


def post(client, **kw):
    body = {"amount": 1200, "hour": 11, "new_device": False, "new_payee": False}
    body.update(kw)
    return client.post("/transactions", json=body)


def test_everyday_payment_is_approved(client):
    r = post(client)
    assert r.status_code == 201
    j = r.json()
    assert j["action"] == "approve" and j["status"] == "approved" and j["level"] == "low"
    assert [s["agent"] for s in j["steps"]] == ["Intake", "Risk", "Action", "Human"]


def test_risky_payment_is_blocked(client):
    j = post(client, amount=85000, hour=2, new_device=True).json()
    assert j["action"] == "block" and j["status"] == "blocked" and j["score"] >= 0.7


def test_medium_payment_waits_for_owner_then_approved(client):
    j = post(client, amount=18500, hour=16, new_payee=True).json()
    assert j["status"] == "pending"
    d = client.post(f"/transactions/{j['id']}/decision", json={"decision": "approve"})
    assert d.status_code == 200 and d.json()["status"] == "approved"
    again = client.post(f"/transactions/{j['id']}/decision", json={"decision": "decline"})
    assert again.status_code == 409


def test_audit_log_records_every_step(client):
    post(client)
    assert len(client.get("/audit").json()) == 4


def test_validation_rejects_bad_input(client):
    assert post(client, hour=30).status_code == 422
    assert post(client, amount=-5).status_code == 422


def test_api_key_required_when_set(client, monkeypatch):
    monkeypatch.setenv("API_KEY", "secret")
    assert post(client).status_code == 401
    ok = client.post("/transactions", headers={"X-API-Key": "secret"},
                     json={"amount": 100, "hour": 10})
    assert ok.status_code == 201

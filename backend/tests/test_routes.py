from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.models.classification import Classification
from app.models.profile import ScoutProfile


def test_scout_run_returns_profile(monkeypatch):
    fake_profile = ScoutProfile(
        id="profile-1",
        company_name="Groupe Clarins",
        classification=Classification(service_line="training", confidence=0.9, rationale="x"),
        brief="Brief text",
        talking_points=["Question?"],
        rationale="Rationale text",
    )
    monkeypatch.setattr(routes, "run_scout", lambda company_name, note: fake_profile)

    client = TestClient(app)
    response = client.post("/scout/run", json={"company_name": "Groupe Clarins", "note": "inbound"})

    assert response.status_code == 200
    body = response.json()
    assert body["company_name"] == "Groupe Clarins"
    assert body["classification"]["service_line"] == "training"


def test_scout_run_rejects_empty_company_name():
    client = TestClient(app)
    response = client.post("/scout/run", json={"company_name": ""})
    assert response.status_code == 422


def test_scout_run_returns_502_on_failure(monkeypatch):
    def boom(company_name, note):
        raise RuntimeError("search failed")

    monkeypatch.setattr(routes, "run_scout", boom)

    client = TestClient(app)
    response = client.post("/scout/run", json={"company_name": "Groupe Clarins"})

    assert response.status_code == 502

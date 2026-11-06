import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(str(tmp_path / "department-test.db"), "admin-secret"))


def test_departments_require_admin(client):
    assert client.get("/api/departments").status_code == 401


def test_department_registry_is_available(client):
    response = client.get("/api/departments", headers={"X-Admin-Token": "admin-secret"})
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()["departments"]}
    assert {"marketing", "hr", "finance", "operations", "sales", "technology"} <= ids


def test_unknown_department_is_rejected(client):
    response = client.post(
        "/api/department-tasks",
        headers={"X-Admin-Token": "admin-secret"},
        json={"department": "legal", "task": "Review this draft"},
    )
    assert response.status_code == 404


def test_department_task_requires_model_configuration(client, monkeypatch):
    monkeypatch.delenv("AURA_LLM_BASE_URL", raising=False)
    monkeypatch.delenv("AURA_LLM_MODEL", raising=False)
    response = client.post(
        "/api/department-tasks",
        headers={"X-Admin-Token": "admin-secret"},
        json={"department": "marketing", "task": "Prepare a launch campaign"},
    )
    assert response.status_code == 503
    assert "AURA_LLM_BASE_URL" in response.json()["detail"]


def test_department_task_uses_specialist_agent(client, monkeypatch):
    import app.department_agents as agents

    async def fake_model(system_prompt, user_prompt):
        assert "Marketing specialist" in system_prompt
        assert "launch campaign" in user_prompt
        return "Draft campaign plan", "test-model"

    monkeypatch.setattr(agents, "call_chat_model", fake_model)
    response = client.post(
        "/api/department-tasks",
        headers={"X-Admin-Token": "admin-secret"},
        json={"department": "marketing", "task": "Prepare a launch campaign"},
    )
    assert response.status_code == 200
    assert response.json()["agent_name"] == "AURA Marketing Agent"
    assert response.json()["external_actions_executed"] is False


def test_coordinator_runs_selected_departments(client, monkeypatch):
    import app.department_agents as agents

    async def fake_model(system_prompt, user_prompt):
        return "Department draft", "test-model"

    monkeypatch.setattr(agents, "call_chat_model", fake_model)
    response = client.post(
        "/api/coordinator/tasks",
        headers={"X-Admin-Token": "admin-secret"},
        json={
            "departments": ["marketing", "sales"],
            "task": "Prepare the product launch plan",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert {item["department"] for item in payload["department_results"]} == {"marketing", "sales"}
    assert payload["external_actions_executed"] is False

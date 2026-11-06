from fastapi.testclient import TestClient
from app.main import create_app

def client(tmp_path):
    return TestClient(create_app(str(tmp_path / "test.db"), "admin-secret"))

def register(c, actions=None, approvals=None):
    response = c.post("/api/agents", headers={"X-Admin-Token": "admin-secret"},
        json={"name": "Test Agent", "description": "test",
              "allowed_actions": actions or ["doc.read", "payment.send"],
              "approval_actions": approvals if approvals is not None else ["payment.send"]})
    assert response.status_code == 201
    return response.json()

def test_health(tmp_path):
    assert client(tmp_path).get("/health").json()["status"] == "ok"

def test_admin_auth(tmp_path):
    assert client(tmp_path).get("/api/agents").status_code == 401

def test_agent_token_not_listed(tmp_path):
    c = client(tmp_path)
    agent = register(c)
    rows = c.get("/api/agents", headers={"X-Admin-Token": "admin-secret"}).json()
    assert "token" not in rows[0] and agent["token"].startswith("aura_")

def test_allow_and_block(tmp_path):
    c = client(tmp_path)
    agent = register(c)
    headers = {"Authorization": f"Bearer {agent['token']}"}
    assert c.post("/api/actions", headers=headers,
        json={"action": "doc.read", "resource": "doc/1"}).json()["status"] == "awaiting_result"
    assert c.post("/api/actions", headers=headers,
        json={"action": "doc.delete", "resource": "doc/1"}).json()["status"] == "blocked"

def test_approval_and_report(tmp_path):
    c = client(tmp_path)
    agent = register(c)
    headers = {"Authorization": f"Bearer {agent['token']}"}
    admin = {"X-Admin-Token": "admin-secret"}
    action = c.post("/api/actions", headers=headers,
        json={"action": "payment.send", "resource": "invoice/1"}).json()
    assert action["status"] == "pending_approval"
    assert c.post(f"/api/actions/{action['id']}/approve", headers=admin).json()["status"] == "awaiting_result"
    result = c.post(f"/api/actions/{action['id']}/result", headers=headers,
        json={"expected_value": "sent", "observed_value": "sent", "evidence_ref": "demo://1"}).json()
    assert result["status"] == "reported_match"
    assert result["outcome"]["verification_level"] == "agent_reported_not_independently_verified"

def test_other_agent_cannot_report_action(tmp_path):
    c = client(tmp_path)
    first = register(c)
    second = register(c, ["doc.read"], [])
    action = c.post("/api/actions", headers={"Authorization": f"Bearer {first['token']}"},
        json={"action": "doc.read", "resource": "doc/1"}).json()
    response = c.post(f"/api/actions/{action['id']}/result",
        headers={"Authorization": f"Bearer {second['token']}"},
        json={"expected_value": "a", "observed_value": "a", "evidence_ref": "demo://1"})
    assert response.status_code == 403

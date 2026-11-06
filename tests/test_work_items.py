from fastapi.testclient import TestClient

from app.main import create_app


def test_work_item_lifecycle(tmp_path):
    client = TestClient(create_app(str(tmp_path / "aura.db"), "admin-secret"))
    headers = {"X-Admin-Token": "admin-secret"}
    created = client.post(
        "/api/work-items",
        headers=headers,
        json={
            "title": "Prepare launch plan",
            "description": "Create a launch plan and risks.",
            "departments": ["marketing", "sales"],
            "priority": "high",
        },
    )
    assert created.status_code == 201
    item = created.json()
    assert item["status"] == "backlog"
    assert item["departments"] == ["marketing", "sales"]

    changed = client.patch(
        f"/api/work-items/{item['id']}",
        headers=headers,
        json={"status": "in_progress"},
    )
    assert changed.status_code == 200
    assert changed.json()["status"] == "in_progress"

    listed = client.get("/api/work-items", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == item["id"]


def test_work_items_require_admin_and_valid_departments(tmp_path):
    client = TestClient(create_app(str(tmp_path / "aura.db"), "admin-secret"))
    payload = {
        "title": "Prepare launch plan",
        "description": "Create a launch plan.",
        "departments": ["not-a-department"],
    }
    assert client.get("/api/work-items").status_code == 401
    assert client.post("/api/work-items", json=payload).status_code == 401
    response = client.post("/api/work-items", headers={"X-Admin-Token": "admin-secret"}, json=payload)
    assert response.status_code == 422

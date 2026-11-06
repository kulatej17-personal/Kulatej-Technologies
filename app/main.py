import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db import Database
from app.policy import evaluate_action
from app.schemas import (
    ActionCreate,
    ActionPublic,
    ActionResult,
    AgentCreate,
    AgentCreated,
    AgentPublic,
    CoordinatorTaskCreate,
    DepartmentTaskCreate,
    WorkItemCreate,
    WorkItemUpdate,
)
from app.security import extract_bearer, hash_token, new_agent_token, require_admin


def now():
    return datetime.now(UTC).isoformat()


def create_app(db_path=None, admin_token=None):
    db = Database(db_path or os.getenv("AURA_DB_PATH", "data/aura.db"))
    secret = admin_token or os.getenv("AURA_ADMIN_TOKEN", "local-dev-change-this-token")
    app = FastAPI(title="Kulatej AURA Guard API", version="0.1.0",
                  description="Early MVP policy and audit API for AI-agent workflows")
    static = Path(__file__).resolve().parent.parent / "static"
    app.mount("/static", StaticFiles(directory=static), name="static")

    def admin(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")):
        require_admin(x_admin_token, secret)

    def agent(authorization: str | None = Header(default=None)):
        row = db.one("SELECT * FROM agents WHERE token_hash=?", (hash_token(extract_bearer(authorization)),))
        if not row:
            raise HTTPException(401, "Unknown agent credential")
        return row

    def public_action(row):
        found = db.one("SELECT name FROM agents WHERE id=?", (row["agent_id"],))
        out = db.decode_action(row)
        out["agent_name"] = found["name"] if found else "Unknown"
        return out

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(static / "index.html")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "kulatej-aura-guard", "version": "0.1.0"}

    @app.post("/api/agents", response_model=AgentCreated, status_code=201, dependencies=[Depends(admin)])
    def create_agent(body: AgentCreate):
        if set(body.approval_actions) - set(body.allowed_actions):
            raise HTTPException(422, "Approval actions must also be allow-listed")
        token = new_agent_token()
        agent_id = str(uuid.uuid4())
        timestamp = now()
        db.execute("INSERT INTO agents VALUES(?,?,?,?,?,?,?)",
                   (agent_id, body.name, body.description, hash_token(token),
                    json.dumps(body.allowed_actions), json.dumps(body.approval_actions), timestamp))
        return {"id": agent_id, "name": body.name, "description": body.description,
                "allowed_actions": body.allowed_actions, "approval_actions": body.approval_actions,
                "created_at": timestamp, "token": token}

    @app.get("/api/agents", response_model=list[AgentPublic], dependencies=[Depends(admin)])
    def agents():
        return [db.decode_agent(r) for r in db.all("SELECT * FROM agents ORDER BY created_at DESC")]

    @app.post("/api/actions", response_model=ActionPublic, status_code=201)
    def request_action(body: ActionCreate, a: Annotated[dict, Depends(agent)]):
        status, reason = evaluate_action(body.action, json.loads(a["allowed_actions"]),
                                         json.loads(a["approval_actions"]))
        action_id = str(uuid.uuid4())
        timestamp = now()
        db.execute("INSERT INTO actions VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (action_id, a["id"], body.action, body.resource, status, reason,
                    json.dumps(body.payload), None, timestamp, timestamp))
        return public_action(db.one("SELECT * FROM actions WHERE id=?", (action_id,)))

    @app.get("/api/actions", response_model=list[ActionPublic], dependencies=[Depends(admin)])
    def actions(limit: int = 50):
        safe_limit = max(1, min(limit, 200))
        return [public_action(r) for r in db.all(
            "SELECT * FROM actions ORDER BY created_at DESC LIMIT ?", (safe_limit,))]

    def transition(action_id, status_from, status_to, reason):
        row = db.one("SELECT * FROM actions WHERE id=?", (action_id,))
        if not row:
            raise HTTPException(404, "Action not found")
        if row["status"] != status_from:
            raise HTTPException(409, "Action is not in the required state")
        db.execute("UPDATE actions SET status=?,reason=?,updated_at=? WHERE id=?",
                   (status_to, reason, now(), action_id))
        return public_action(db.one("SELECT * FROM actions WHERE id=?", (action_id,)))

    @app.post("/api/actions/{action_id}/approve", response_model=ActionPublic, dependencies=[Depends(admin)])
    def approve(action_id: str):
        return transition(action_id, "pending_approval", "awaiting_result",
                          "Approved by an administrator; awaiting outcome report.")

    @app.post("/api/actions/{action_id}/reject", response_model=ActionPublic, dependencies=[Depends(admin)])
    def reject(action_id: str):
        return transition(action_id, "pending_approval", "blocked", "Rejected by an administrator.")

    @app.post("/api/actions/{action_id}/result", response_model=ActionPublic)
    def result(action_id: str, body: ActionResult, a: Annotated[dict, Depends(agent)]):
        row = db.one("SELECT * FROM actions WHERE id=?", (action_id,))
        if not row:
            raise HTTPException(404, "Action not found")
        if row["agent_id"] != a["id"]:
            raise HTTPException(403, "Agent does not own this action")
        if row["status"] != "awaiting_result":
            raise HTTPException(409, "Action is not awaiting a result")
        match = body.expected_value.strip() == body.observed_value.strip()
        status = "reported_match" if match else "reported_mismatch"
        outcome = {"expected_value": body.expected_value, "observed_value": body.observed_value,
                   "evidence_ref": body.evidence_ref, "comparison": "match" if match else "mismatch",
                   "verification_level": "agent_reported_not_independently_verified"}
        db.execute("UPDATE actions SET status=?,outcome=?,reason=?,updated_at=? WHERE id=?",
                   (status, json.dumps(outcome),
                    "Agent-reported values match." if match else "Agent-reported values differ.",
                    now(), action_id))
        return public_action(db.one("SELECT * FROM actions WHERE id=?", (action_id,)))


    @app.get("/api/departments", dependencies=[Depends(admin)])
    def departments():
        from app.department_agents import load_department_registry

        registry = load_department_registry()
        return {
            "coordinator": registry["coordinator"],
            "departments": registry["departments"],
            "runtime_status": "model_configuration_required",
        }

    @app.post("/api/department-tasks", dependencies=[Depends(admin)])
    async def department_task(body: DepartmentTaskCreate):
        from app.department_agents import run_department_agent

        try:
            return await run_department_agent(body.department, body.task, body.context)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(503, str(exc)) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(502, "The configured AI provider could not complete the request.") from exc

    @app.post("/api/coordinator/tasks", dependencies=[Depends(admin)])
    async def coordinator_task(body: CoordinatorTaskCreate):
        import asyncio

        from app.department_agents import get_department, run_department_agent

        if len(set(body.departments)) != len(body.departments):
            raise HTTPException(422, "Department IDs must be unique.")
        unknown = [item for item in body.departments if get_department(item) is None]
        if unknown:
            raise HTTPException(422, f"Unknown department IDs: {', '.join(unknown)}")
        results = await asyncio.gather(
            *(run_department_agent(item, body.task, body.context) for item in body.departments),
            return_exceptions=True,
        )
        completed = []
        failed = []
        for department_id, result in zip(body.departments, results):
            if isinstance(result, Exception):
                failed.append({"department": department_id, "error": str(result)})
            else:
                completed.append(result)
        return {
            "task": body.task,
            "status": "completed" if not failed else ("partial" if completed else "failed"),
            "department_results": completed,
            "failures": failed,
            "external_actions_executed": False,
            "human_review_required": True,
        }

    @app.get("/api/work-items", dependencies=[Depends(admin)])
    def list_work_items():
        rows = db.all("SELECT * FROM work_items ORDER BY updated_at DESC")
        for row in rows:
            row["departments"] = json.loads(row["departments"])
            row["result"] = json.loads(row["result"]) if row["result"] else None
        return rows

    @app.post("/api/work-items", status_code=201, dependencies=[Depends(admin)])
    def create_work_item(body: WorkItemCreate):
        from app.department_agents import get_department
        if len(set(body.departments)) != len(body.departments):
            raise HTTPException(422, "Department IDs must be unique.")
        unknown = [item for item in body.departments if get_department(item) is None]
        if unknown:
            raise HTTPException(422, f"Unknown department IDs: {', '.join(unknown)}")
        item_id, timestamp = str(uuid.uuid4()), now()
        db.execute(
            "INSERT INTO work_items VALUES(?,?,?,?,?,?,?,?,?)",
            (item_id, body.title, body.description, json.dumps(body.departments),
             "backlog", body.priority, None, timestamp, timestamp),
        )
        row = db.one("SELECT * FROM work_items WHERE id=?", (item_id,))
        row["departments"] = json.loads(row["departments"])
        row["result"] = None
        return row

    @app.patch("/api/work-items/{item_id}", dependencies=[Depends(admin)])
    def update_work_item(item_id: str, body: WorkItemUpdate):
        row = db.one("SELECT * FROM work_items WHERE id=?", (item_id,))
        if not row:
            raise HTTPException(404, "Work item not found")
        db.execute("UPDATE work_items SET status=?,updated_at=? WHERE id=?",
                   (body.status, now(), item_id))
        updated = db.one("SELECT * FROM work_items WHERE id=?", (item_id,))
        updated["departments"] = json.loads(updated["departments"])
        updated["result"] = json.loads(updated["result"]) if updated["result"] else None
        return updated

    @app.post("/api/work-items/{item_id}/run", dependencies=[Depends(admin)])
    async def run_work_item(item_id: str):
        import asyncio
        from app.department_agents import get_department, run_department_agent
        row = db.one("SELECT * FROM work_items WHERE id=?", (item_id,))
        if not row:
            raise HTTPException(404, "Work item not found")
        department_ids = json.loads(row["departments"])
        results = await asyncio.gather(
            *(run_department_agent(dept, row["description"], {"work_item": row["title"]})
              for dept in department_ids),
            return_exceptions=True,
        )
        completed, failed = [], []
        for department_id, result in zip(department_ids, results):
            if isinstance(result, Exception):
                failed.append({"department": department_id, "error": str(result)})
            else:
                completed.append(result)
        output = {
            "status": "completed" if not failed else ("partial" if completed else "failed"),
            "department_results": completed,
            "failures": failed,
            "external_actions_executed": False,
            "human_review_required": True,
        }
        new_status = "done" if not failed else "blocked"
        db.execute("UPDATE work_items SET result=?,status=?,updated_at=? WHERE id=?",
                   (json.dumps(output), new_status, now(), item_id))
        output["work_item_id"] = item_id
        return output

    return app


app = create_app()

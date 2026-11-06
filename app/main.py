import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.db import Database
from app.policy import evaluate_action
from app.schemas import AgentCreate, AgentCreated, AgentPublic, ActionCreate, ActionResult, ActionPublic
from app.security import hash_token, new_agent_token, extract_bearer, require_admin

def now():
    return datetime.now(timezone.utc).isoformat()

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
    def request_action(body: ActionCreate, a=Depends(agent)):
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
    def result(action_id: str, body: ActionResult, a=Depends(agent)):
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

    return app

app = create_app()

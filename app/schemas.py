from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

class AgentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    description: str = Field(default="", max_length=500)
    allowed_actions: list[str] = Field(default_factory=list, max_length=100)
    approval_actions: list[str] = Field(default_factory=list, max_length=100)

class AgentCreated(BaseModel):
    id: str
    name: str
    description: str
    allowed_actions: list[str]
    approval_actions: list[str]
    created_at: datetime
    token: str

class AgentPublic(BaseModel):
    id: str
    name: str
    description: str
    allowed_actions: list[str]
    approval_actions: list[str]
    created_at: datetime

class ActionCreate(BaseModel):
    action: str = Field(min_length=2, max_length=120)
    resource: str = Field(min_length=1, max_length=300)
    payload: dict[str, Any] = Field(default_factory=dict)

class ActionResult(BaseModel):
    expected_value: str = Field(min_length=1, max_length=500)
    observed_value: str = Field(min_length=1, max_length=500)
    evidence_ref: str = Field(min_length=1, max_length=1000)

class ActionPublic(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    action: str
    resource: str
    status: str
    reason: str
    payload: dict[str, Any]
    outcome: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

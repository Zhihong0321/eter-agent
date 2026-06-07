"""Pydantic schemas for WebSocket payloads.

The mobile PWA and the Mac daemon speak the same wire format. Keep this file
in lockstep with the TypeScript types in frontend/src/types/ws.ts.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------- Connection handshake ----------

class WSHello(BaseModel):
    type: Literal["hello"] = "hello"
    department_id: str
    role: Literal["agent", "user"]
    auth_token: str  # shared secret or session JWT


# ---------- Client -> Server (HoD via phone) ----------

class WSUserChat(BaseModel):
    type: Literal["user_chat"] = "user_chat"
    session_id: int
    content: str


class WSUserApprovalResponse(BaseModel):
    type: Literal["respond_approval"] = "respond_approval"
    approval_id: int
    decision: Literal["approved", "rejected"]
    note: str | None = None


# ---------- Server -> Client (Mac daemon) ----------

class WSAgentCommand(BaseModel):
    type: Literal["agent_command"] = "agent_command"
    session_id: int
    content: str


class WSAgentApprovalResult(BaseModel):
    type: Literal["approval_result"] = "approval_result"
    approval_id: int
    decision: Literal["approved", "rejected"]
    note: str | None = None


# ---------- Daemon -> Server (status updates) ----------

class WSAgentChat(BaseModel):
    type: Literal["agent_chat"] = "agent_chat"
    session_id: int
    content: str
    role: Literal["agent", "system"] = "agent"


class WSAgentStateUpdate(BaseModel):
    """Checklist push: a list of {key, title, status, detail} items."""

    type: Literal["state_update"] = "state_update"
    tasks: list[dict[str, Any]] = Field(default_factory=list)


class WSAgentRequestApproval(BaseModel):
    type: Literal["request_approval"] = "request_approval"
    session_id: int
    plan_id: str
    summary: str
    plan: dict[str, Any]


class WSAgentStagingPreview(BaseModel):
    type: Literal["staging_preview"] = "staging_preview"
    url: str
    label: str = "staging"
    expires_at: datetime | None = None


class WSAgentHeartbeat(BaseModel):
    type: Literal["heartbeat"] = "heartbeat"
    status: str = "online"
    extra: dict[str, Any] = Field(default_factory=dict)


# ---------- Server -> Phone (push) ----------

class WSPushToUser(BaseModel):
    type: Literal["push_to_user"] = "push_to_user"
    session_id: int
    content: str
    role: Literal["agent", "system"] = "agent"


class WSPushApprovalRequest(BaseModel):
    type: Literal["approval_request"] = "approval_request"
    approval_id: int
    plan_id: str
    summary: str
    plan: dict[str, Any]


class WSPushStateUpdate(BaseModel):
    type: Literal["state_update"] = "state_update"
    tasks: list[dict[str, Any]]


class WSPushStagingPreview(BaseModel):
    type: Literal["staging_preview"] = "staging_preview"
    url: str
    label: str = "staging"


# Discriminated union for inbound
InboundMessage = (
    WSHello
    | WSUserChat
    | WSUserApprovalResponse
    | WSAgentChat
    | WSAgentStateUpdate
    | WSAgentRequestApproval
    | WSAgentStagingPreview
    | WSAgentHeartbeat
)

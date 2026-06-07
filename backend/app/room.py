"""In-memory WebSocket room registry, shared by ws.py and handlers.py.

One process owns one of these. If you scale to multiple uvicorn workers,
swap this for a Redis pub/sub fan-out (or a NATS subject per department).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket


@dataclass
class DepartmentRoom:
    department_id: str
    agent_sockets: set[WebSocket] = field(default_factory=set)
    user_sockets: set[WebSocket] = field(default_factory=set)

    async def broadcast_to_users(self, payload: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in list(self.user_sockets):
            try:
                await ws.send_json(payload)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        for ws in dead:
            self.user_sockets.discard(ws)

    async def send_to_agents(self, payload: dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        for ws in list(self.agent_sockets):
            try:
                await ws.send_json(payload)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        for ws in dead:
            self.agent_sockets.discard(ws)


# Single-process registry. OK for dev; see note above.
_rooms: dict[str, DepartmentRoom] = {}


def get_room(department_id: str) -> DepartmentRoom:
    if department_id not in _rooms:
        _rooms[department_id] = DepartmentRoom(department_id=department_id)
    return _rooms[department_id]

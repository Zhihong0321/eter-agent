"""WebSocket router.

The mailbox coordinator multiplexes two kinds of connections per department:
  - 'agent' socket  (the Mac Mini Hermes daemon)
  - 'user' socket   (the HoD's phone via the PWA)

Both speak the same JSON message shapes defined in app.schemas.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth import authenticate_socket
from app.config import get_settings
from app.handlers import (
    handle_agent_chat,
    handle_agent_heartbeat,
    handle_agent_request_approval,
    handle_agent_staging_preview,
    handle_agent_state_update,
    handle_user_approval_response,
    handle_user_chat,
)
from app.room import DepartmentRoom, get_room

log = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    """Single endpoint. Role is declared in the first `hello` message."""
    await websocket.accept()
    settings = get_settings()

    department_id: str | None = None
    role: str | None = None
    room: DepartmentRoom | None = None

    try:
        first = await websocket.receive_json()
        if first.get("type") != "hello":
            await websocket.close(code=1008, reason="expected hello")
            return

        department_id = first.get("department_id", "")
        role = first.get("role", "")
        auth_token = first.get("auth_token", "")

        if role not in ("agent", "user"):
            await websocket.close(code=1008, reason="bad role")
            return

        if not authenticate_socket(auth_token, settings.ws_shared_secret):
            await websocket.close(code=1008, reason="auth failed")
            return

        room = get_room(department_id)
        if role == "agent":
            room.agent_sockets.add(websocket)
        else:
            room.user_sockets.add(websocket)
        log.info("ws connected: dept=%s role=%s", department_id, role)
        await websocket.send_json({"type": "hello_ack", "role": role})

        # Main loop
        while True:
            msg = await websocket.receive_json()
            mtype = msg.get("type")

            if role == "user":
                if mtype == "user_chat":
                    await handle_user_chat(room, msg, websocket)
                elif mtype == "respond_approval":
                    await handle_user_approval_response(room, msg)
                else:
                    await websocket.send_json(
                        {"type": "error", "detail": f"unknown user msg: {mtype}"}
                    )

            elif role == "agent":
                if mtype == "agent_chat":
                    await handle_agent_chat(room, msg)
                elif mtype == "state_update":
                    await handle_agent_state_update(room, msg)
                elif mtype == "request_approval":
                    await handle_agent_request_approval(room, msg)
                elif mtype == "staging_preview":
                    await handle_agent_staging_preview(room, msg)
                elif mtype == "heartbeat":
                    await handle_agent_heartbeat(room, msg)
                else:
                    await websocket.send_json(
                        {"type": "error", "detail": f"unknown agent msg: {mtype}"}
                    )

    except WebSocketDisconnect:
        log.info("ws disconnected: dept=%s role=%s", department_id, role)
    except Exception as e:  # noqa: BLE001
        log.exception("ws error: %s", e)
        try:
            await websocket.close(code=1011, reason="server error")
        except Exception:  # noqa: BLE001
            pass
    finally:
        if room and role == "agent" and websocket in room.agent_sockets:
            room.agent_sockets.discard(websocket)
        if room and role == "user" and websocket in room.user_sockets:
            room.user_sockets.discard(websocket)

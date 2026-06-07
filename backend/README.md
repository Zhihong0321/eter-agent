# eter-agent backend

Mailbox coordinator for the multi-department AI IT team. Sits between the
Mac Mini Hermes daemon and the mobile PWA, fanning out chat, checklist
state, approval requests, and staging previews.

## Run locally

```bash
cd backend
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
cp .env.example .env   # then edit
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/health to confirm.

## Run tests

```bash
.venv/Scripts/python.exe -m pytest -v
```

## Layout

- `app/main.py`      FastAPI entrypoint + lifespan (init DB, start sweeper)
- `app/ws.py`        WebSocket router, in-memory per-department rooms
- `app/handlers.py`  Per-message-type handlers (chat, state, approval, preview, heartbeat)
- `app/models.py`    SQLAlchemy ORM models for the 6 tables
- `app/schemas.py`   Pydantic wire-format models shared with the frontend
- `app/auth.py`      WS handshake (constant-time shared secret compare)
- `app/db.py`        Async SQLAlchemy engine and session factory
- `app/config.py`    pydantic-settings, env-driven
- `app/heartbeat.py` Background sweeper that flips stale depts to offline

## WebSocket protocol

`/ws` accepts one connection per client. The first message must be a
`hello` frame declaring `department_id`, `role` (`agent` or `user`), and
`auth_token`. See `app/schemas.py` for the full message catalog.

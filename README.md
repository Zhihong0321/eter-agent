# eter-agent

Multi-department AI IT team runtime. Each department (Marketing,
Sales, Operations, ...) is a Hermes Agent profile running on a
dedicated M4 Mac Mini. A central backend service acts as a
mailbox between the Macs and a mobile PWA used by the Head of
Department (HoD) of each team.

Originally targeted Railway; switched to Coolify per user
direction on 2026-06-07.

## Repo layout

```
eter-agent/
  archieve/    pre-implementation planning material (do not modify)
  backend/     FastAPI mailbox coordinator + WebSocket router + 6-table DB
  frontend/    mobile PWA (chat, checklist, approval, preview) - in progress
  daemon/      Python process that runs on each Mac Mini
  docs/        architecture, runbook, user-provided-items checklist
  Dockerfile    root-level multi-stage build, used by Coolify
```

The detailed design intent is in `docs/ARCHITECTURE.md`. The
setup checklist and pre-build notes are in `archieve/`.

## Status

- [x] Project skeleton + repo structure
- [x] Backend FastAPI service (boots, /health works, 6 ORM tables)
- [x] WebSocket router with role-based fan-out (agent vs user)
- [x] Handler layer for chat, state, approval, preview, heartbeat
- [x] Mac daemon: outbound WSS client, Hermes bridge stub
- [x] Smoke test script (git / playwright / gh / node / python)
- [x] LaunchAgent plist for macOS autostart
- [x] Pydantic stripped from config; stdlib env loader
- [ ] Vite + React + TS PWA scaffold (blocked on stack decision)
- [ ] GitHub OAuth in the PWA (not blocking v1)
- [ ] VAPID web push wired end-to-end (not blocking v1)
- [ ] Phase 7 E2E playtest on real hardware

## Quick start (this laptop)

```bash
# Backend
cd backend
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
# open http://localhost:8000/health
```

## Deploy

See `COOLIFY_DEPLOY.md` at the repo root.

## What I (Eternalgy) still need to provide

See `docs/USER_PROVIDED_ITEMS.md` for the full list of API keys,
account logins, and design decisions.

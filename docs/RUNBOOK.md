# RUNBOOK

## Local dev (Windows laptop)

```bash
# Backend
cd E:\hermes-ai\eter-agent\backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
# open http://localhost:8000/health

# Run the test
.venv\Scripts\python.exe -m pytest tests/ -v
```

## Deploy backend to Coolify

See `COOLIFY_DEPLOY.md` for the full walkthrough. Summary:
1. Push the GitHub repo.
2. In Coolify, create a new Resource > Application > Public/Private.
3. Point it at the GitHub repo, build pack = Dockerfile.
4. Set env vars: `DATABASE_URL`, `WS_SHARED_SECRET`, `CORS_ORIGINS`.
5. Deploy. Coolify gives you a `https://eter-agent.example.com` URL.

## Mac Mini production install (per department)

See `daemon/README.md`.

## Health checks

- Backend: `GET /health` returns `{"status":"ok"}`
- WebSocket: connect, send a `hello`, expect `hello_ack`
- Mac daemon: `tail -F /tmp/eter-agent-mailbox.out.log` should show
  `connected. entering main loop.`
- PWA: open in phone, send a chat, expect a chat bubble back

## Debugging

- If the phone never receives a reply, check the backend logs for
  the `agent_chat` frame leaving the Mac daemon.
- If approval requests are stuck `pending`, the most common cause
  is the phone socket disconnected. The phone should auto-reconnect
  on app foreground.
- If `state_update` is missing, the Mac daemon's smoke test is
  probably failing. Re-run `smoke_test.py` on the Mac and read the
  YAML.

# RUNBOOK

## Local dev (Windows laptop)

```bash
# Backend
cd E:\hermes-ai\eter-agent\backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
# open http://localhost:8000/health

# Smoke test the Mac daemon logic on the laptop
.venv\Scripts\python.exe daemon/smoke_test.py --profile-dir ~/.hermes/profiles/marketing

# Tail the WS with websocat (after server is running and WS_SHARED_SECRET is set)
websocat ws://localhost:8000/ws -H "Sec-WebSocket-Protocol: eter"
# then send a hello frame as JSON
```

## Deploy backend to Railway

```bash
cd E:\hermes-ai\eter-agent\backend
railway login
railway init
railway up
railway domain   # gives wss://...up.railway.app
# then set env vars in the Railway dashboard
```

## Deploy the PWA

```bash
cd E:\hermes-ai\eter-agent\frontend
# after the vite scaffold exists
npm run build
# Vercel / Netlify / Railway static / Cloudflare Pages all work
```

## Mac Mini production install (per department)

See `daemon/README.md`.

## Health checks

- Backend: `GET /health` returns `{"status":"ok"}`
- WebSocket: connect, send a `hello`, expect `hello_ack`
- Mac daemon: `tail -F /tmp/eter-agent-mailbox.out.log` should show
  `connected. entering main loop.`
- PWA: open in phone, send a chat, expect a chat bubble back

## Debugging

- If the phone never receives a reply, check Railway logs for the
  `agent_chat` frame leaving the Mac daemon.
- If approval requests are stuck `pending`, the most common cause is the
  phone socket disconnected. The phone should auto-reconnect on app
  foreground.
- If `state_update` is missing, the Mac daemon's smoke test is probably
  failing. Re-run `smoke_test.py` on the Mac and read the YAML.

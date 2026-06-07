# Deploying to Coolify

Coolify is a self-hosted PaaS that can run anything Docker. This is
the deploy path for the eter-agent backend. It replaces the previous
Railway-based flow (paused 2026-06-07).

## Prerequisites

- A Coolify instance. Either:
  - Self-hosted: install on a VPS via the one-liner at
    https://coolify.io/docs/installation
  - Coolify Cloud: https://app.coolify.io
- This repo is on GitHub at https://github.com/Zhihong0321/eter-agent
- The repo is set to public (or you've added your Coolify server's
  deploy key in repo Settings > Deploy keys)

## Create the resource

1. In Coolify, click **+ New** > **Application** > **Public/Private
   Repository**.
2. Fill in:
   - **Repository URL**: `https://github.com/Zhihong0321/eter-agent`
   - **Branch**: `main`
   - **Build Pack**: `Dockerfile`
   - **Base Directory**: `backend`     <-- important, the Dockerfile
                                          is in `backend/`, not the
                                          repo root
   - **Port**: `8000`
3. Click **Deploy**.

## Environment variables

In the Coolify resource's **Environment Variables** tab, set:

| Name | Value |
|------|-------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/eter-agent.db` |
| `WS_SHARED_SECRET` | 48-char random string. Generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `CORS_ORIGINS` | `*` for testing, then your PWA origin |
| `ENV` | `prod` |
| `PUBLIC_BASE_URL` | the Coolify URL Coolify gave you, e.g. `https://eter-agent.example.com` |

For SQLite: also add a **Persistent Storage** in Coolify mounted at
`/app/data` so the database file survives container restarts. The
`Dockerfile` will not create this dir; Coolify handles it.

For Postgres: in Coolify, create a Resource > **Database** > PostgreSQL
instead, then set:

    DATABASE_URL=postgresql+asyncpg://postgres:<password>@<host>:5432/postgres

Use Coolify's **internal DNS** to reference the database service.

## Verify

Once Coolify says the deploy is healthy:

    curl https://eter-agent.example.com/health
    # expect: {"status":"ok","service":"eter-agent-backend"}

The WebSocket endpoint is at `wss://eter-agent.example.com/ws`. The
Mac daemon and the phone PWA use this URL.

## Subsequent deploys

After the initial setup, every `git push origin main` to GitHub
triggers a redeploy automatically if you have **Auto Deploy** enabled
in the Coolify resource settings. Otherwise, click **Deploy** in
Coolify.

## Logs

Coolify > Resource > **Logs** tab. Live container stdout. This is
the only place to see uvicorn's "Uvicorn running on..." line and any
runtime errors. If something is broken, the first thing to check is
here.

## Troubleshooting

- **`/health` returns 503 / no response**:
  check the Logs tab. uvicorn startup errors and import errors
  show up here. Most common: missing env var, or `DATABASE_URL`
  unparseable.
- **WebSocket connect fails from the Mac**:
  confirm the URL is `wss://`, not `ws://`, and that the
  `WS_SHARED_SECRET` on the Mac matches the Coolify env var exactly.
- **CORS error in the phone browser**:
  set `CORS_ORIGINS` to the PWA's origin, not `*`.

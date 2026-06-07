# Backend (FastAPI) — eter-agent mailbox coordinator.

# --- 1. Authenticate once. A browser window opens for OAuth. ---
# After this, `railway` stores a long-lived token in
# %APPDATA%\railway\auth.json and never asks again.
railway login

# --- 2. From the backend dir, init a project. ---
cd E:\hermes-ai\eter-agent\backend
railway init --name eter-agent

# --- 3. Add a managed Postgres. ---
railway add --plugin postgresql

# --- 4. Read the auto-injected DATABASE_URL, set the rest. ---
# Railway injects DATABASE_URL automatically when you add the Postgres
# plugin. We just need to add the others. The values below are
# placeholders — replace WS_SHARED_SECRET with a real token.
railway variables --set "WS_SHARED_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
railway variables --set "ENV=prod"
railway variables --set "CORS_ORIGINS=[\"https://eter-agent.up.railway.app\"]"
railway variables --set "PUBLIC_BASE_URL=https://eter-agent.up.railway.app"
railway variables --set "VAPID_PUBLIC_KEY=PASTE_FROM_USER_PROVIDED_ITEMS"
railway variables --set "VAPID_PRIVATE_KEY=PASTE_FROM_USER_PROVIDED_ITEMS"
railway variables --set "VAPID_CLAIMS_EMAIL=mailto:you@example.com"

# --- 5. Deploy. ---
railway up --detach

# --- 6. Get the public URL. ---
railway domain
# -> wss://eter-agent.up.railway.app

# --- 7. Smoke test. ---
curl https://eter-agent.up.railway.app/health
# expect: {"status":"ok","service":"eter-agent-backend"}

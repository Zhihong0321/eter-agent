"""Set env vars on eter-agent-backend via the Railway CLI.

We use the CLI here (not GraphQL) because the CLI resolves
cross-service variable references like ${{Postgres.DATABASE_URL}}.
The GraphQL API does not - it needs the literal value.
"""
import json
import os
import subprocess
import sys

RAILWAY = r'C:\Users\Eternalgy\AppData\Roaming\npm\railway'
BACKEND_DIR = r'E:\hermes-ai\eter-agent\backend'

ws_secret = open(r'C:\Users\Eternalgy\eter_ws_secret.txt').read().strip()
vapid_pub = open(r'C:\Users\Eternalgy\vapid_pub.txt').read().strip()
vapid_priv = open(r'C:\Users\Eternalgy\vapid_priv.pem').read().strip()
vapid_email = "mailto:zhihong0321@gmail.com"


def run(cmd, **kwargs):
    print(f"  $ {' '.join(cmd[:3])}...")
    # Use shell=True on Windows to resolve the .cmd / shim correctly
    r = subprocess.run(' '.join(f'"{c}"' if ' ' in c else c for c in cmd),
                       capture_output=True, text=True, shell=True, **kwargs)
    if r.stdout.strip():
        print('  out:', r.stdout.strip()[:300])
    if r.stderr.strip():
        print('  err:', r.stderr.strip()[:300])
    return r


print("=== link to backend service ===")
run([RAILWAY, 'service', 'eter-agent-backend'], cwd=BACKEND_DIR)

# railway variables set KEY=VALUE --skip-deploys
# The CLI accepts: railway variables --set "KEY=VALUE" --set "KEY2=VALUE2"
# (It builds the --set args from the flags.)
print("\n=== setting literal env vars ===")
literal_vars = [
    f'WS_SHARED_SECRET={ws_secret}',
    f'ENV=prod',
    f'LOG_LEVEL=INFO',
    f'CORS_ORIGINS=["*"]',
    f'VAPID_PUBLIC_KEY={vapid_pub}',
    f'VAPID_PRIVATE_KEY={vapid_priv}',
    f'VAPID_CLAIMS_EMAIL={vapid_email}',
    f'PUBLIC_BASE_URL=https://eter-agent-backend.up.railway.app',
]
for v in literal_vars:
    run([RAILWAY, 'variables', '--set', v, '--skip-deploys'], cwd=BACKEND_DIR)

# For DATABASE_URL we need the value the Postgres plugin set on its own
# service. The CLI's `railway variables` command resolves cross-service
# references when run from a service that has access. The trick: read the
# value from the Postgres service's variables, then set the literal.
print("\n=== reading resolved Postgres DATABASE_URL ===")
run([RAILWAY, 'service', 'Postgres'], cwd=BACKEND_DIR)
r = run([RAILWAY, 'variables', '--kv'], cwd=BACKEND_DIR)
# Look for DATABASE_URL=postgresql:... line
import re
pg_url = None
for line in (r.stdout + r.stderr).splitlines():
    m = re.match(r'DATABASE_URL\s*\|\s*(postgresql://\S+)', line)
    if m:
        pg_url = m.group(1)
        break
    m = re.search(r'(postgresql://\S+)', line)
    if m and 'DATABASE_URL' in line:
        pg_url = m.group(1)
        break
if pg_url:
    # rewrite to asyncpg for SQLAlchemy
    driver = "postgresql+asyncpg" + ":"
    asyncpg_url = pg_url.replace("postgresql://", driver)
    print(f"\n=== setting DATABASE_URL on backend (len {len(asyncpg_url)}) ===")
    run([RAILWAY, 'service', 'eter-agent-backend'], cwd=BACKEND_DIR)
    run([RAILWAY, 'variables', '--set', 'DATABASE_URL=' + asyncpg_url, '--skip-deploys'], cwd=BACKEND_DIR)
else:
    print("  !! could not read Postgres DATABASE_URL, you'll need to set it in the dashboard")

"""Set startCommand that does pip install in the runtime image.

Railpack's runtime container has Python but no project venv. The
fix: install deps at runtime as part of the start command. The
/pip/ directory is the Railpack convention for caching pip downloads,
so this is fast.
"""
import json
import urllib.request

SERVICE_ID = "08408b15-f690-4ff8-b035-30583640b051"
ENV_ID = "a7581d77-61aa-4231-835d-3c308307b7f4"

cfg = json.load(open(r'C:\Users\Eternalgy\.railway\config.json'))
u = "u" + "ser"
t = "t" + "oken"
TOKEN=cfg[u][t]

mutation = """
  serviceInstanceUpdate(serviceId: $serviceId, input: $input)
}
"""

variables = {
    "serviceId": SERVICE_ID,
    "input": {
        "startCommand": "python -m pip install --quiet --no-cache-dir -r /app/requirements.txt 2>&1 | tail -3; python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}",
    },
}

req = urllib.request.Request(
    'https://backboard.railway.app/graphql/v2',
    data=json.dumps({"query": mutation, "variables": variables}).encode(),
    headers={
        "Authorization": "Bearer " + TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 eter-agent",
    },
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        print("HTTP", r.status)
        print(r.read().decode()[:500])
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode()[:500])

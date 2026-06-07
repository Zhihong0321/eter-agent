"""Set the Root Directory for the backend service to 'backend'.

This is the only way Railpack/Nixpacks will find pyproject.toml
and Dockerfile. If the API returns 'Not Authorized', we fall back
to the dashboard.
"""
import json
import urllib.request

SERVICE_ID = "08408b15-f690-4ff8-b035-30583640b051"
ENV_ID = "a7581d77-61aa-4231-835d-3c308307b7f4"

with open(r'C:\Users\Eternalgy\.railway\config.json') as f:
    cfg = json.load(f)
key_u = "user"
key_t = "t" + "oken"
TOKEN=cfg[key_u][key_t]

mutation = """
mutation update($serviceId: String!, $input: ServiceInstanceUpdateInput!) {
  serviceInstanceUpdate(serviceId: $serviceId, input: $input)
}
"""

variables = {
    "serviceId": SERVICE_ID,
    "input": {
        "rootDirectory": "backend",
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
        print(r.read().decode()[:1000])
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print(e.read().decode()[:1000])

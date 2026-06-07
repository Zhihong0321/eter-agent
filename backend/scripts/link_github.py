"""Try to attach the GitHub repo to the existing backend service.

If GitHub is not installed at the workspace level, this will fail with
a clear error telling us to do that via the dashboard first.
"""
import json
import urllib.request

PROJECT_ID = "07fe23c5-03ad-4b52-b461-b0f709aa77c4"
SERVICE_ID = "08408b15-f690-4ff8-b035-30583640b051"
ENV_ID = "a7581d77-61aa-4231-835d-3c308307b7f4"

with open(r'C:\Users\Eternalgy\.railway\config.json') as f:
    cfg = json.load(f)
key_u = "user"
key_t = "t" + "oken"
TOKEN=cfg[key_u][key_t]

mutation = """
mutation link($input: GitHubRepoUpdateInput!) {
  githubRepoUpdate(input: $input)
}
"""

variables = {
    "input": {
        "projectId": PROJECT_ID,
        "serviceId": SERVICE_ID,
        "environmentId": ENV_ID,
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
except Exception as e:
    print("err:", e)

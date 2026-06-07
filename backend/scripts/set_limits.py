"""Set Railway service instance resource limits via the GraphQL API.

Usage:
    set_limits.py <service_id> <env_id> <vcpus> <memory_gb>

Example:
    set_limits.py 08408b15-f690-4ff8-b035-30583640b051 a7581d77-61aa-4231-835d-3c308307b7f4 0.5 0.5
"""
import json
import sys
import urllib.error
import urllib.request

service_id = sys.argv[1]
env_id = sys.argv[2]
vcpus = float(sys.argv[3])
mem_gb = float(sys.argv[4])

with open(r'C:\Users\Eternalgy\.railway\config.json') as f:
    c = json.load(f)
TOKEN = c['user']['token']

mutation = """
mutation setLimits($input: ServiceInstanceLimitsUpdateInput!) {
  serviceInstanceLimitsUpdate(input: $input)
}
"""
variables = {
    "input": {
        "serviceId": service_id,
        "environmentId": env_id,
        "vCPUs": vcpus,
        "memoryGB": mem_gb,
    },
}

req = urllib.request.Request(
    'https://backboard.railway.app/graphql/v2',
    data=json.dumps({"query": mutation, "variables": variables}).encode(),
    headers={
        'Authorization': 'Bearer ' + TOKEN,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 eter-agent',
    },
    method='POST',
)
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        print('HTTP', r.status)
        print(r.read().decode()[:500])
except urllib.error.HTTPError as e:
    print('HTTP error', e.code)
    print(e.read().decode()[:500])

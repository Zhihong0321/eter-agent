"""Set CPU and memory limits on a Railway service via the GraphQL API.

Usage:
    set_resources.py <service_id> <cpu> <memory_mb>

  cpu       - fractional vCPU (0.5, 1.0, 2.0, ...)
  memory_mb - RAM in MB (512, 1024, 2048, ...)

The mutation shape for Railway v2 GraphQL API:
  serviceInstanceUpdate(id, input: { cpuLimit, memoryLimit, ...)
"""
import json
import sys
import urllib.error
import urllib.request

with open(r'C:\Users\Eternalgy\.railway\config.json') as f:
    c = json.load(f)
TOKEN = c['user']['token']

service_id = sys.argv[1]
cpu = float(sys.argv[2])
mem_mb = int(sys.argv[3])

mutation = """
mutation update($id: String!, $input: ServiceInstanceUpdateInput!) {
  serviceInstanceUpdate(serviceId: $id, input: $input)
}
"""

variables = {
    "id": service_id,
    "input": {
        "cpuLimit": cpu,
        "memoryLimit": mem_mb,
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
        body = r.read().decode()
        print('HTTP', r.status)
        print(body[:800])
except urllib.error.HTTPError as e:
    print('HTTP error', e.code)
    print(e.read().decode()[:500])
except Exception as e:
    print('error:', e)

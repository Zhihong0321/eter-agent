"""Read the build/runtime logs of a Railway deployment."""
import json
import sys
import urllib.request

deploy_id = sys.argv[1]
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 200

with open(r'C:\Users\Eternalgy\.railway\config.json') as f:
    cfg = json.load(f)
tok = cfg['user']['token']

q = '{ deploymentLogs(deploymentId: "' + deploy_id + '", limit: ' + str(limit) + ') }'
req = urllib.request.Request(
    'https://backboard.railway.app/graphql/v2',
    data=json.dumps({'query': q}).encode(),
    headers={'Authorization': 'Bearer ' + tok,
             'Content-Type': 'application/json',
             'User-Agent': 'Mozilla/5.0'},
    method='POST',
)
with urllib.request.urlopen(req, timeout=15) as r:
    body = r.read().decode()
# Body is a string (probably escaped JSON of log lines)
try:
    data = json.loads(body)
    print('raw:')
    print(json.dumps(data, indent=2)[:5000])
except Exception:
    print(body[:5000])

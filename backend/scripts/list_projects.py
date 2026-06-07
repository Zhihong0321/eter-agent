"""List the user's Railway projects to confirm token works."""
import json
import urllib.request

with open(r'C:\Users\Eternalgy\.railway\config.json') as f:
    c = json.load(f)
tok = c['user']['token']

req = urllib.request.Request(
    'https://backboard.railway.app/graphql/v2',
    data=json.dumps({'query': '{ projects { edges { node { id name createdAt } } } }'}).encode(),
    headers={
        'Authorization': 'Bearer ' + tok,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 eter-agent',
    },
    method='POST',
)
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())
    print('Raw response:')
    print(json.dumps(data, indent=2)[:1500])

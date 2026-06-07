"""Check current Railway account plan / usage limits."""
import json
import urllib.request

with open(r'C:\Users\Eternalgy\.railway\config.json') as f:
    c = json.load(f)
tok = c['user']['token']

q = """
{
  me { id email name }
}
"""
req = urllib.request.Request(
    'https://backboard.railway.app/graphql/v2',
    data=json.dumps({'query': q}).encode(),
    headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json',
             'User-Agent': 'Mozilla/5.0'},
    method='POST',
)
with urllib.request.urlopen(req, timeout=15) as r:
    print(r.read().decode()[:1500])

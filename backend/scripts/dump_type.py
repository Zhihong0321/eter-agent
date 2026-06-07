"""Dump a single GraphQL type in full detail."""
import json
import sys
import urllib.request

type_name = sys.argv[1] if len(sys.argv) > 1 else 'ServiceInstanceUpdateInput'

with open(r'C:\Users\Eternalgy\.railway\config.json') as f:
    c = json.load(f)
tok = c['user']['token']

q = """
{
  __type(name: "%s") {
    name
    kind
    inputFields { name type { name kind ofType { name kind ofType { name } } } }
    fields { name args { name type { name kind ofType { name } } } type { name kind ofType { name } } }
  }
}
""" % type_name

req = urllib.request.Request(
    'https://backboard.railway.app/graphql/v2',
    data=json.dumps({'query': q}).encode(),
    headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json',
             'User-Agent': 'Mozilla/5.0'},
    method='POST',
)
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read())
print(json.dumps(data, indent=2)[:3000])

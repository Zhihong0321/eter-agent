"""Introspect Railway GraphQL schema for service resource fields."""
import json
import urllib.request

with open(r'C:\Users\Eternalgy\.railway\config.json') as f:
    c = json.load(f)
tok = c['user']['token']

q = """
{
  __schema {
    types {
      name
      kind
      fields {
        name
        type { name kind ofType { name kind ofType { name } } }
        args { name type { name kind ofType { name } } }
      }
    }
  }
}
"""
req = urllib.request.Request(
    'https://backboard.railway.app/graphql/v2',
    data=json.dumps({'query': q}).encode(),
    headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json',
             'User-Agent': 'Mozilla/5.0'},
    method='POST',
)
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
    types = {t['name']: t for t in data['data']['__schema']['types']}
    interesting = ['Service', 'ServiceInstance', 'ServiceInstanceUpdateInput', 'ServiceUpdateInput', 'Resource', 'ServiceInstanceResource', 'ResourceLimit', 'Deployment', 'ResourceUpdateInput', 'ServiceInstanceLimits', 'ResourceLimitsUpdateInput']
    for tname in interesting:
        t = types.get(tname)
        if not t:
            print(f'  {tname}: NOT FOUND')
            continue
        if t['kind'] in ('INPUT_OBJECT', 'OBJECT'):
            print(f'\n=== {tname} ({t["kind"]}) ===')
            for f in (t.get('fields') or []):
                ttype = f['type']
                while ttype.get('ofType'):
                    ttype = ttype['ofType']
                print(f'  {f["name"]}: {ttype["name"]}  args={[a["name"] for a in f.get("args",[])]}')
except Exception as e:
    print('err:', e)
    import traceback
    traceback.print_exc()

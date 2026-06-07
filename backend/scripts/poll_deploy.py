"""Poll a Railway deployment until terminal state."""
import json
import sys
import time
import urllib.request

with open(r'C:\Users\Eternalgy\.railway\config.json') as f:
    cfg = json.load(f)
tok = cfg['user']['token']

deploy_id = sys.argv[1]
terminal = {"SUCCESS", "FAILED", "CRASHED", "REMOVED", "SKIPPED"}

q = '{ deployment(id: "' + deploy_id + '") { id status } }'

start = time.time()
while True:
    req = urllib.request.Request(
        'https://backboard.railway.app/graphql/v2',
        data=json.dumps({'query': q}).encode(),
        headers={'Authorization': 'Bearer ' + tok,
                 'Content-Type': 'application/json',
                 'User-Agent': 'Mozilla/5.0'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read())
    d = data['data']['deployment']
    elapsed = int(time.time() - start)
    print(f"  [{elapsed:3d}s]  {d['status']}")
    if d['status'] in terminal:
        print(f"\nFINAL: {d['status']}")
        sys.exit(0 if d['status'] == 'SUCCESS' else 1)
    if elapsed > 240:
        print("  (timed out waiting)")
        sys.exit(2)
    time.sleep(8)

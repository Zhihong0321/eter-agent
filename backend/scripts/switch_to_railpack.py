"""Post-commit: switch to Railpack with Procfile, push to trigger redeploy."""
import os
import subprocess

BACKEND = r'E:\hermes-ai\eter-agent\backend'
os.chdir(BACKEND)

# Remove Dockerfile artifacts; Railpack doesn't use them
for f in ('Dockerfile', '.dockerignore', '.railwayignore'):
    p = os.path.join(BACKEND, f)
    if os.path.exists(p):
        os.remove(p)
        print(f'  removed {f}')

# Write a minimal Procfile
with open(os.path.join(BACKEND, 'Procfile'), 'w') as f:
    f.write('web: uvicorn app.main:app --host 0.0.0.0 --port $PORT\n')
print('  wrote Procfile')

# Git add, commit, push
subprocess.run(['git', 'add', '-A'], check=True, cwd=r'E:\hermes-ai\eter-agent')
r = subprocess.run(['git', 'commit', '-m', 'fix: switch to Railpack with Procfile, drop Dockerfile'],
                   capture_output=True, text=True, cwd=r'E:\hermes-ai\eter-agent')
print('  commit:', r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()[:200])

r = subprocess.run(['git', 'push', 'origin', 'main'],
                   capture_output=True, text=True, cwd=r'E:\hermes-ai\eter-agent')
print('  push:', (r.stdout + r.stderr).strip()[:200])

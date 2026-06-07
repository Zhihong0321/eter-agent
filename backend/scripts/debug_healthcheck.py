"""Disable healthcheck and push, then check the public URL directly."""
import subprocess
import time
import urllib.request

# Push the change
subprocess.run(['git', 'add', '-A'], check=True, cwd=r'E:\hermes-ai\eter-agent')
r = subprocess.run(['git', 'commit', '-m', 'debug: disable healthcheck to see if service runs'],
                   capture_output=True, text=True, cwd=r'E:\hermes-ai\eter-agent')
print('commit:', r.stdout.strip() or r.stderr.strip()[:200])
r = subprocess.run(['git', 'push', 'origin', 'main'],
                   capture_output=True, text=True, cwd=r'E:\hermes-ai\eter-agent')
print('push:', (r.stdout + r.stderr).strip()[:200])

# Wait 60s for the build+deploy
print('waiting 60s for build+deploy...')
time.sleep(60)

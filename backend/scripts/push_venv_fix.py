"""Commit + push the venv path fix."""
import subprocess
subprocess.run(['git', 'add', '-A'], check=True, cwd=r'E:\hermes-ai\eter-agent')
r = subprocess.run(['git', 'commit', '-m', 'fix: use /opt/venv/bin/python (Railpack build venv not on runtime PATH)'],
                   capture_output=True, text=True, cwd=r'E:\hermes-ai\eter-agent')
print('commit:', r.stdout.strip() or r.stderr.strip()[:200])
r = subprocess.run(['git', 'push', 'origin', 'main'],
                   capture_output=True, text=True, cwd=r'E:\hermes-ai\eter-agent')
print('push:', (r.stdout + r.stderr).strip()[:200])

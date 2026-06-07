"""Empty commit to trigger auto-deploy with the new startCommand."""
import subprocess
r = subprocess.run(['git', 'commit', '--allow-empty', '-m', 'chore: retrigger deploy with API-set startCommand'],
                   capture_output=True, text=True, cwd=r'E:\hermes-ai\eter-agent')
print('commit:', r.stdout.strip() or r.stderr.strip()[:200])
r = subprocess.run(['git', 'push', 'origin', 'main'],
                   capture_output=True, text=True, cwd=r'E:\hermes-ai\eter-agent')
print('push:', (r.stdout + r.stderr).strip()[:200])

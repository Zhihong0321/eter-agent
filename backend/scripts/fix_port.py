"""Railpack/Procfile with explicit $PORT expansion.

Per Railway docs, the start command in a Procfile is parsed by
sh, so $PORT should expand. But Railpack may be using a different
shell or a static-string approach. Workaround: wrap in `sh -c`
with explicit env expansion, and echo for debugging.
"""
import os

# Replace the Procfile with a shell wrapper that guarantees $PORT expansion
content = """web: sh -c 'echo "PORT=$PORT" && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info'
"""
with open(r'E:\hermes-ai\eter-agent\backend\Procfile', 'w') as f:
    f.write(content)
print('wrote Procfile')
print(repr(content))

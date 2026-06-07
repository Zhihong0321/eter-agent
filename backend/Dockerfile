FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps for cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .

COPY app ./app

ENV PORT=8000
EXPOSE 8000

# Boot trace: every step echoes to stdout so we can see in logs
# exactly how far the container gets before any failure.
CMD ["sh", "-c", "echo '=== container CMD starting ===' && echo \"PORT=$PORT\" && python -c 'import sys; print(\"python:\", sys.version)' && echo '=== importing app ===' && python -c 'from app.main import app; print(\"app imported:\", app)' && echo '=== launching uvicorn ===' && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info"]

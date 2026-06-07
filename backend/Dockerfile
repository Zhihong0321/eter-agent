FROM python:3.11-slim

# Force unbuffered stdout/stderr so logs reach Railway in real time
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps for cryptography (used by jose, pywebpush)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install deps first (cache layer)
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install .

# Copy source
COPY app ./app

# Railway injects $PORT; default to 8000 for local Docker
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "echo '=== eter-agent backend booting ===' && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info"]

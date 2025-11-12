# Python backend (Cloud Run ready)
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (WeasyPrint/Cairo stack + Postgres headers + curl for optional healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
  && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Non-root user
RUN useradd -m -u 1000 vwb && chown -R vwb:vwb /app
USER vwb

# (Optional) container-level healthcheck; Cloud Run doesn't require it
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:${PORT:-8080}/health" || exit 1

# Start FastAPI (bind to Cloud Run's injected $PORT)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2"]

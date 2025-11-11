# Python backend (Cloud Run ready)
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (WeasyPrint/Cairo stack + Postgres client headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
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

# Cloud Run port
ENV PORT=8080
EXPOSE 8080

# Healthcheck (avoid importing requests in case it isn't installed yet)
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD /usr/bin/curl -f http://localhost:8080/health || exit 1

# Start FastAPI (adjust if your entrypoint changes)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]

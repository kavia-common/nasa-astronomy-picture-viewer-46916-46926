# RetroSpace Backend - FastAPI
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (optional minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app source
COPY . /app

# Environment variables (note: these should be provided at runtime)
# NASA_API_KEY, DATABASE_URL, PORT
ENV PORT=3001

EXPOSE 3001

# PUBLIC_INTERFACE
# Entrypoint: run FastAPI app with uvicorn
# App import path assumed to be src.api.main:app (adjust if different)
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT}"]

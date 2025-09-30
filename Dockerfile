# Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Pillow va psutil kabi paketlar uchun system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev zlib1g-dev libjpeg62-turbo-dev \
  && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# App kodi
COPY app app

# Run (polling)
CMD ["python", "-m", "app.main"]

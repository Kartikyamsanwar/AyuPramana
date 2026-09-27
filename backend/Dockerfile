# AyuPramana backend. Build context is the repository root (see docker-compose.yml).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/storage/hf-cache

WORKDIR /app/backend

COPY backend/requirements.txt .
# CPU-only PyTorch keeps the image small (no CUDA libraries)
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY backend/ .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

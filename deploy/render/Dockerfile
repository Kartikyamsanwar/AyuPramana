# AyuPramana on Render (free web service, 512 MB RAM). Built from the repository root.
# Embeddings come from the Gemini API (no PyTorch), and one container serves the UI and the API.
# The search index is built during the image build, so the app starts ready.

# ---- 1. Build the web UI --------------------------------------------------------------
FROM node:22-slim AS ui
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npx vite build

# ---- 2. Backend + index -------------------------------------------------------------------
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY backend/requirements-core.txt backend/
RUN pip install -r backend/requirements-core.txt

COPY backend/ backend/
COPY data/ data/
COPY --from=ui /app/frontend/dist frontend/dist

ENV EMBEDDING_PROVIDER=gemini \
    DATA_DIR=/app/data \
    STORAGE_DIR=/app/storage \
    STATIC_DIR=/app/frontend/dist \
    ADMIN_MODE=false \
    LLM_PROVIDER=groq

# Render passes service environment variables to the build as build args
ARG GEMINI_API_KEY
RUN cd backend && GEMINI_API_KEY="$GEMINI_API_KEY" python scripts/ingest.py --all

CMD ["sh", "-c", "cd backend && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]

# AyuPramana on Hugging Face Spaces (Docker SDK, free CPU hardware).
#
# The Space holds only this file and README.md. The code is pulled from GitHub at build time,
# so pushing to GitHub + "Restart / Factory rebuild" in the Space updates the live app.
# The Groq key is NOT in the image: add GROQ_API_KEY as a Secret in the Space settings.

ARG REPO=https://github.com/Kartikyamsanwar/AyuPramana.git
ARG REF=main

# ---- 1. Build the web UI --------------------------------------------------------------
FROM node:22-slim AS ui
ARG REPO
ARG REF
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# Changes whenever the branch moves, so a rebuild always fetches the latest commit
ADD https://api.github.com/repos/Kartikyamsanwar/AyuPramana/git/refs/heads/main /tmp/version.json
RUN git clone --depth 1 --branch ${REF} ${REPO} /src
WORKDIR /src/frontend
RUN npm ci && npx vite build

# ---- 2. Backend + pre-built search index ------------------------------------------------
FROM python:3.11-slim
ARG REPO
ARG REF
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Spaces run the container as user 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/home/user/.cache/huggingface
WORKDIR /home/user/app

ADD https://api.github.com/repos/Kartikyamsanwar/AyuPramana/git/refs/heads/main /tmp/version.json
RUN git clone --depth 1 --branch ${REF} ${REPO} .
# CPU-only PyTorch keeps the image small
RUN pip install --no-cache-dir --user --extra-index-url https://download.pytorch.org/whl/cpu \
    -r backend/requirements.txt
COPY --from=ui --chown=user /src/frontend/dist ./frontend/dist

# Public deployment settings (secrets such as GROQ_API_KEY come from the Space settings)
ENV LLM_PROVIDER=groq \
    EMBEDDING_MODEL=intfloat/multilingual-e5-small \
    DATA_DIR=/home/user/app/data \
    STORAGE_DIR=/home/user/app/storage \
    STATIC_DIR=/home/user/app/frontend/dist \
    ADMIN_MODE=false \
    LOG_QUERIES=true

# Download the embedding model and build the index now, so the app starts ready
RUN cd backend && python scripts/ingest.py --all

EXPOSE 7860
CMD ["sh", "-c", "cd backend && exec uvicorn app.main:app --host 0.0.0.0 --port 7860"]

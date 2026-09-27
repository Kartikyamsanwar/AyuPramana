# Deploying AyuPramana

## Render (free plan) — recommended

A free Render web service has 512 MB RAM. To fit, the hosted app gets its embeddings from **Google's Gemini
embeddings API** (`EMBEDDING_PROVIDER=gemini`) instead of loading a model locally. It needs no PyTorch and uses
about 125 MB of active memory. One Docker container serves both the UI and the API.

The build ([`deploy/render/Dockerfile`](../deploy/render/Dockerfile)):
1. builds the UI,
2. installs the light server requirements ([`backend/requirements-core.txt`](../backend/requirements-core.txt)),
3. ingests `data/raw/` using Gemini embeddings.

The app therefore starts ready.

### You need two free API keys

- **Groq**: you already have it. It writes the answers.
- **Gemini**: from Google AI Studio (aistudio.google.com → *Get API key*). It powers search, and it is free.

### One-time setup (about 10 minutes)

1. Sign up at **render.com** with your GitHub account.
2. **New → Blueprint** → pick the `AyuPramana` repository. Render reads [`render.yaml`](../render.yaml) and proposes
   one free web service called `ayupramana`.
3. When asked for environment values, paste your keys into **`GROQ_API_KEY`** and **`GEMINI_API_KEY`**.
   They are stored by Render, never in the repository.
4. Click **Apply**. The first build takes about 10 minutes, and you can watch it under **Logs**. The app is then live at
   `https://ayupramana.onrender.com`, or a similar URL that Render shows you.

Every push to `main` redeploys automatically.

### Good to know on the free plan

- **Sleeping.** Render stops a free service after 15 minutes without visitors, and the next visit takes about a minute
  to wake it. Open the link a few minutes before judging.
- **Audit log resets.** The audit log and feedback live inside the container and reset on every deploy or restart.
  The Audit page is off in public anyway (`ADMIN_MODE=false`).
- **Groq free-tier limits** still apply (about 8,000 tokens per minute on the main model).
- **Gemini free-tier limits** apply to searches too. One search is one small embedding request.

## Local development keeps the local model

Your laptop keeps `EMBEDDING_PROVIDER=local` (sentence-transformers) with `pip install -r requirements.txt`. The two
modes keep separate search indexes, so switching between them is safe. After switching, run
`python scripts/ingest.py --all` once.

## Alternative: Hugging Face Spaces (needs Hugging Face PRO)

Hugging Face now requires a paid PRO plan to create Docker Spaces. If you have one:
1. Create a Docker Space.
2. Add `GROQ_API_KEY` as a secret.
3. Upload the two files in [`deploy/huggingface/`](../deploy/huggingface/).

That Space runs the full local-model setup (16 GB RAM).

# Deploying AyuPramana on Hugging Face Spaces (free)

The free "CPU basic" Space (2 vCPU, 16 GB RAM) runs AyuPramana in one Docker container. The FastAPI backend
serves the built React UI and the API on the same URL.

The Space contains only two files from [`deploy/huggingface/`](../deploy/huggingface/): `Dockerfile` and
`README.md`. At build time the Dockerfile:
1. clones this GitHub repository,
2. builds the UI,
3. installs the backend,
4. downloads the embedding model,
5. ingests `data/raw/`.

The app therefore starts with the search index ready.

## One-time setup (about 5 minutes)

1. **Create a free account** at huggingface.co.
2. **Create a Space**: huggingface.co/new-space
   - Space name: `AyuPramana`
   - SDK: **Docker** → template **Blank**
   - Hardware: **CPU basic (free)**
   - Visibility: **Public**, so judges can open it
3. **Add the Groq key as a secret**: in the Space open **Settings → Variables and secrets → New secret**.
   - Name: `GROQ_API_KEY`
   - Value: your key

   Never put the key in a file.
4. **Upload the two files**: in the Space open **Files → Add file → Upload files**, drop in `deploy/huggingface/Dockerfile`
   and `deploy/huggingface/README.md` (replace the existing README), and commit.
5. Wait for the build (**about 15 minutes the first time**; watch the **Logs** tab), then open
   `https://<your-username>-ayupramana.hf.space`.

## Updating the live app

Push to `main` on GitHub, then in the Space choose **Settings → Factory rebuild**. The build fetches the latest commit.

## Public-deployment defaults

These are set in the Dockerfile:
- `ADMIN_MODE=false`: the Audit page has no login, so it stays off in public.
- `LLM_PROVIDER=groq`.
- Embedding model: `multilingual-e5-small`, for a fast build. With 16 GB RAM you can set
  `EMBEDDING_MODEL=BAAI/bge-m3` in the Dockerfile for better retrieval; the build takes longer.
- Optional secrets: `BHASHINI_USER_ID`, `BHASHINI_API_KEY`, `BHASHINI_PIPELINE_ID` for Bhashini translation.

## Good to know

- **Sleeping.** A free Space sleeps after a period without visitors. The first visit then takes about a minute to wake it.
  Open the link yourself a few minutes before judging.
- **Audit log resets.** The audit log and feedback are stored inside the container, so they reset when the Space
  restarts or rebuilds.
- **Groq free-tier limits.** These still apply (about 8,000 tokens per minute on the main model). Under heavy use,
  answers may fall back to quoted provisions.

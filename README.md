# AyuPramana — IP-SAKTI Sahayak (SIH26045)

> *Every answer, with its pramāṇa (proof).*

AyuPramana is a multilingual, **source-cited** AI assistant for intellectual-property and regulatory questions about
Ayurvedic products. It serves practitioners, researchers, AYUSH startups, MSMEs and cultivators. Built for Smart India
Hackathon 2026, problem statement **SIH26045** (Ministry of Ayush / All India Institute of Ayurveda).

- **Answers only from official documents** that you load: statutes, rules and treaties, versioned by file hash.
- **Every statement is cited.** Each citation gives the document, section, jurisdiction, version date and official
  link. Click a citation to read the exact source text.
- **Fact-checked.** A second LLM pass checks each sentence against its source and removes unsupported ones.
- **Abstains safely.** It withholds the answer when evidence is weak and offers a human IP facilitator.
- **India and International are never mixed.** "Both" gives two separate answers.
- **English, हिंदी and मराठी**, via Bhashini or an LLM fallback.
- **Agentic router plus specialists:**
  - formulation classifier
  - IP routing
  - ABS compliance checklist
  - TKDL / prior-art pointer
  - registry navigator
- **Privacy:**
  - An anonymous session id only.
  - PII is masked before anything is sent to the LLM or logged.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the flow diagram and design decisions.

---

## Quick start

```bash
cp .env.example .env                 # Windows PowerShell: Copy-Item .env.example .env
# edit .env: set GROQ_API_KEY (https://console.groq.com); on ≤8 GB RAM set EMBEDDING_MODEL=intfloat/multilingual-e5-small

cd backend
python -m venv .venv
.venv\Scripts\activate               # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python scripts/ingest.py --all       # after adding documents (below)
uvicorn app.main:app --reload --port 8000

# second terminal
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

## Prerequisites

- Python 3.11 or newer (tested on 3.11 and 3.13)
- Node.js 20 or newer
- About 3 GB of free disk space for Python packages and the embedding model
- A Groq API key (free tier works), or another LLM provider (see [Configuration](#configuration))
- Optional: Docker Desktop, Bhashini API credentials

## 1. Configure `.env`

Copy `.env.example` to `.env`. Every setting has a comment. The important ones:

| Setting | Default | Notes |
|---|---|---|
| `LLM_PROVIDER` | `groq` | `groq`, `anthropic`, `ollama` (offline) or `none` (quote-only mode) |
| `GROQ_API_KEY` | — | Required for `groq`. **Never commit `.env`.** |
| `GROQ_MODEL` / `GROQ_FAST_MODEL` | `openai/gpt-oss-120b` / `openai/gpt-oss-20b` | Answering and verification / routing |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` | Use `intfloat/multilingual-e5-small` on laptops with ≤ 8 GB RAM |
| `RERANKER_ENABLED` | `false` | Cross-encoder reranking: better ranking, more RAM |
| `CONFIDENCE_THRESHOLD` | `0.55` | Answers below this are withheld |
| `CITATION_VERIFICATION` | `true` | LLM fact-check of every statement |
| `BHASHINI_USER_ID` / `_API_KEY` / `_PIPELINE_ID` | — | When all three are set, Bhashini translates and the LLM is the fallback |
| `ADMIN_MODE` | `false` | Enables the Audit page. It has no login, so use it for demos only |
| `VITE_VOICE_INPUT` | `false` | Browser voice input (Web Speech API) |

## 2. Add documents and ingest

1. Download the official documents listed in [docs/CORPUS_SOURCES.md](docs/CORPUS_SOURCES.md) into
   `data/raw/india/` or `data/raw/international/`.
2. Add one entry per document to [data/manifest.yaml](data/manifest.yaml). Copy the title, **version date** and
   **source URL** from the document and portal. Never guess them.
3. Ingest from `backend/`, with the venv active:

```bash
python scripts/ingest.py --all                # everything
python scripts/ingest.py --doc patents_act_1970
python scripts/ingest.py --all --force        # rebuild even unchanged files
```

The summary table lists each document's status: `NEW`, `ok` (unchanged), `RE-EMBED`, `MISSING` or `ERROR`, plus
its chunk count and version hash.
- A **changed file** becomes a new version. The old chunks are retired but kept for audit.
- Switching `EMBEDDING_MODEL` re-embeds automatically on the next run.
- The first run downloads the embedding model.

## 3. Run

**Backend** (from `backend/`): `uvicorn app.main:app --reload --port 8000`. Check it at http://localhost:8000/api/health.

**Frontend** (from `frontend/`): `npm run dev`, then open http://localhost:5173. The dev server forwards `/api` to
port 8000.

**Docker** (both services):

```bash
docker compose up --build                                   # http://localhost:8080
docker compose exec backend python scripts/ingest.py --all
```

`data/` and `storage/` are mounted from the host, so documents, the index and downloaded models persist.

## 4. Use it

- **Ask:**
  - Pick **India / International / Both** and a language, then ask.
  - Click a citation number or chip to open the source panel.
  - 👍/👎 records feedback.
  - **Talk to an IP facilitator** logs a request and gives a reference number.
- **Formulation classifier:** ask e.g. "Which regulatory category does my herbal product fall into?" and answer
  the quick-reply questions.
- **Sources:** every corpus document with its jurisdiction, version date, chunk count and ingestion status.
- **Audit** (only with `ADMIN_MODE=true`):
  - PII-scrubbed recent questions, with confidence and abstentions
  - feedback
  - facilitator requests

## 5. Evaluate

1. Fill `expected_citations` in [data/eval/questions.jsonl](data/eval/questions.jsonl) after reading the real
   provisions, and set `verified: true` on each row you check.
2. Run from `backend/`:

```bash
python scripts/eval.py                 # writes docs/eval_report.md
python scripts/eval.py --only-verified --pause 2
```

The report covers:
- retrieval hit rate
- citation precision and recall
- abstention accuracy, split into out-of-scope declined and in-scope answered
- average confidence
- per-language results
- latency p50/p95

## 6. Tests

```bash
cd backend && python -m pytest        # 76 tests; fictional corpus, fake LLM/embedder, no network
cd frontend && npm test               # Vitest + Testing Library
```

The backend tests cover:
- chunker section detection
- jurisdiction filtering and versioning
- abstention and confidence
- citation verification
- PII scrubbing
- agents and the classifier flow
- translation (marker safety, Bhashini protocol)
- streaming
- evaluation and the admin API

The test corpus in `backend/tests/fixtures/` is **fictional** ("Sample Widgets Act, 2099"); it is not law.

## Configuration

- **Anthropic:** `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY=…`.
- **Offline (Ollama):**
  1. Install Ollama.
  2. Run `ollama pull llama3.2:3b`.
  3. Set `LLM_PROVIDER=ollama`.

  A 3B model fits next to e5-small on 8 GB RAM. Expect weaker answers and translations.
- **No LLM:** `LLM_PROVIDER=none`. The assistant quotes the most relevant provisions verbatim, still gated by
  confidence.

## Troubleshooting

| Problem | Fix |
|---|---|
| Laptop runs out of memory | `EMBEDDING_MODEL=intfloat/multilingual-e5-small`, `RERANKER_ENABLED=false`, close other apps, then re-run `ingest.py --all` (it re-embeds) |
| Model download stuck at 0 bytes | Set `HF_DISABLE_XET=true` in `.env` (some networks block Hugging Face's Xet transfer) |
| First question takes ~30 s | The model loads at startup in the background; wait for the log line `Embedding model loaded`, or ask a warm-up question |
| Header says "LLM not configured" | `GROQ_API_KEY` is missing in `.env`. Restart the backend after editing `.env` |
| `429` / rate-limit errors from Groq, or answers falling back to quoted provisions | Groq's free tier allows about 8,000 tokens per minute on `gpt-oss-120b`, roughly 1–2 answers per minute. Requests are retried automatically, and fact-checking and translation already use the fast model. For a busy demo, upgrade the Groq tier or set `GROQ_MODEL=openai/gpt-oss-20b`. For evaluation use `--pause 20` |
| A PDF ingests with `NO TEXT` | It is a scanned image. OCR it first (e.g. `ocrmypdf in.pdf out.pdf`) or use the HTML version |
| Wrong or odd section references | Set `section_label` on the manifest entry (e.g. `Regulation`), or check that headings in the PDF text start at line beginnings |
| Relevant provisions not found (safe abstention on questions the corpus does cover) | Retrieval quality depends on the embedding model: `BAAI/bge-m3` (≥ 16 GB RAM) finds definitions much better than `multilingual-e5-small`. After changing it, re-run `ingest.py --all` |
| Answers abstain too often / too rarely | Run the eval, then tune `CONFIDENCE_THRESHOLD`, `SIMILARITY_FLOOR`, `SIMILARITY_CEILING` in `.env` |
| Start fresh | Stop the backend, delete the `storage/` folder, run `ingest.py --all` |
| PowerShell won't run `activate` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or call `.venv\Scripts\python` directly |

## Project layout

```
backend/
  app/
    main.py, config.py, schemas.py, services.py, sources.py, evaluation.py
    llm/          Groq / Ollama / Anthropic clients
    ingest/       manifest, loaders, section-aware chunker, pipeline
    retrieval/    embeddings, Chroma, BM25, hybrid search, reranker
    agents/       router, specialists, formulation flow, composer, orchestrator
    guardrails/   PII, verification, confidence, fixed messages
    translate/    Translator interface, Bhashini, LLM fallback
    db/           SQLAlchemy models, audit log
  scripts/        ingest.py, eval.py
  tests/
frontend/         React + Vite + TypeScript + Tailwind
data/
  raw/{india,international}/   official documents (team adds)
  manifest.yaml                one entry per document
  formulation_flow.yaml        classifier questions (editable)
  registry_links.yaml          official portal links (shown only when verified)
  eval/questions.jsonl         evaluation set
docs/             ARCHITECTURE.md, CORPUS_SOURCES.md, DEMO_SCRIPT.md, eval_report.md
```

## Team checklist before judging

- [ ] Download and ingest the corpus ([docs/CORPUS_SOURCES.md](docs/CORPUS_SOURCES.md))
- [ ] Verify portal links in `data/registry_links.yaml` and set `verified: true`
- [ ] Review `data/formulation_flow.yaml` with a regulatory expert and set `verified: true`
- [ ] Fill and verify `data/eval/questions.jsonl`; run `scripts/eval.py`
- [ ] Verify the five answers in [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)
- [ ] Have a native speaker review the Hindi/Marathi text (`frontend/src/i18n.tsx`,
      `backend/app/guardrails/messages.py`, `data/formulation_flow.yaml`)

---

*This is information, not legal advice.*

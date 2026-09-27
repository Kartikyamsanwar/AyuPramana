# AyuPramana — IP-SAKTI Sahayak (SIH26045)

> *Every answer, with its pramāṇa (proof).*

AyuPramana is a multilingual, **source-cited** AI assistant for Intellectual Property and regulatory questions about
Ayurvedic products. It answers only from a curated corpus of statutes, rules and treaties. Every answer cites the
exact provision and document version it used. When the sources don't answer a question, it abstains.

Built for Smart India Hackathon 2026, problem statement **SIH26045** (Ministry of Ayush / All India Institute of Ayurveda).

## Prerequisites

- Python 3.11+ (tested on 3.11 and 3.13)
- Node.js 20+
- Optional: Docker Desktop

## Setup

```bash
cp .env.example .env        # Windows PowerShell: Copy-Item .env.example .env
```

Edit `.env` and set `GROQ_API_KEY`. Get a key from the Groq console.

### Backend

```bash
cd backend
python -m venv .venv
# Windows:      .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Check it: http://localhost:8000/api/health

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The dev server forwards `/api` to the backend on port 8000.

### Docker (both services)

```bash
docker compose up --build
```

Open http://localhost:8080.

## Tests

```bash
cd backend && python -m pytest
cd frontend && npm test
```

## Repository layout

```
backend/    FastAPI app (app/), CLI scripts (scripts/), tests
frontend/   React + Vite + TypeScript + Tailwind UI
data/       raw documents, manifest.yaml, evaluation set
docs/       architecture, corpus sources, demo script, eval report
```

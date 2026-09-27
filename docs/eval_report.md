# AyuPramana — evaluation report

This file is **generated**. It is overwritten every time you run:

```bash
cd backend
python scripts/eval.py            # add --pause 2 on the Groq free tier
```

It has not been generated from the real corpus yet, because the official documents still have to be
downloaded (see [CORPUS_SOURCES.md](CORPUS_SOURCES.md)). Numbers only mean something after:

1. the documents are in `data/raw/` and listed in `data/manifest.yaml`
2. `python scripts/ingest.py --all` has run
3. a team member has filled `expected_citations` in [`data/eval/questions.jsonl`](../data/eval/questions.jsonl)
   by reading the real provisions, and set `verified: true` on each checked row

## What the report measures

| Metric | Definition |
|---|---|
| Retrieval hit rate | Share of answer blocks where an expected provision was among the retrieved sources |
| Citation precision / recall | Share of the answer's citations that are expected provisions / share of expected provisions cited |
| Abstention accuracy | Answered in-scope questions and abstained on out-of-scope ones |
| Out-of-scope abstained | Safety: medical/dosage and unrelated questions were declined |
| In-scope answered | Coverage: in-scope questions got an answer |
| Average confidence | Mean confidence of the answers that were given |
| Per-language results | The same measures for English, Hindi and Marathi questions |
| Latency p50 / p95 | End-to-end time per question |

A pipeline smoke run on the fictional test corpus (not real law) correctly declined all out-of-scope
questions (medical dosage in English and Hindi, and an unrelated sports question).

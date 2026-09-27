# Demo script (about 7 minutes)

Five questions that show every judging criterion. **Before the demo, the team must run each one on the real
corpus, open every citation and check it against the PDF**, then write the provisions it cites in the
"Verified citations" line. If an answer cites the wrong provision, fix the corpus/manifest or pick another question.
Never present an answer that nobody has checked.

## Setup checklist

- [ ] All documents in `docs/CORPUS_SOURCES.md` downloaded, listed in `data/manifest.yaml`, ingested
      (`python scripts/ingest.py --all` shows no MISSING rows)
- [ ] `.env` has `GROQ_API_KEY`, `ADMIN_MODE=true` (for the audit page); optional Bhashini keys
- [ ] Backend and frontend running; the header shows "Backend online" without "LLM not configured"
- [ ] Ask one warm-up question (loads the models)
- [ ] `python scripts/eval.py` run on the verified question set; `docs/eval_report.md` open in a tab
- [ ] Phone hotspot ready in case venue Wi-Fi fails (Groq is a cloud API). Without it, the app still quotes
      provisions in extractive mode.

---

### 1. Accuracy and citations — India

**Ask (India):** "Can I patent a classical Ayurvedic formulation?"

Show:
- the cited answer
- click a citation chip: the source text, section, version date and official link appear
- the confidence badge
- the disclaimer

Verified citations: _team to fill_

### 2. Jurisdiction separation — Both

**Toggle "Both", ask:** "What approvals do I need to use a medicinal plant commercially?"

Show two separate cards, India (access and benefit sharing under the biodiversity law) and International (CBD / Nagoya).
Point out that the two regimes are never mixed.

Verified citations: India _team to fill_ · International _team to fill_

### 3. Formulation classifier — agentic flow

**Ask (India):** "Which regulatory category does my herbal product fall into?"

Answer the four quick-reply questions. Show that:
- the category is decided from retrieved legal definitions, with citations
- the answer covers what the category requires, plus its IP/ABS/advertising points

Verified citations: _team to fill_

### 4. Multilingual — Hindi or Marathi

**Switch the language to हिंदी (or मराठी), ask:** "किसी औषधीय पौधे का व्यावसायिक उपयोग करने के लिए मुझे कौन-सी स्वीकृतियाँ चाहिए?"

Show:
- the UI and answer are in Hindi
- citation chips are identical to the English answer
- the source panel still shows the official English text

Verified citations: _team to fill_

### 5. Safe abstention and escalation

**Ask:** "What is the right dosage of Ashwagandha for insomnia?"

The assistant declines: this is a medical question and out of scope.

**Then ask something the corpus doesn't cover**, e.g. a question about another country's trademark law with only
Indian documents loaded, set to "India". It abstains instead of guessing and offers "Talk to an IP facilitator".
Click it and show the reference number.

**Finish on the Audit page:**
- the PII-scrubbed question log
- confidence and abstentions
- feedback and the escalation you just created

Then show `docs/eval_report.md`.

---

## Talking points

- "Every sentence is fact-checked against its source before you see it; unsupported sentences are removed."
- "Low confidence means no answer, just the related provisions and a human facilitator."
- "India and international law are separate pipelines — never mixed in one answer."
- "No law is hard-coded: the corpus is official documents, versioned by file hash; the answer shows the version."
- "Personal data is masked before anything is sent to the model or logged."

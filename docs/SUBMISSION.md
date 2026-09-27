# SIH 2026 idea submission — SIH26045

Copy each section into the matching form field. Character limits were checked with a script.

---

## Idea Title (max 100 characters)

AyuPramana: Source-Cited Multilingual AI for Ayurveda IP and Regulatory Guidance

---

## Abstract / Summary (max 10,000 characters)

AyuPramana ("every answer, with its pramana — its proof") is a multilingual, source-cited AI assistant that helps Ayurveda practitioners, researchers, AYUSH startups, MSMEs and cultivators understand the intellectual-property and regulatory rules that apply to their products, under both Indian law and international treaties.

Protecting and commercialising an Ayurvedic product means working through several overlapping regimes at once: patents, geographical indications, trade marks, designs, copyright and plant-variety rights; access-and-benefit-sharing (ABS) duties for biological resources and traditional knowledge; drug, food and cosmetic regulation; and the law on advertising claims. The law is spread across many statutes and treaties, it changes often, and plain-language guidance is scarce. Genuine innovation goes unprotected, while India's traditional knowledge stays exposed to misappropriation.

AyuPramana answers only from a curated, version-tracked corpus of official documents. Retrieval-augmented generation (RAG) finds the relevant provisions, and the language model writes an answer using nothing but those provisions. Every sentence ends with a citation that shows the document, section or article, jurisdiction, version date and official link, and one click opens the exact source text. A second AI pass fact-checks each sentence against its cited source and removes anything unsupported. It also checks that the sources are about what the user actually asked, and it rejects claims based on what a list merely does not mention. A confidence score combines retrieval relevance, agreement between keyword and semantic search, and the fact-check result. When confidence is low, or the question is out of scope (for example medical dosage questions), the assistant abstains politely, points to related provisions and offers to connect the user with a human IP facilitator.

India and international answers are never mixed. A jurisdiction toggle (India / International / Both) runs separate, strictly filtered pipelines and shows the answers side by side. A small agentic router sends each question to a specialist:
- a formulation classifier that asks up to four quick-reply questions and decides the product's regulatory category only from retrieved legal definitions,
- an IP-routing agent,
- an ABS compliance checklist,
- a traditional-knowledge / TKDL prior-art pointer,
- a registry navigator that shows only team-verified official portal links.

The assistant works in English, Hindi and Marathi. Questions are translated to English for search, and answers are translated back through Bhashini, with an LLM as fallback. Citation markers are preserved, and the source text is always shown in its official language. Personal data such as phone, email and Aadhaar-like numbers is masked before anything is sent to the model or logged, and only an anonymous session id is kept, in the spirit of the DPDP Act, 2023. Every question is recorded in a privacy-safe audit log along with its confidence, abstentions and feedback. A built-in evaluation harness measures retrieval hit rate, citation precision and recall, abstention accuracy and per-language quality.

A working prototype is built and tested. It already covers 13 official documents: nine Indian Acts from India Code (Patents, Biological Diversity, Geographical Indications, Trade Marks, Designs, Copyright, Plant Varieties and Farmers' Rights, Drugs and Cosmetics, and Drugs and Magic Remedies) and four international instruments (TRIPS, the Convention on Biological Diversity, the Nagoya Protocol and the 2024 WIPO Treaty on IP, Genetic Resources and Associated Traditional Knowledge). No law is hard-coded, and new or amended documents are added by dropping in the official file and re-running ingestion.

---

## Technology Bucket

Choose the option closest to **Artificial Intelligence / Machine Learning** (or "AI/ML"; if there is a separate
"Natural Language Processing" bucket, pick that one).

---

## Idea Description (max 50,000 characters)

1. PROBLEM

Ayurveda rests on a vast body of codified and community-held traditional knowledge, and on therapeutics from plant, mineral and animal sources. Taking an Ayurvedic product to market means navigating many regimes at the same time:
- Intellectual property: patents, geographical indications (GI), trade marks, designs, copyright, trade secrets and plant-variety rights.
- Access and benefit sharing (ABS) obligations that flow from India's sovereignty over its biological resources and associated traditional knowledge.
- Drug regulation that decides whether a formulation is a classical medicine, a proprietary medicine, a new drug, a phytopharmaceutical, a food product (Ayurveda Aahar) or a cosmetic, and the rules on advertising claims.
- International instruments such as TRIPS, the Convention on Biological Diversity, the Nagoya Protocol and the 2024 WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge.

Practitioners, researchers, AYUSH startups, MSMEs and cultivators struggle to find authoritative, plain-language answers. The rules are spread across many documents, they are amended often, and professional advice is expensive. As a result, legitimate innovation is under-protected and under-commercialised, and traditional knowledge stays exposed to misappropriation abroad. General-purpose chatbots are not a safe substitute. They answer from memory, can invent section numbers, mix Indian and foreign law, and rarely admit uncertainty.

2. OUR SOLUTION: AYUPRAMANA

AyuPramana (from pramana, "valid means of knowledge") is a multilingual AI assistant that answers IP and regulatory questions about Ayurvedic products only from official documents, and shows the proof for every statement. Its design follows the four things that matter most for such a tool:
- Accurate answers.
- Correct citations.
- Safe abstention when unsure or out of scope.
- Good quality in Indian languages.

3. HOW IT WORKS (END TO END)

a) Curated, version-tracked corpus
- The corpus holds only official documents from official portals: India Code, WTO, the CBD Secretariat, WIPO, and later IP India, NBA, FSSAI and the Ministry of Ayush.
- A manifest records each document's title, jurisdiction (India or International), domain (IP, ABS, drug regulation, advertising, food, cosmetics or traditional knowledge), type (statute, rules, treaty or guideline), version date and source URL.
- Every file is identified by a cryptographic hash. If the file changes, a new version is created and the old text is retired but kept for audit. Answers show exactly which version they used.

b) Section-aware ingestion
- Documents are split along their legal structure: Sections, Articles, Rules, Chapters and Schedules.
- The heading stays inside every chunk, so each citation points to a precise provision, for example "Section 3" or "Article 15".
- Long provisions are split at clause boundaries and cited as ranges such as "Section 3(k)-(p)".
- Handling for the realities of official PDFs:
  - footnotes and amendment markers (detected by font size),
  - tables of contents,
  - lists of amending Acts,
  - headings split across lines,
  - wrapped cross-references,
  - schedules,
  - annexes inside treaties.

c) Hybrid retrieval with strict jurisdiction separation
- Each question is searched with both keyword search (BM25) and multilingual semantic search. The two result lists are merged with reciprocal rank fusion, and an optional cross-encoder reranker can re-score them.
- Every search is restricted to one jurisdiction. For "Both", two independent pipelines run, and the UI shows two separate cards, so Indian and international law are never mixed in one answer.

d) Agentic router and specialists
A router agent returns strict JSON with the scope (in scope, medical advice, personal legal advice, greeting or off-topic) and the intents. It then dispatches to specialists:
- Formulation Classifier: asks up to four quick-reply questions (origin of the formulation, intended use, ingredients, planned health claims), then places the product in a regulatory category. The category is decided only from the legal definitions retrieved from the corpus, with citations. The questions live in an editable configuration file that experts can review.
- IP Routing agent: which IP rights could apply, what they protect, and their key conditions and exclusions.
- ABS Compliance helper: a cited checklist of access and benefit-sharing obligations.
- Traditional-knowledge / TKDL pointer: why traditional knowledge matters as prior art, with links to the official search portals.
- Registry navigator: which office, portal or form applies. It shows only links that the team has verified.
- General regulatory Q&A for everything else.

A composer merges the specialists' results into one cited answer per jurisdiction.

e) Grounded generation, citation verification and confidence
- The language model receives only the retrieved provisions, numbered as sources. It must end every factual sentence with citation markers, must not add inferences, and must reply "insufficient evidence" if the sources do not answer.
- Citation markers that point to sources which were not provided are removed.
- A second AI pass then fact-checks each statement against its cited source:
  - Unsupported statements are deleted.
  - Claims about what a source does not say (for example "X is not in the list") are rejected unless the source says so explicitly. This prevents confident wrong answers built on incomplete excerpts.
  - The same pass checks that the sources are about the subject the user asked about.
- A confidence score (0 to 1) combines:
  - how relevant the best cited provision is,
  - whether keyword and semantic search agree,
  - what share of statements passed the fact-check.
- Answers below a configurable threshold are withheld. The user sees an abstention message, a labelled list of possibly related provisions, and a "Talk to an IP facilitator" button that records a request with a reference number.

f) Scope guardrails
- Medical, dosage and treatment questions are declined.
- Questions that ask for personal legal advice ("should I sue…") get general information, a clear notice and an offer of escalation.
- Retrieved text is always treated as data, never as instructions, to prevent prompt injection.
- Every answer carries the standing disclaimer "This is information, not legal advice."

g) Multilingual
- The interface, fixed messages and classifier questions are available in English, Hindi and Marathi.
- Questions in Hindi or Marathi are translated to English for search, the pivot language of the corpus. Generated answers are translated back.
- Translation uses the Bhashini (MeitY) pipeline when credentials are configured, with a language-model translator as fallback.
- Citation markers must survive translation, and a translation that changes them is rejected.
- Quoted source text is always shown in its official language.
- Voice input through the browser is available as an optional feature.

h) Privacy, audit and evaluation
- Phone numbers, emails, Aadhaar-like numbers, PAN-like numbers and other long ID numbers are masked before anything is sent to the model or logged. Only an anonymous session id is kept, in the spirit of India's Digital Personal Data Protection Act, 2023.
- An audit page shows recent (scrubbed) questions, confidence, abstentions, feedback and facilitator requests.
- An evaluation harness runs a question set that includes deliberately out-of-scope questions. It reports:
  - retrieval hit rate,
  - citation precision and recall,
  - abstention accuracy,
  - average confidence,
  - per-language results,
  - latency.

4. CURRENT STATUS (WORKING PROTOTYPE)

The prototype is built end to end and tested:
- Backend: Python, FastAPI, SQLite and ChromaDB, with hybrid search, the agents, verification, translation and the audit log.
- Web UI: React, TypeScript and Tailwind, with a jurisdiction toggle, language selector, citation chips with a source panel, confidence badges, quick-reply buttons, and Sources and Audit pages.
- The corpus currently holds 13 official documents, split into about 1,200 provision-level chunks:
  - India (India Code): the Patents Act 1970, Biological Diversity Act 2002 (with the 2023 amendment), Geographical Indications of Goods Act 1999, Trade Marks Act 1999, Designs Act 2000, Copyright Act 1957, Protection of Plant Varieties and Farmers' Rights Act 2001, Drugs and Cosmetics Act 1940 (including Chapter IVA on Ayurvedic, Siddha and Unani drugs) and Drugs and Magic Remedies (Objectionable Advertisements) Act 1954.
  - International: TRIPS (as amended in 2017), the Convention on Biological Diversity, the Nagoya Protocol and the WIPO GRATK Treaty (2024).
- The backend has an automated test suite (79 tests), and live tests were run with a hosted LLM.
- Example: asked "Can I advertise that my Ayurvedic product cures diabetes?", the assistant answers that such an advertisement is not permitted. It cites the Schedule of the Drugs and Magic Remedies (Objectionable Advertisements) Act, 1954, which lists diabetes. The same question asked in Hindi gets the same cited answer in Hindi. A dosage question is declined.

5. TECHNOLOGY STACK

- Backend: Python, FastAPI and Pydantic. SQLite (via SQLAlchemy) holds documents, versions, chunks and the audit log. ChromaDB is the vector store, with BM25 keyword search alongside.
- Embeddings: multilingual models (multilingual-e5 / BGE-M3 locally, or a hosted embeddings API for low-memory deployment). Optional cross-encoder reranker.
- LLM: provider-agnostic wrapper (Groq-hosted open models by default; Anthropic Claude and offline Ollama supported).
- Translation: Bhashini API with LLM fallback.
- Frontend: React, Vite, TypeScript and Tailwind CSS. Accessible and mobile-friendly.
- Deployment: Docker, a single container that serves the UI and the API.

6. IMPACT AND BENEFITS

- Access to authoritative, free, plain-language guidance, in their own language, for innovators, MSMEs and cultivators who cannot afford specialist advice.
- Trust through transparency: every statement can be checked against the official text and its version date.
- Fewer compliance mistakes, for example non-compliant advertising claims or missed benefit-sharing obligations.
- Better protection of Ayurvedic innovation, and wider awareness of traditional-knowledge prior art, which supports India's efforts against misappropriation.
- Lighter load on IP facilitation centres: routine questions are answered, and complex cases are escalated with context.
- An auditable, measurable system that the Ministry can evaluate and improve.

7. FEASIBILITY AND SCALABILITY

- The system is built only from open, authoritative public sources and open-source software.
- New or amended laws are added by placing the official file and running one ingestion command. Nothing is hard-coded.
- It runs on modest hardware. A low-memory mode uses a hosted embeddings service, and an offline mode runs local models.
- More Indian languages can be added through Bhashini and the UI string tables.

8. RISKS AND MITIGATIONS

- Wrong or invented legal statements: answers are grounded only in retrieved text, every statement is fact-checked, absence claims are rejected, and the assistant abstains when unsure.
- Outdated law: every document is version-tracked by hash and date, answers show the version used, and retired versions are kept for audit.
- Over-reliance: a disclaimer is shown on every answer, and escalation to human IP facilitators is built in.
- Privacy: personal data is masked before it is sent to the model or logged, and only an anonymous session id is kept.
- Translation errors: citations are preserved and checked, and the official source text is always shown alongside.

9. ROADMAP

- Add the remaining documents:
  - Patents Rules,
  - Biological Diversity Rules 2024 and ABS regulations,
  - the Ayurveda provisions of the Drugs and Cosmetics Rules,
  - FSSAI Ayurveda Aahar regulations,
  - PCT, Madrid, Hague and Budapest treaties,
  - Ministry of Ayush guidelines.
- Have domain experts verify the evaluation set and the classifier questions.
- Integrate Bhashini fully, add more Indian languages, and improve voice input.
- Integrate with IP facilitation centres for escalated cases.

All information given by AyuPramana is general information, not legal advice.

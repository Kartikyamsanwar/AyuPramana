# Corpus sources — what to download and from where

AyuPramana answers **only** from the documents listed in `data/manifest.yaml`.
This page is the team's checklist for collecting them.

**Rules for collectors**

1. Download only from the **official portal** named for each document. Do not use blogs or third-party mirrors.
2. Prefer the **latest consolidated / "as amended"** text. If only the principal Act plus separate amendment
   documents are available, download each and add each as its own manifest entry.
3. Record the **exact page URL** you downloaded from and the **date of the text** (amendment or consolidation date)
   in `data/manifest.yaml`. Leave nothing to memory — copy both from the document/portal.
4. Save PDFs (or HTML pages) into `data/raw/india/` or `data/raw/international/` using the suggested file name.
5. Tick the box below and commit.

The "Exact link" column is intentionally empty: fill it in from the portal after you have checked it.

## India

| ✔ | Suggested `id` | Document (use the official title in the manifest) | `domain` | `doc_type` | Where to get it | Exact link | Text dated |
|---|---|---|---|---|---|---|---|
| ☐ | `patents_act_1970` | Patents Act, 1970 (as amended) | ip | statute | India Code — indiacode.nic.in (also IP India — ipindia.gov.in) | | |
| ☐ | `patents_rules` | Patents Rules, as amended (including the 2024 amendment) | ip | rules | IP India — ipindia.gov.in | | |
| ☐ | `biological_diversity_act_2002` | Biological Diversity Act, 2002 (including the 2023 amendment) | abs | statute | India Code — indiacode.nic.in; National Biodiversity Authority (NBA) website | | |
| ☐ | `biological_diversity_rules_2024` | Biological Diversity rules, 2024 | abs | rules | National Biodiversity Authority (NBA) website | | |
| ☐ | `abs_regulations` | Access and Benefit Sharing regulations / guidelines currently in force | abs | guideline | National Biodiversity Authority (NBA) website | | |
| ☐ | `gi_act` | Geographical Indications of Goods Act (as amended) | ip | statute | India Code — indiacode.nic.in; IP India (GI Registry) — ipindia.gov.in | | |
| ☐ | `trade_marks_act` | Trade Marks Act (as amended) | ip | statute | India Code — indiacode.nic.in | | |
| ☐ | `designs_act` | Designs Act (as amended) | ip | statute | India Code — indiacode.nic.in | | |
| ☐ | `copyright_act` | Copyright Act (as amended) | ip | statute | India Code — indiacode.nic.in | | |
| ☐ | `ppvfr_act` | Protection of Plant Varieties and Farmers' Rights Act | ip | statute | India Code — indiacode.nic.in | | |
| ☐ | `drugs_cosmetics_act` | Drugs and Cosmetics Act (as amended) | drug_regulation | statute | India Code — indiacode.nic.in; CDSCO / Ministry of Ayush | | |
| ☐ | `drugs_cosmetics_rules_ayush` | Drugs and Cosmetics Rules — Ayurveda, Siddha & Unani provisions | drug_regulation | rules | CDSCO / Ministry of Ayush | | |
| ☐ | `dmr_act` | Drugs and Magic Remedies (Objectionable Advertisements) Act (as amended) | advertising | statute | India Code — indiacode.nic.in | | |
| ☐ | `fssai_ayurveda_aahar` | FSSAI regulations on Ayurveda Aahar | food | rules | FSSAI website | | |
| ☐ | `tkdl_about` | TKDL — official description / access-policy pages | tk | registry_note | Traditional Knowledge Digital Library — tkdl.res.in | | |

Optional but useful: cosmetics-specific rules (`domain: cosmetics`), official IP India manuals or guidelines
for examiners (`doc_type: guideline`), and Ministry of Ayush guidance on advertisements (`domain: advertising`).

## International

| ✔ | Suggested `id` | Document | `domain` | `doc_type` | Where to get it | Exact link | Text dated |
|---|---|---|---|---|---|---|---|
| ☐ | `trips_agreement` | Agreement on Trade-Related Aspects of Intellectual Property Rights (TRIPS) | ip | treaty | World Trade Organization (WTO) website | | |
| ☐ | `cbd` | Convention on Biological Diversity | abs | treaty | CBD — cbd.int | | |
| ☐ | `nagoya_protocol` | Nagoya Protocol on Access and Benefit-sharing | abs | treaty | CBD — cbd.int | | |
| ☐ | `wipo_gr_atk_treaty_2024` | WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge (2024) | tk | treaty | WIPO — wipo.int | | |
| ☐ | `pct` | Patent Cooperation Treaty (PCT) | ip | treaty | WIPO — wipo.int | | |
| ☐ | `madrid_protocol` | Madrid Protocol (international trademark registration) | ip | treaty | WIPO — wipo.int | | |
| ☐ | `hague_agreement` | Hague Agreement (international registration of industrial designs) | ip | treaty | WIPO — wipo.int | | |
| ☐ | `budapest_treaty` | Budapest Treaty (deposit of microorganisms for patent procedure) | ip | treaty | WIPO — wipo.int | | |

## Official portals for the Registry navigator

The Registry navigator only shows links that the team has entered and marked `verified: true` in
`data/registry_links.yaml`. Collect the exact filing/search pages from:

- IP India — ipindia.gov.in (patent, trade mark, design and GI filing and public search)
- Traditional Knowledge Digital Library — tkdl.res.in
- National Biodiversity Authority (NBA) — ABS application forms
- India Code — indiacode.nic.in (statute texts)
- WIPO — wipo.int (PCT, Madrid, Hague filing systems)

## After downloading

```bash
cd backend
python scripts/ingest.py --all
```

The ingest summary lists every manifest entry, its chunk count, and warns about entries whose files are missing.

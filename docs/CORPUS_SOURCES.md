# Corpus sources — what to download and from where

AyuPramana answers **only** from the documents listed in `data/manifest.yaml`.
This page is the team's checklist for collecting them.

**Rules for collectors**

1. Download only from the **official portal** named for each document. (India Code moved to **indiacode.gov.in** in 2026; old indiacode.nic.in PDF links no longer work.) Do not use blogs or third-party mirrors.
2. Prefer the **latest consolidated / "as amended"** text. If only the principal Act plus separate amendment
   documents are available, download each and add each as its own manifest entry.
3. Record the **exact page URL** you downloaded from and the **date of the text** (amendment or consolidation date)
   in `data/manifest.yaml`. Leave nothing to memory — copy both from the document/portal.
4. Save PDFs (or HTML pages) into `data/raw/india/` or `data/raw/international/` using the suggested file name.
5. Tick the box below and commit.

Rows marked ☑ are downloaded, listed in `data/manifest.yaml` and ingested (links and dates taken from the documents on 2026-09-27). Rows marked ☐ are still to collect; fill in their links from the portal after checking them.

## India

| ✔ | Suggested `id` | Document (use the official title in the manifest) | `domain` | `doc_type` | Where to get it | Exact link | Text dated |
|---|---|---|---|---|---|---|---|
| ☑ | `patents_act_1970` | Patents Act, 1970 (as amended) | ip | statute | India Code — indiacode.nic.in (also IP India — ipindia.gov.in) | [official PDF](https://indiacode.gov.in/server/api/core/bitstreams/9e02bd6e-8946-4131-9eec-b1a0dd71cf80/content) | 2026-05-05 |
| ☐ | `patents_rules` | Patents Rules, as amended (including the 2024 amendment) | ip | rules | IP India — ipindia.gov.in | | |
| ☑ | `biological_diversity_act_2002` | Biological Diversity Act, 2002 (including the 2023 amendment) | abs | statute | India Code — indiacode.nic.in; National Biodiversity Authority (NBA) website | [official PDF](https://indiacode.gov.in/server/api/core/bitstreams/bf83f6e3-2c10-4dab-9daa-da46662849d2/content) | 2024-04-01 |
| ☐ | `biological_diversity_rules_2024` | Biological Diversity rules, 2024 | abs | rules | National Biodiversity Authority (NBA) website | | |
| ☐ | `abs_regulations` | Access and Benefit Sharing regulations / guidelines currently in force | abs | guideline | National Biodiversity Authority (NBA) website | | |
| ☑ | `gi_act_1999` | Geographical Indications of Goods Act (as amended) | ip | statute | India Code — indiacode.nic.in; IP India (GI Registry) — ipindia.gov.in | [official PDF](https://indiacode.gov.in/server/api/core/bitstreams/55740471-35c8-4016-a122-c20c019b91ab/content) | 2026-06-01 |
| ☑ | `trade_marks_act_1999` | Trade Marks Act (as amended) | ip | statute | India Code — indiacode.nic.in | [official PDF](https://indiacode.gov.in/server/api/core/bitstreams/7648d2d2-4e14-40dc-80d0-db8f99716fd5/content) | 2026-06-01 |
| ☑ | `designs_act_2000` | Designs Act (as amended) | ip | statute | India Code — indiacode.nic.in | [official PDF](https://indiacode.gov.in/server/api/core/bitstreams/94cc7bf7-96c1-4dbe-b3b3-9b3287296573/content) | 2026-06-15 |
| ☑ | `copyright_act_1957` | Copyright Act (as amended) | ip | statute | India Code — indiacode.nic.in | [official PDF](https://indiacode.gov.in/server/api/core/bitstreams/696240f0-b1ef-42f3-972d-9d03b1a6066f/content) | 2026-06-15 |
| ☑ | `ppvfr_act_2001` | Protection of Plant Varieties and Farmers' Rights Act | ip | statute | India Code — indiacode.nic.in | [official PDF](https://indiacode.gov.in/server/api/core/bitstreams/e04ea3dd-cccf-4562-82ee-d661b9af0c8e/content) | 2026-09-10 |
| ☑ | `drugs_cosmetics_act_1940` | Drugs and Cosmetics Act (as amended) | drug_regulation | statute | India Code — indiacode.nic.in; CDSCO / Ministry of Ayush | [official PDF](https://indiacode.gov.in/server/api/core/bitstreams/f775a727-4f6e-4da4-9a53-71865e8468ad/content) | 2026-07-01 |
| ☐ | `drugs_cosmetics_rules_ayush` | Drugs and Cosmetics Rules — Ayurveda, Siddha & Unani provisions | drug_regulation | rules | CDSCO / Ministry of Ayush | | |
| ☑ | `dmr_act_1954` | Drugs and Magic Remedies (Objectionable Advertisements) Act (as amended) | advertising | statute | India Code — indiacode.nic.in | [official PDF](https://indiacode.gov.in/server/api/core/bitstreams/6381cc69-0b65-4e0f-9754-71f0f3bf91b7/content) | 2026-04-15 |
| ☐ | `fssai_ayurveda_aahar` | FSSAI regulations on Ayurveda Aahar | food | rules | FSSAI website | | |
| ☐ | `tkdl_about` | TKDL — official description / access-policy pages | tk | registry_note | Traditional Knowledge Digital Library — tkdl.res.in | | |

Optional but useful: cosmetics-specific rules (`domain: cosmetics`), official IP India manuals or guidelines
for examiners (`doc_type: guideline`), and Ministry of Ayush guidance on advertisements (`domain: advertising`).

## International

| ✔ | Suggested `id` | Document | `domain` | `doc_type` | Where to get it | Exact link | Text dated |
|---|---|---|---|---|---|---|---|
| ☑ | `trips_agreement` | Agreement on Trade-Related Aspects of Intellectual Property Rights (TRIPS) | ip | treaty | World Trade Organization (WTO) website | [official PDF](https://www.wto.org/english/docs_e/legal_e/31bis_trips_e.pdf) | 2017-01-23 |
| ☑ | `cbd` | Convention on Biological Diversity | abs | treaty | CBD — cbd.int | [official PDF](https://www.cbd.int/doc/legal/cbd-en.pdf) | 1992-06-05 |
| ☑ | `nagoya_protocol` | Nagoya Protocol on Access and Benefit-sharing | abs | treaty | CBD — cbd.int | [official PDF](https://www.cbd.int/abs/doc/protocol/nagoya-protocol-en.pdf) | 2010-10-29 |
| ☑ | `wipo_gratk_treaty_2024` | WIPO Treaty on Intellectual Property, Genetic Resources and Associated Traditional Knowledge (2024) | tk | treaty | WIPO — wipo.int | [official PDF (GRATK/DC/7)](https://www.wipo.int/edocs/mdocs/tk/en/gratk_dc/gratk_dc_7.pdf) | 2024-05-24 |
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

"""Section detection and splitting. All sample texts are fictional."""

from pathlib import Path

from app.ingest.chunker import chunk_document, estimate_tokens
from app.ingest.loaders import PageText, load_document

FIXTURES = Path(__file__).parent / "fixtures" / "corpus" / "raw"


def refs(chunks):
    return [c.section_ref for c in chunks]


def test_statute_sections_toc_chapters_footnotes_and_schedule() -> None:
    chunks = chunk_document(load_document(FIXTURES / "india" / "widgets_act.txt"), doc_type="statute")
    assert refs(chunks) == [
        "Preamble",
        "Arrangement of sections",
        "Section 1",
        "Section 2",
        "Section 3",
        "Section 4",
        "First Schedule",
    ]
    by_ref = {c.section_ref: c for c in chunks}
    # The table of contents is kept but marked, so retrieval can skip it
    assert by_ref["Arrangement of sections"].kind == "toc"
    # Headings stay inside the chunk text
    assert by_ref["Section 3"].text.splitlines()[0] == "CHAPTER II"  # chapter title folded into the next section
    assert "3. Registration of widgets" in by_ref["Section 3"].text
    # A lowercase cross-reference ("under section 2") and a footnote are not headings
    assert "under section 2" in by_ref["Section 3"].text
    assert "1. Subs. by fictional Act" in by_ref["Section 3"].text
    # Numbered items inside a schedule belong to the schedule
    assert "2. Particulars of moonflower petals" in by_ref["First Schedule"].text


def test_treaty_articles_ignore_inline_references() -> None:
    chunks = chunk_document(load_document(FIXTURES / "international" / "cloud_treaty.txt"), doc_type="treaty")
    assert refs(chunks) == ["Preamble", "Article 1", "Article 2", "Article 3"]
    assert "Article 1 of this Treaty" in chunks[2].text


def test_rules_use_rule_label_for_numbered_headings() -> None:
    chunks = chunk_document(load_document(FIXTURES / "india" / "starlight_rules.txt"), doc_type="rules")
    assert refs(chunks)[1:] == ["Rule 1", "Rule 2", "Rule 3"]


def test_explicit_keyword_headings_and_custom_label() -> None:
    text = "\n".join(
        [
            "Section 5 Scope",
            "Body of section five.",
            "RULE 7",
            "Body of rule seven.",
            "2.1.1 Definitions of fictional terms",
            "Body text.",
            "SCHEDULE E(1)",
            "List of fictional items.",
        ]
    )
    chunks = chunk_document([PageText(1, text)], doc_type="rules", section_label="Regulation")
    assert refs(chunks) == ["Section 5", "Rule 7", "Regulation 2.1.1", "Schedule E(1)"]


def test_long_section_is_split_with_clause_refs_and_overlap() -> None:
    clauses = "\n".join(f"({letter}) " + " ".join(["moonflower"] * 60) + ";" for letter in "abcdefghijklmnop")
    text = "3. Things that are not widgets.—The following are not widgets,—\n" + clauses
    chunks = chunk_document([PageText(1, text)], doc_type="statute", target_tokens=300, max_tokens=400, overlap_tokens=30)
    assert len(chunks) > 1
    assert chunks[0].section_ref.startswith("Section 3(a)")
    assert chunks[-1].section_ref.endswith("(p)")
    assert all(c.section_ref.startswith("Section 3(") for c in chunks)
    assert chunks[0].text.startswith("3. Things that are not widgets")
    assert chunks[1].text.startswith("3. Things that are not widgets") and "(continued)" in chunks[1].text.splitlines()[0]
    assert "… " in chunks[1].text  # overlap from the previous part
    assert all(estimate_tokens(c.text) <= 400 + 60 for c in chunks)


def test_pages_are_tracked() -> None:
    pages = [
        PageText(1, "Article 1\nFirst article text."),
        PageText(2, "continued on page two.\nArticle 2\nSecond article text."),
    ]
    chunks = chunk_document(pages, doc_type="treaty")
    assert [(c.section_ref, c.page) for c in chunks] == [("Article 1", 1), ("Article 2", 2)]
    assert "continued on page two." in chunks[0].text


def test_html_single_long_line_section_is_split(tmp_path) -> None:
    body = " ".join(["fictional"] * 1500)
    html = tmp_path / "doc.html"
    html.write_text(f"<html><body><script>ignore()</script><p>4. Long provision.—{body}</p></body></html>", encoding="utf-8")
    chunks = chunk_document(load_document(html), doc_type="statute", target_tokens=400, max_tokens=600)
    assert len(chunks) >= 3
    assert all(c.section_ref.startswith("Section 4") for c in chunks)
    assert "ignore()" not in chunks[0].text


# --- Layouts found in the official PDFs (sample text is fictional) ---------------------------
def test_split_article_heading_lines_are_joined_and_paragraphs_stay_inside() -> None:
    text = "\n".join([
        "Preamble text of a fictional treaty.",
        "Article",
        "15",
        "Access to Moonflowers",
        "1. Each Contracting Party shall respect moonflowers.",
        "2. Access shall be on mutually agreed fictional terms, as set out in",
        "Article 16",
        "paragraph 2 of this fictional Treaty.",
        "Article 16",
        "Sharing of Petals",
    ])
    chunks = chunk_document([PageText(1, text)], doc_type="treaty")
    assert refs(chunks) == ["Preamble", "Article 15", "Article 16"]
    assert "2. Access shall be on mutually agreed" in chunks[1].text  # numbered paragraph stays in Article 15
    assert "paragraph 2 of this fictional Treaty." in chunks[1].text  # wrapped cross-reference is not a heading


def test_annex_articles_are_prefixed_but_a_document_that_is_an_annex_is_not() -> None:
    body = "Article 1\nMain text.\nArticle 2\nMore main text.\nAnnex II\nPart 1\nArticle 1\nAnnex article text."
    assert refs(chunk_document([PageText(1, body)], doc_type="treaty"))[-1] == "Annex II, Part 1, Article 1"
    whole = "ANNEX 1C\nAGREEMENT ON FICTIONAL WIDGETS\nArticle 1\nText."
    assert refs(chunk_document([PageText(1, whole)], doc_type="treaty"))[-1] == "Article 1"


def test_statute_front_matter_footnotes_and_chapter_iva() -> None:
    text = "\n".join([
        "LIST OF AMENDING ACTS",
        "1. The Sample Widgets (Amendment) Act, 2090 (5 of 2090).",
        "2. The Sample Reforms Act, 2091 (Act 7 of 2091",
        "Sch.  for Schedule.",
        "1. Short title.—This fictional Act may be called the Sample Act.",
        "2. Definitions.—In this Act words mean what they say.",
        "† 1. 1st April, 2095, vide fictional notification.",
        "CHAPTER IVA",
        "PROVISIONS RELATING TO FICTIONAL REMEDIES",
        "33B. Application of Chapter IVA.—This Chapter applies to fictional remedies.",
    ])
    chunks = chunk_document([PageText(1, text)], doc_type="statute")
    assert refs(chunks) == ["Preamble", "Section 1", "Section 2", "Section 33B"]
    assert chunks[-1].text.startswith("CHAPTER IVA")


def test_schedule_heading_with_amendment_marker() -> None:
    text = "1. Short title.—Fictional.\n2. Definitions.—Fictional.\n1[THE SCHEDULE\n[See sections 3(d) and 14]\n1.\nMoon fever\n2.\nStar blindness"
    chunks = chunk_document([PageText(1, text)], doc_type="statute")
    assert refs(chunks)[-1] == "Schedule"
    assert "Moon fever" in chunks[-1].text and "Star blindness" in chunks[-1].text

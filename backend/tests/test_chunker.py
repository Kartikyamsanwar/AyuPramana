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

"""Ingestion, versioning and jurisdiction-filtered retrieval over the fictional corpus."""

import pytest


def test_ingest_reports_each_manifest_entry(make_services) -> None:
    services = make_services(ingest=False)
    results = {r.doc_id: r for r in services.ingestor().ingest()}
    assert results["widgets_act"].status == "ingested"
    assert results["cloud_treaty"].status == "ingested"
    assert results["missing_doc"].status == "missing_file"
    assert results["widgets_act"].chunks > 0

    again = {r.doc_id: r.status for r in services.ingestor().ingest()}
    assert again["widgets_act"] == "unchanged"


def test_ingest_single_doc_and_unknown_id(make_services) -> None:
    services = make_services(ingest=False)
    results = services.ingestor().ingest(doc_ids=["starlight_rules", "nope"])
    assert [(r.doc_id, r.status) for r in results] == [("nope", "unknown_id"), ("starlight_rules", "ingested")]


def test_retrieval_never_crosses_jurisdiction(make_services) -> None:
    services = make_services()
    query = "registration of widgets"
    india = services.retriever.search(query, "india")
    international = services.retriever.search(query, "international")
    assert india and international
    assert {r.chunk.jurisdiction for r in india} == {"india"}
    assert {r.chunk.jurisdiction for r in international} == {"international"}
    with pytest.raises(ValueError):
        services.retriever.search(query, "both")


def test_domain_filter_and_toc_excluded(make_services) -> None:
    services = make_services()
    abs_hits = services.retriever.search("share sea shells with grove keepers", "india", domains=["abs"])
    assert abs_hits and {r.chunk.doc_id for r in abs_hits} == {"starlight_rules"}
    all_hits = services.retriever.search("registration of widgets renewal", "india", top_k=20)
    assert all(r.chunk.kind != "toc" for r in all_hits)


def test_changed_file_creates_new_version_and_retires_old_chunks(make_services, settings) -> None:
    services = make_services()
    path = settings.raw_dir / "india" / "starlight_rules.txt"
    path.write_text(
        path.read_text(encoding="utf-8").replace("one tenth", "one fifth"), encoding="utf-8"
    )
    [result] = services.ingestor().ingest(doc_ids=["starlight_rules"])
    assert result.status == "ingested"

    hits = services.retriever.search("benefit sharing sea shells grove keepers", "india", domains=["abs"])
    texts = " ".join(h.chunk.text for h in hits)
    assert "one fifth" in texts and "one tenth" not in texts
    assert {h.chunk.version for h in hits} == {result.version}

    [(doc, versions)] = [d for d in services.repository.documents_with_versions() if d[0].id == "starlight_rules"]
    assert [v.is_active for v in versions] == [True, False]

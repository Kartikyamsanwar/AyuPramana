import pytest

from app.ingest.manifest import ManifestError, load_manifest

VALID = """
- id: sample_doc
  title: "Sample (fictional)"
  jurisdiction: india
  domain: ip
  doc_type: statute
  version_date: "2099-01-01"
  file: india/sample.pdf
"""


def write(tmp_path, text):
    path = tmp_path / "manifest.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_manifest(tmp_path) -> None:
    [entry] = load_manifest(write(tmp_path, VALID))
    assert entry.id == "sample_doc" and entry.file == "india/sample.pdf"


def test_comment_only_manifest_is_empty(tmp_path) -> None:
    assert load_manifest(write(tmp_path, "# nothing yet\n")) == []
    assert load_manifest(tmp_path / "absent.yaml") == []


@pytest.mark.parametrize(
    "broken",
    [
        VALID.replace('"2099-01-01"', '"YYYY-MM-DD"'),
        VALID.replace("jurisdiction: india", "jurisdiction: both"),
        VALID.replace("india/sample.pdf", "../secret.pdf"),
        VALID + VALID,  # duplicate id
        "id: not_a_list",
    ],
)
def test_invalid_manifest_raises(tmp_path, broken) -> None:
    with pytest.raises(ManifestError):
        load_manifest(write(tmp_path, broken))

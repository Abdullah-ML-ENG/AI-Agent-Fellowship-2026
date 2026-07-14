from pathlib import Path
from rag_application import clean_text, extract_txt_md

def test_clean_text():
    raw = "Hello   \n\n world \x00 test"
    assert clean_text(raw) == "Hello world test"

def test_extract_txt_md(tmp_path: Path):
    p = tmp_path / "a.txt"
    p.write_text("This is a test file.")
    docs = extract_txt_md(p)
    assert len(docs) == 1
    assert "test file" in docs[0].page_content
    assert docs[0].metadata["source"] == "a.txt"

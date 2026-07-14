from pathlib import Path
from rag_application import extract_txt_md, get_splitter, index_chunks, retrieve_context

def test_end_to_end_txt_pipeline(tmp_path: Path):
    p = tmp_path / "doc.txt"
    p.write_text("The warranty period is 2 years from purchase date.")
    raw = extract_txt_md(p)
    chunks = get_splitter().split_documents(raw)
    for i, c in enumerate(chunks):
        c.metadata["chunk_id"] = i
    index_chunks(chunks)

    out = retrieve_context("What is the warranty period?", "ChromaDB", top_k=3)
    assert len(out) >= 1

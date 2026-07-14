from rag_application import build_prompt
from langchain.schema import Document

def test_prompt_contains_citation_contract():
    docs = [Document(page_content="abc", metadata={"source":"a.pdf","page":3,"chunk_id":7})]
    p = build_prompt("What is abc?", [], docs)
    assert "source: <doc>" in p or "source=" in p

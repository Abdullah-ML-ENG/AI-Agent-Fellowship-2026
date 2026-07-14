from langchain.schema import Document
from rag_application import index_chunks, retrieve_context

def test_retrieval_returns_relevant_docs():
    docs = [
        Document(page_content="Python is used for machine learning", metadata={"source":"x.txt","page":1,"chunk_id":0}),
        Document(page_content="Finance report Q2 revenue", metadata={"source":"y.txt","page":2,"chunk_id":1}),
    ]
    index_chunks(docs)
    out = retrieve_context("machine learning", "ChromaDB", top_k=2)
    assert len(out) >= 1

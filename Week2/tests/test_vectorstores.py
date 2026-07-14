from langchain.schema import Document
from rag_application import index_chunks, get_vectorstore, CHROMA_DIR, FAISS_DIR
import shutil

def test_chroma_and_faiss_indexing():
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    if FAISS_DIR.exists():
        shutil.rmtree(FAISS_DIR)
        FAISS_DIR.mkdir(parents=True, exist_ok=True)

    docs = [
        Document(page_content="Revenue grew by 20 percent", metadata={"source": "r1.txt", "page": 1, "chunk_id": 0}),
        Document(page_content="Net margin improved", metadata={"source": "r1.txt", "page": 1, "chunk_id": 1}),
    ]
    index_chunks(docs)

    c = get_vectorstore("ChromaDB")
    f = get_vectorstore("FAISS")
    assert c is not None
    assert f is not None

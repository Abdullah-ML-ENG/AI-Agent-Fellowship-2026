# Enterprise Document Intelligence Platform (RAG)

A production-grade Streamlit + LangChain RAG app supporting:
- Multi-document upload (PDF/TXT/MD, optional DOCX)
- Chunking + embeddings with sentence-transformers
- Dual vector stores: ChromaDB (default) and FAISS (runtime switch)
- Semantic retrieval + LLM answer generation
- Inline source citations (doc/page/chunk)
- Persistent chat sessions
- Document library management (reprocess/delete)
- Advanced features: metadata filtering + chat export JSON

## Run
1. `python -m venv .venv && source .venv/bin/activate` (Windows: `.venv\\Scripts\\activate`)
2. `pip install -r requirements.txt`
3. `cp .env.example .env` and fill API key
4. `streamlit run rag_application.py`

## Tests
`pytest -q --disable-warnings --maxfail=1`

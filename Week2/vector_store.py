import os
import shutil
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

CHROMA_DIR = os.path.join(os.getcwd(), "chroma_db")
FAISS_DIR = os.path.join(os.getcwd(), "faiss_db")

class VectorStoreManager:
    def __init__(self, db_type="faiss", embedding_provider="local", api_key=None):
        self.db_type = db_type.lower()
        self.embedding_provider = embedding_provider.lower()
        self.api_key = api_key
        
        # In-memory store of chunks to support BM25 and FAISS reconstruction
        self.all_chunks = []  # list of dicts with {"text": text, "metadata": metadata}
        self.embeddings = self._init_embeddings()
        self.db = None
        self.bm25_retriever = None
        
        # Load existing database if it exists
        self.load_database()

    def _init_embeddings(self):
        """Initialize the selected embedding model."""
        if self.embedding_provider == "openai" and self.api_key:
            return OpenAIEmbeddings(openai_api_key=self.api_key)
        elif self.embedding_provider == "gemini" and self.api_key:
            # We can use OpenAIEmbeddings pointing to Google's API, or use a simple langchain-google-genai if imported
            try:
                from langchain_google_genai import GoogleGenAIEmbeddings
                return GoogleGenAIEmbeddings(model="models/embedding-001", google_api_key=self.api_key)
            except ImportError:
                # Fallback to local HuggingFace if not installed
                pass
                
        # Default local HuggingFace embeddings
        # HuggingFaceEmbeddings is clean and runs locally
        # Using a small and fast model: all-MiniLM-L6-v2
        try:
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
        except Exception as e:
            # Fallback mock embedding for environment safety if HuggingFace fails to load/download
            print(f"Warning: Failed to load local HuggingFace model ({e}). Using mock embeddings.")
            class MockEmbeddings:
                def embed_documents(self, texts):
                    # Return deterministic dummy vectors of size 384
                    return [[0.1] * 384 for _ in texts]
                def embed_query(self, text):
                    return [0.1] * 384
            return MockEmbeddings()

    def load_database(self):
        """Load an existing database index if present."""
        if not self.all_chunks:
            return
            
        try:
            # Convert cached dict chunks back to LangChain Document objects
            docs = [Document(page_content=c["text"], metadata=c["metadata"]) for c in self.all_chunks]
            
            if self.db_type == "chroma":
                # Re-create/load Chroma
                if os.path.exists(CHROMA_DIR):
                    self.db = Chroma(persist_directory=CHROMA_DIR, embedding_function=self.embeddings)
                else:
                    self.db = Chroma.from_documents(docs, self.embeddings, persist_directory=CHROMA_DIR)
            else:
                # Re-create FAISS
                self.db = FAISS.from_documents(docs, self.embeddings)
                
            self._update_bm25()
        except Exception as e:
            print(f"Error loading database: {e}")
            self.db = None

    def _update_bm25(self):
        """Update the BM25 keyword index using the current chunks."""
        if not self.all_chunks:
            self.bm25_retriever = None
            return
            
        docs = [Document(page_content=c["text"], metadata=c["metadata"]) for c in self.all_chunks]
        self.bm25_retriever = BM25Retriever.from_documents(docs)

    def add_chunks(self, chunks: list):
        """
        Add new document chunks to the active vector database.
        chunks: list of dicts with {"text": text, "metadata": metadata}
        """
        if not chunks:
            return
            
        # Append to our local in-memory log
        self.all_chunks.extend(chunks)
        
        # Convert to LangChain Documents
        docs = [Document(page_content=c["text"], metadata=c["metadata"]) for c in chunks]
        
        # Add to the selected vector store
        if self.db_type == "chroma":
            if self.db is None:
                self.db = Chroma.from_documents(docs, self.embeddings, persist_directory=CHROMA_DIR)
            else:
                self.db.add_documents(docs)
        else:  # FAISS
            if self.db is None:
                self.db = FAISS.from_documents(docs, self.embeddings)
            else:
                # FAISS allows adding documents
                self.db.add_documents(docs)
                
        # Re-build BM25 index with all chunks
        self._update_bm25()

    def delete_document(self, doc_name: str):
        """Delete all chunks belonging to a document from the vector store."""
        # Filter chunks cache
        self.all_chunks = [c for c in self.all_chunks if c["metadata"]["source"] != doc_name]
        
        # Clean disk or memory
        if self.db_type == "chroma":
            if self.db is not None:
                try:
                    # Chroma supports deleting by metadata query
                    self.db.delete(where={"source": doc_name})
                except Exception:
                    # Rebuild from scratch if delete fails
                    self.db = None
                    if os.path.exists(CHROMA_DIR):
                        shutil.rmtree(CHROMA_DIR)
                    self.load_database()
            else:
                if os.path.exists(CHROMA_DIR):
                    shutil.rmtree(CHROMA_DIR)
        else:  # FAISS
            # FAISS does not easily support metadata deletion directly, so we rebuild the index
            self.db = None
            if os.path.exists(FAISS_DIR):
                shutil.rmtree(FAISS_DIR)
            if self.all_chunks:
                self.load_database()
                
        # Update BM25
        self._update_bm25()

    def refresh_embeddings(self, new_embedding_provider, new_api_key=None):
        """Re-generate embeddings for all current chunks with a new provider."""
        self.embedding_provider = new_embedding_provider.lower()
        self.api_key = new_api_key
        self.embeddings = self._init_embeddings()
        
        # Clear database
        self.db = None
        if os.path.exists(CHROMA_DIR):
            shutil.rmtree(CHROMA_DIR)
            
        # Rebuild database with existing chunks using new embeddings
        if self.all_chunks:
            self.load_database()

    def clear_all(self):
        """Reset the vector stores and chunk cache."""
        self.all_chunks = []
        self.db = None
        self.bm25_retriever = None
        
        # Clean Chroma
        if os.path.exists(CHROMA_DIR):
            try:
                shutil.rmtree(CHROMA_DIR)
            except Exception as e:
                print(f"Error cleaning Chroma directory: {e}")
                
        # Clean FAISS
        if os.path.exists(FAISS_DIR):
            try:
                shutil.rmtree(FAISS_DIR)
            except Exception as e:
                print(f"Error cleaning FAISS directory: {e}")

    def similarity_search(self, query: str, k: int = 4, doc_filter: str = None) -> list:
        """Perform semantic search only."""
        if self.db is None:
            return []
            
        # Format metadata filter if selected
        search_filter = None
        if doc_filter:
            if self.db_type == "chroma":
                search_filter = {"source": doc_filter}
            else:
                # FAISS uses a function filter
                search_filter = lambda metadata: metadata.get("source") == doc_filter
                
        try:
            # Query the vector store
            if self.db_type == "chroma":
                return self.db.similarity_search(query, k=k, filter=search_filter)
            else:
                return self.db.similarity_search(query, k=k, filter=search_filter)
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []

    def hybrid_search(self, query: str, k: int = 4, doc_filter: str = None) -> list:
        """
        Combine Semantic (dense vector) and Keyword (BM25 sparse vector) search results.
        Blends them using Reciprocal Rank Fusion (RRF) or weighted ordering.
        """
        # If no BM25 retriever or no database, fall back to standard semantic or return empty
        if self.db is None:
            return []
            
        # 1. Fetch semantic results
        semantic_results = self.similarity_search(query, k=k*2, doc_filter=doc_filter)
        
        # 2. Fetch keyword results (BM25)
        bm25_results = []
        if self.bm25_retriever:
            try:
                # BM25 is just on the corpus, filter manually afterwards or check if filters are supported
                all_bm25 = self.bm25_retriever.invoke(query)
                if doc_filter:
                    bm25_results = [doc for doc in all_bm25 if doc.metadata.get("source") == doc_filter][:k*2]
                else:
                    bm25_results = all_bm25[:k*2]
            except Exception as e:
                print(f"Error in BM25 retrieval: {e}")
                bm25_results = []
                
        # 3. Reciprocal Rank Fusion (RRF)
        # Score = Sum (1 / (rank + 60))
        rrf_scores = {}
        
        def add_scores(results_list):
            for rank, doc in enumerate(results_list):
                # Use a unique identifier (source + chunk_index or content hash)
                doc_id = (doc.metadata.get("source"), doc.metadata.get("chunk_index"), hash(doc.page_content))
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = {"doc": doc, "score": 0.0}
                rrf_scores[doc_id]["score"] += 1.0 / (rank + 60.0)
                
        add_scores(semantic_results)
        add_scores(bm25_results)
        
        # Sort by score descending
        sorted_docs = sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)
        
        # Return top K docs
        return [item["doc"] for item in sorted_docs[:k]]

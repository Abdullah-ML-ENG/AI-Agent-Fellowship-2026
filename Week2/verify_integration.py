import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

print("[*] Starting Enterprise Document Intelligence Platform integration verification...")

# 1. Test Auth Import
try:
    import auth
    print("[+] auth.py imported successfully.")
except Exception as e:
    print(f"[-] Error importing auth.py: {e}")
    sys.exit(1)

# 2. Test Document Processor
try:
    import document_processor
    mock_txt = b"Hello this is a test document. It contains some text content about financial markets and algorithms. We need to verify that document parsing and chunking works perfectly."
    res = document_processor.process_document("test_doc.txt", mock_txt, chunk_size=50, chunk_overlap=10)
    
    if res["success"]:
        print(f"[+] document_processor.py works. Parsed {res['pages']} page(s), created {res['chunk_count']} chunks.")
        test_chunks = res["chunks"]
    else:
        print(f"[-] document_processor.py returned failure: {res['error']}")
        sys.exit(1)
except Exception as e:
    print(f"[-] Error testing document_processor.py: {e}")
    sys.exit(1)

# 3. Test Vector Store & Hybrid Search
try:
    import vector_store
    # Instantiate with local mock/SentenceTransformers
    manager = vector_store.VectorStoreManager(db_type="faiss", embedding_provider="local")
    manager.add_chunks(test_chunks)
    
    # Try a search
    results = manager.similarity_search("financial markets", k=1)
    if results:
        print(f"[+] vector_store.py works. Successfully indexed chunks and retrieved: '{results[0].page_content[:40]}...'")
    else:
        print("[-] vector_store.py failed to retrieve any results.")
        sys.exit(1)
except Exception as e:
    print(f"[-] Error testing vector_store.py: {e}")
    sys.exit(1)

# 4. Test Chat Engine (Mock mode)
try:
    import chat_engine
    engine = chat_engine.ChatEngine(provider="mock")
    response = engine.ask("financial markets question", results, [])
    if "Demo Mode" in response["answer"]:
        print("[+] chat_engine.py works (Mock mode verified).")
    else:
        print(f"[-] chat_engine.py returned unexpected answer: {response['answer']}")
        sys.exit(1)
except Exception as e:
    print(f"[-] Error testing chat_engine.py: {e}")
    sys.exit(1)

print("\n[+] ALL SYSTEMS OK! The integration verification completed successfully. The application is ready to run.")

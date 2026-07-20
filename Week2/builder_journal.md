# Builder Journal: Enterprise Document Intelligence Platform

*A project diary of a CS Bachelor student documenting what worked, the absolute nightmares faced during debugging, and the lessons learned about Retrieval-Augmented Generation (RAG) systems.*

---

## 1. What Worked Well?

- **Dynamic Database Swapping**: Saving the text chunks in Streamlit session state (`st.session_state.processed_chunks`) turned out to be a massive win. When a user switches between FAISS and ChromaDB in the sidebar, the system automatically indices the cached chunks in the new database. It’s instant and doesn't require the user to re-upload files.
- **Unified LLM API Client**: Wrapping OpenAI, Google Gemini, and Groq inside a single `ChatEngine` class was a great choice. It made switching from a local mock model to Groq’s high-speed Llama 3.3 models super easy.
- **Custom UI Theming**: Injecting styling overrides directly onto Streamlit elements (like `.stApp`, `[data-testid="stSidebar"]`, and metrics blocks) worked beautifully. We built a real-time Light/Dark mode switcher that changes the entire color palette instantly without refreshing the page or restarting the server.
- **File Parsing & Chunking**: Using `pypdf` for PDFs and `python-docx` for Word documents was extremely reliable. The Recursive Text Splitter chunked the text cleanly, keeping sentences intact.

---

## 2. What Challenges Did You Face?

- **The Windows Store Python Alias Trap**: When I first ran `python`, Windows tried to redirect me to the Microsoft Store to install Python, completely ignoring my local installation! I had to find the absolute path to the virtual environment binary (`C:\Users\win 11\AppData\Local\Python\pythoncore-3.14-64\python.exe`) to run commands.
- **Streamlit Watcher / Torchvision Crash**: Streamlit has a built-in file watcher that scans all imported modules for changes. When I imported `sentence-transformers`, Streamlit scanned its sub-modules, encountered a lazy import for `torchvision` (which wasn't installed), and crashed the app. This was a head-scratcher since we only process text, not images.
- **Groq Model Deprecations**: The initial default model `llama-3.3-70b-specdec` was suddenly decommissioned by Groq, causing API queries to fail with HTTP 400 errors. 
- **One-Step Session State Theme Lag**: At first, toggling between Light and Dark mode had a annoying one-step lag. If I selected Dark, it would display Light, and vice versa, because Streamlit rendered the top-of-file CSS *before* reading the sidebar radio state.

---

## 3. How Did You Debug Problems?

- **Custom Integration Scripts**: I wrote `verify_integration.py` to test the backend modules (auth, parsing, vector database indexing, and query generation) without starting the Streamlit frontend. This helped isolate issues like missing dependencies and syntax errors quickly.
- **Streamlit Config Customization**: To resolve the `torchvision` crash, I disabled Streamlit's source watcher by editing `.streamlit/config.toml` and setting `fileWatcherType = "none"`. This stopped Streamlit from scanning third-party libraries, resolving the crash and making the app boot up much faster.
- **Streamlit Callbacks**: To fix the theme switching lag, I defined a `change_theme()` callback function and bound it to the sidebar radio button using the `on_change` parameter. This forced Streamlit to update the state variable *before* re-running the script from top to bottom, making the transition instant.
- **Groq Model Resolution**: Checked Groq's developer console and switched our default configuration to the active model: `llama-3.3-70b-versatile` and added the super-fast `llama-3.1-8b-instant` as a secondary option.

---

## 4. What Would You Improve?

- **Metadata Database Persistence**: Currently, document metadata is saved in memory (Session State). If the app restarts, the metadata lists are cleared, even though the vector database files remain on disk. I would write a lightweight SQLite database in the workspace to save document summaries, upload dates, and page counts persistently.
- **Matryoshka Dimension Compression**: For API-based embeddings, I would implement dimension reduction (e.g. compressing OpenAI embeddings from 1536 down to 256 dimensions) to speed up FAISS vector lookups and save local storage space.
- **Semantic Chunking Integration**: I want to add an option in the UI to switch from structural character chunking to semantic chunking, calculating cosine distance between consecutive sentences to keep paragraphs more cohesive.

---

## 5. What Did You Learn About RAG?

- **Ingestion is 80% of the Battle**: To be honest, I thought RAG was mostly about complex prompts and LLMs. But I realized that if your document parsers output garbage text, or if your chunking boundaries are messy, no LLM can save you. High-precision extraction is key.
- **Hybrid Search is a Lifesaver**: Dense vector search is smart with synonyms, but it is terrible with exact keywords, part numbers, or system codes. Combining dense search with traditional BM25 keyword matching via Reciprocal Rank Fusion (RRF) makes the retriever twice as reliable.
- **Re-ranking is Essential**: In long documents, LLMs suffer from "lost in the middle" (ignoring facts buried in the middle of long contexts). Running a Cross-Encoder reranker to filter out noise and sort the top-5 documents is critical to ensuring accurate grounding.
- **API Cost Control**: Running RAG systems requires budget discipline. Estimating tokens and displaying costs in the dashboard helped me realize how quickly completions and prompt injections add up.

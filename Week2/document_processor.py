import io
import re
from pypdf import PdfReader
from docx import Document as DocxDocument

# Pure Python RecursiveCharacterTextSplitter — no torch/ML dependencies
class RecursiveCharacterTextSplitter:
    """
    Minimal drop-in replacement for LangChain's RecursiveCharacterTextSplitter.
    Uses only the Python standard library — no torch, no sentence_transformers.
    """
    def __init__(self, chunk_size=1000, chunk_overlap=200, length_function=len,
                 separators=None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> list:
        return self._split(text, self.separators)

    def _split(self, text: str, separators: list) -> list:
        chunks = []
        separator = separators[-1]
        for sep in separators:
            if sep == "":
                separator = sep
                break
            if sep in text:
                separator = sep
                break

        splits = text.split(separator) if separator else list(text)
        good_splits = []
        for s in splits:
            if self.length_function(s) < self.chunk_size:
                good_splits.append(s)
            else:
                if good_splits:
                    chunks.extend(self._merge(good_splits, separator))
                    good_splits = []
                next_seps = separators[separators.index(separator) + 1:] if separator in separators else [""]
                chunks.extend(self._split(s, next_seps))
        if good_splits:
            chunks.extend(self._merge(good_splits, separator))
        return chunks

    def _merge(self, splits: list, separator: str) -> list:
        chunks = []
        current = []
        current_len = 0
        for s in splits:
            s_len = self.length_function(s)
            sep_len = self.length_function(separator) if current else 0
            if current_len + sep_len + s_len > self.chunk_size and current:
                chunk_text = separator.join(current).strip()
                if chunk_text:
                    chunks.append(chunk_text)
                # Keep overlap
                while current and (current_len > self.chunk_overlap or
                                   (current_len + sep_len + s_len > self.chunk_size and current_len > 0)):
                    removed = current.pop(0)
                    current_len -= self.length_function(removed) + self.length_function(separator)
                    current_len = max(current_len, 0)
            current.append(s)
            current_len += s_len + (self.length_function(separator) if len(current) > 1 else 0)
        if current:
            chunk_text = separator.join(current).strip()
            if chunk_text:
                chunks.append(chunk_text)
        return chunks

def clean_text(text: str) -> str:
    """Clean extracted text from unnecessary whitespaces and artifacts."""
    if not text:
        return ""
    # Normalize unicode and whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove multiple newlines but preserve paragraph spacing where appropriate
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def extract_pdf_content(file_bytes: bytes) -> list:
    """Extract page-by-page text from PDF file bytes."""
    pages_content = []
    pdf_file = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages_content.append({
                "text": text,  # Keep raw text, we clean it before chunking
                "page": i + 1  # 1-indexed page
            })
            
    # Fallback if no text extracted (e.g. scanned PDF without OCR)
    if not pages_content:
        pages_content.append({
            "text": "[Scanned PDF or Empty Document - Text Extraction Failed]",
            "page": 1
        })
        
    return pages_content

def extract_docx_content(file_bytes: bytes) -> list:
    """Extract text from DOCX file bytes."""
    docx_file = io.BytesIO(file_bytes)
    doc = DocxDocument(docx_file)
    
    full_text = []
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            full_text.append(paragraph.text)
            
    text_content = "\n\n".join(full_text)
    
    if not text_content.strip():
        text_content = "[Empty DOCX Document]"
        
    return [{"text": text_content, "page": 1}]

def extract_text_content(file_bytes: bytes) -> list:
    """Extract text from plain TXT file bytes."""
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        # Fallback to latin-1
        text = file_bytes.decode("latin-1")
        
    if not text.strip():
        text = "[Empty Text Document]"
        
    return [{"text": text, "page": 1}]

def extract_markdown_content(file_bytes: bytes) -> list:
    """Extract text from Markdown file bytes."""
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")
        
    if not text.strip():
        text = "[Empty Markdown Document]"
        
    return [{"text": text, "page": 1}]

def process_document(file_name: str, file_bytes: bytes, chunk_size: int = 1000, chunk_overlap: int = 200) -> dict:
    """
    Process an uploaded document: extracts text based on format,
    cleans, chunks it, and returns details.
    
    Returns a dictionary containing:
        - "success": bool
        - "error": str or None
        - "pages": int (total page count)
        - "chunks": list of dicts (chunk data with text and metadata)
        - "chunk_count": int
        - "char_count": int
    """
    ext = file_name.split(".")[-1].lower()
    
    try:
        # Extract text based on file format
        if ext == "pdf":
            pages_data = extract_pdf_content(file_bytes)
        elif ext == "docx":
            pages_data = extract_docx_content(file_bytes)
        elif ext == "txt":
            pages_data = extract_text_content(file_bytes)
        elif ext in ["md", "markdown"]:
            pages_data = extract_markdown_content(file_bytes)
        else:
            return {
                "success": False,
                "error": f"Unsupported file extension: .{ext}",
                "pages": 0,
                "chunks": [],
                "chunk_count": 0,
                "char_count": 0
            }
            
        # Count total characters and pages
        total_chars = sum(len(page["text"]) for page in pages_data)
        total_pages = len(pages_data)
        
        # Split text into chunks using LangChain splitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        
        processed_chunks = []
        chunk_idx = 0
        
        for page_data in pages_data:
            page_text = page_data["text"]
            page_num = page_data["page"]
            
            # Split the text of this specific page
            page_chunks = splitter.split_text(page_text)
            
            for chunk_text in page_chunks:
                cleaned_chunk = clean_text(chunk_text)
                if not cleaned_chunk:
                    continue
                    
                processed_chunks.append({
                    "text": cleaned_chunk,
                    "metadata": {
                        "source": file_name,
                        "page": page_num,
                        "chunk_index": chunk_idx,
                        "char_count": len(cleaned_chunk)
                    }
                })
                chunk_idx += 1
                
        return {
            "success": True,
            "error": None,
            "pages": total_pages,
            "chunks": processed_chunks,
            "chunk_count": len(processed_chunks),
            "char_count": total_chars
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error parsing document: {str(e)}",
            "pages": 0,
            "chunks": [],
            "chunk_count": 0,
            "char_count": 0
        }

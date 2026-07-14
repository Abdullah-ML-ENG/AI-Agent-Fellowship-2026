import re
from openai import OpenAI
import google.generativeai as genai
from groq import Groq

def estimate_tokens(text: str) -> int:
    """Approximate token count for a given text."""
    if not text:
        return 0
    char_count = len(text)
    word_count = len(text.split())
    return max(int(char_count / 4), int(word_count / 0.75))

def generate_summary(text: str, filename: str, provider: str = "local", api_key: str = None) -> str:
    """Generate a clean summary of the document text."""
    provider = provider.lower()
    
    # 1. API Summarization if key is provided
    if api_key and provider != "local":
        prompt = (
            f"Please generate a concise, professional executive summary of the document '{filename}'. "
            "Highlight the main topics, key findings, and structure of the document in 3-5 bullet points.\n\n"
            f"Document Text excerpt:\n{text[:6000]}"
        )
        
        try:
            if provider == "openai":
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=300
                )
                return response.choices[0].message.content.strip()
            elif provider == "gemini":
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                return response.text.strip()
            elif provider == "groq":
                client = Groq(api_key=api_key)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=300
                )
                return response.choices[0].message.content.strip()
        except Exception as e:
            # Fallback to local on API error
            pass
            
    # 2. Local/Offline Heuristic Summary
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
    intro = ""
    if paragraphs:
        intro = paragraphs[0]
        if len(intro) > 300:
            intro = intro[:300] + "..."
            
    summary = (
        f"📋 **[Executive Summary - Heuristic]**\n\n"
        f"This is an automatically generated summary of **{filename}**.\n\n"
        f"**Introductory Content:**\n{intro or 'No text structure found.'}\n\n"
        f"**Document Statistics:**\n"
        f"- Total characters: {len(text):,}\n"
        f"- Approximate word count: {len(text.split()):,}\n"
        f"- Est. Token density: {estimate_tokens(text):,} tokens\n\n"
        f"*(For an advanced AI summary, configure your LLM API Key).* "
    )
    return summary

def generate_suggested_questions(text: str, filename: str, provider: str = "local", api_key: str = None) -> list:
    """Generate 3 relevant sample questions a user might ask about the document."""
    provider = provider.lower()
    
    # 1. API generation if keys are present
    if api_key and provider != "local":
        prompt = (
            f"Based on the following document excerpt from '{filename}', generate exactly 3 short, "
            "highly specific questions that a user might ask to query this document. "
            "Output only the questions as a bulleted list, one per line. Do not number them or add intro text.\n\n"
            f"Document Excerpt:\n{text[:3000]}"
        )
        try:
            questions = []
            raw_qs = []
            if provider == "openai":
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=150
                )
                raw_qs = response.choices[0].message.content.strip().split("\n")
            elif provider == "gemini":
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                raw_qs = response.text.strip().split("\n")
            elif provider == "groq":
                client = Groq(api_key=api_key)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=150
                )
                raw_qs = response.choices[0].message.content.strip().split("\n")
                
            for q in raw_qs:
                cleaned_q = re.sub(r'^[\s\-\*\d\.\)]+', '', q).strip()
                if cleaned_q and len(cleaned_q) > 10:
                    questions.append(cleaned_q)
            if len(questions) >= 3:
                return questions[:3]
        except Exception:
            pass

    # 2. Local heuristic fallback
    text_lower = text.lower()
    questions = []
    
    # Finance or report matching
    if any(k in text_lower for k in ["revenue", "profit", "quarter", "fiscal", "dollar", "$", "financial"]):
        questions = [
            f"What are the key financial performance numbers in {filename}?",
            "What is the revenue or net growth details reported?",
            "Are there any financial risks or expenses listed?"
        ]
    # Technical or code matching
    elif any(k in text_lower for k in ["function", "code", "install", "module", "class", "database"]):
        questions = [
            f"How do I install or configure the system in {filename}?",
            "What are the main functions, modules, or classes described?",
            "What is the structure of the database or code architecture?"
        ]
    # Agreement/Legal matching
    elif any(k in text_lower for k in ["agreement", "party", "licensor", "indemnity", "termination", "court"]):
        questions = [
            f"What are the termination clauses or periods in {filename}?",
            "Who are the signing parties and their core obligations?",
            "Is there any liability or indemnity limit defined?"
        ]
    else:
        # Default questions
        questions = [
            f"Summarize the key sections of {filename}.",
            "What is the primary topic or goal of this document?",
            "What are the main conclusions or next steps outlined?"
        ]
        
    return questions

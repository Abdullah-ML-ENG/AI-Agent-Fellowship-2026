import os
from openai import OpenAI
import google.generativeai as genai
from groq import Groq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

class ChatEngine:
    def __init__(self, provider="openai", api_key=None, model_name=None):
        self.provider = provider.lower()
        self.api_key = api_key
        
        # Default models
        if self.provider == "openai":
            self.model_name = model_name or "gpt-4o-mini"
        elif self.provider == "gemini":
            self.model_name = model_name or "gemini-1.5-flash"
        elif self.provider == "groq":
            self.model_name = model_name or "llama-3.3-70b-versatile"
        else:
            self.model_name = "mock"

        # Initialize clients
        self.openai_client = None
        self.gemini_model = None
        self.groq_client = None
        
        if self.api_key:
            if self.provider == "openai":
                self.openai_client = OpenAI(api_key=self.api_key)
            elif self.provider == "gemini":
                genai.configure(api_key=self.api_key)
                self.gemini_model = genai.GenerativeModel(self.model_name)
            elif self.provider == "groq":
                self.groq_client = Groq(api_key=self.api_key)

    def generate_prompt(self, query: str, context_docs: list) -> str:
        """Format the retrieved chunks and prompt for the LLM."""
        context_str = ""
        for i, doc in enumerate(context_docs):
            meta = doc.metadata
            page_info = f", Page {meta.get('page')}" if meta.get('page') else ""
            context_str += f"--- SOURCE {i+1}: {meta.get('source')}{page_info} ---\n"
            context_str += f"{doc.page_content}\n\n"
            
        system_prompt = (
            "You are a professional Enterprise Document Intelligence Platform Assistant. "
            "Your goal is to answer the user's question using ONLY the provided document sources. "
            "Please follow these instructions strictly:\n"
            "1. Answer the question comprehensively and professionally using the sources.\n"
            "2. If the source material does not contain the answer, state: 'I cannot find the answer in the uploaded documents.' and do not make up facts.\n"
            "3. For every claim you make, cite the source number (e.g., [Source 1], [Source 2]) at the end of the sentence where it is mentioned.\n"
            "4. Keep your tone neutral, professional, and clear.\n\n"
            f"Here are the retrieved sources:\n{context_str}\n"
            f"User Question: {query}"
        )
        return system_prompt

    def ask(self, query: str, context_docs: list, chat_history: list) -> dict:
        """
        Queries the selected LLM and returns the response, token counts, and citations.
        
        chat_history: list of dicts: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
        """
        # Formulate prompt
        prompt = self.generate_prompt(query, context_docs)
        
        tokens_used = 0
        estimated_cost = 0.0
        response_text = ""
        
        # 1. Mock Mode (If no API Key is provided)
        if not self.api_key:
            response_text = self._mock_response(query, context_docs)
            tokens_used = len(prompt.split()) + len(response_text.split())
            return {
                "answer": response_text,
                "tokens": tokens_used,
                "cost": 0.0,
                "sources": context_docs
            }
            
        # 2. OpenAI Execution
        if self.provider == "openai" and self.openai_client:
            try:
                messages = []
                messages.append({"role": "system", "content": "You are a helpful enterprise assistant. Answer queries using the context provided in user prompts."})
                for msg in chat_history[-4:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
                messages.append({"role": "user", "content": prompt})
                
                response = self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=800
                )
                
                response_text = response.choices[0].message.content
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                tokens_used = prompt_tokens + completion_tokens
                estimated_cost = (prompt_tokens * 0.00000015) + (completion_tokens * 0.00000060)
                
            except Exception as e:
                response_text = f"Error communicating with OpenAI API: {str(e)}"
                
        # 3. Gemini Execution
        elif self.provider == "gemini" and self.gemini_model:
            try:
                gemini_history = []
                for msg in chat_history[-4:]:
                    role = "user" if msg["role"] == "user" else "model"
                    gemini_history.append({"role": role, "parts": [msg["content"]]})
                
                chat = self.gemini_model.start_chat(history=gemini_history)
                response = chat.send_message(prompt)
                
                response_text = response.text
                input_tokens = len(prompt.split()) * 1.3
                output_tokens = len(response_text.split()) * 1.3
                tokens_used = int(input_tokens + output_tokens)
                estimated_cost = (input_tokens * 0.000000075) + (output_tokens * 0.00000030)
                
            except Exception as e:
                response_text = f"Error communicating with Gemini API: {str(e)}"
                
        # 4. Groq Execution
        elif self.provider == "groq" and self.groq_client:
            try:
                messages = []
                messages.append({"role": "system", "content": "You are a helpful enterprise assistant. Answer queries using the context provided in user prompts."})
                for msg in chat_history[-4:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
                messages.append({"role": "user", "content": prompt})
                
                response = self.groq_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=800
                )
                
                response_text = response.choices[0].message.content
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                tokens_used = prompt_tokens + completion_tokens
                
                # Estimate cost for llama-3.3-70b: Input: $0.59/1M, Output: $0.79/1M
                # (Lower rates apply for smaller models, but this acts as a safe, realistic estimate)
                estimated_cost = (prompt_tokens * 0.00000059) + (completion_tokens * 0.00000079)
                
            except Exception as e:
                response_text = f"Error communicating with Groq API: {str(e)}"
                
        else:
            response_text = "Unsupported provider or API client not initialized."
            
        return {
            "answer": response_text,
            "tokens": tokens_used,
            "cost": estimated_cost,
            "sources": context_docs
        }

    def _mock_response(self, query: str, context_docs: list) -> str:
        """Generate a simulated response using context chunks when offline/API key is missing."""
        if not context_docs:
            return (
                "ℹ️ **[Demo Mode - No API Key Entered]**\n\n"
                "I cannot answer your question because no documents have been uploaded or processed. "
                "Please upload a document to begin semantic search."
            )
            
        # Try to find matching words
        query_words = set(query.lower().split())
        best_doc = None
        best_overlap = -1
        
        for doc in context_docs:
            doc_words = set(doc.page_content.lower().split())
            overlap = len(query_words.intersection(doc_words))
            if overlap > best_overlap:
                best_overlap = overlap
                best_doc = doc
                
        best_doc = best_doc or context_docs[0]
        meta = best_doc.metadata
        page_info = f"page {meta.get('page')}" if meta.get('page') else "doc reference"
        
        return (
            "🤖 **[Demo Mode - Simulated Answer]**\n\n"
            f"Based on the document **{meta.get('source')}** ({page_info}), here is the most relevant snippet:\n\n"
            f"> \"...{best_doc.page_content[:400]}...\"\n\n"
            "*(To enable natural intelligence and get a real answer, please enter your API Key in the sidebar).* [Source 1]"
        )

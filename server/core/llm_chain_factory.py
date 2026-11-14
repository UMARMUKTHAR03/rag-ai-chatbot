from typing import List, Dict, Any, Optional
from core.multimodal.service import MultimodalService
from core.vector_database import get_session_vectorstore
from utils.logger import logger

RAG_SYSTEM_PROMPT = """You are OmniMind AI — an advanced multimodal knowledge assistant.
Your goal is to answer questions thoroughly, accurately, and with strict intellectual honesty.

CORE OPERATIONAL PRINCIPLES:
1. GROUNDED KNOWLEDGE: When user queries pertain to uploaded documents, images, or audio transcripts, synthesize your response strictly from the retrieved context.
2. CITATION DISCLOSURE: Attribute key facts to their source document and location (e.g. [Document: annual_report.pdf, Page 4]).
3. FACTUAL INTEGRITY: If the retrieved documents do not contain the answer, explicitly state:
   "The answer was not found in the uploaded documents."
   Do NOT invent facts, numbers, dates, or source citations.
4. MULTIMODAL SYNTHESIS: Connect observations from uploaded images, audio transcripts, and documents into a unified, coherent explanation.
"""

def generate_rag_response(
    query: str,
    session_id: str = "default",
    model_provider: str = "gemini",
    model_name: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    use_rag: bool = True
) -> Dict[str, Any]:
    """
    Executes grounded RAG retrieval, context assembly, and LLM answer generation.
    Returns the generated answer along with verified source citations.
    """
    store = get_session_vectorstore(session_id=session_id, model_provider=model_provider)
    citations: List[Dict[str, Any]] = []
    context_text = ""

    if use_rag and store.count() > 0:
        retrieved = store.search(query=query, top_k=4, threshold=0.04)
        if retrieved:
            context_blocks = []
            for item in retrieved:
                meta = item.get("metadata", {})
                source = meta.get("source", "Document")
                page = meta.get("page") or meta.get("slide") or meta.get("sheet") or meta.get("chunk_index", 1)
                file_type = meta.get("file_type", "Document")
                score = item.get("similarity_score", 0.0)

                citations.append({
                    "source": source,
                    "location": f"Page/Unit {page}",
                    "file_type": file_type,
                    "similarity_score": score,
                    "snippet": item.get("content", "")[:180] + "..."
                })

                context_blocks.append(
                    f"--- SOURCE: {source} ({file_type}, Location: {page}, Relevance: {score:.2f}) ---\n"
                    f"{item.get('content', '')}\n"
                )

            context_text = "\n".join(context_blocks)

    messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT}]

    # Include recent conversation turns for context-awareness
    if conversation_history:
        for turn in conversation_history[-6:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            if role in ["user", "assistant"] and content:
                messages.append({"role": role, "content": content})

    if context_text:
        user_prompt = (
            f"RETRIEVED KNOWLEDGE SOURCES:\n{context_text}\n\n"
            f"USER QUESTION:\n{query}\n\n"
            f"Please provide an accurate, grounded answer citing the specific sources above where applicable."
        )
    else:
        user_prompt = query

    messages.append({"role": "user", "content": user_prompt})

    llm_output = MultimodalService.chat_completion(
        messages=messages,
        provider=model_provider,
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens
    )

    return {
        "answer": llm_output.get("text", ""),
        "model": llm_output.get("model", ""),
        "provider": llm_output.get("provider", model_provider),
        "citations": citations,
        "context_used": bool(context_text),
        "retrieved_chunk_count": len(citations)
    }

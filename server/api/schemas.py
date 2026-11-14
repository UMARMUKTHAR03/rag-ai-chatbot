from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class StandardAPIResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[Any] = None

class SearchQueryRequest(BaseModel):
    query: str
    model_provider: str = "gemini"
    session_id: Optional[str] = "default"
    top_k: int = 4

class ChatMessage(BaseModel):
    role: str
    content: str
    image_url: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    model_name: Optional[str] = None
    model_provider: str = "gemini"
    session_id: Optional[str] = "default"
    conversation_history: Optional[List[ChatMessage]] = Field(default_factory=list)
    temperature: float = 0.7
    max_tokens: int = 1024
    use_rag: bool = True

class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    file_type: str
    page_count: int = 1
    chunk_count: int = 0
    upload_timestamp: str
    file_size_bytes: int = 0
    session_id: str = "default"

class ImageAnalysisRequest(BaseModel):
    prompt: Optional[str] = "Analyze this image and describe its key elements in detail."
    model_provider: str = "gemini"
    model_name: Optional[str] = None
    session_id: Optional[str] = "default"

class SynthesizeSpeechRequest(BaseModel):
    text: str
    voice: Optional[str] = "alloy"

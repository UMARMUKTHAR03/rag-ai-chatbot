import os
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query

from config.settings import (
    MODEL_OPTIONS,
    APP_NAME,
    APP_TITLE,
    APP_TAGLINE,
    APP_VERSION
)
from core.vector_database import (
    get_session_vectorstore,
    upsert_vectorstore_from_file,
    find_similar_chunks,
    get_collections_count
)
from core.document_processor import save_uploaded_file, validate_uploaded_file, sanitize_session_id, cleanup_session_files
from core.multimodal.service import MultimodalService
from core.llm_chain_factory import generate_rag_response
from api.schemas import (
    SearchQueryRequest,
    ChatRequest,
    StandardAPIResponse,
    DocumentMetadata,
    SynthesizeSpeechRequest
)
from utils.logger import logger

router = APIRouter()

@router.get("/health", response_model=StandardAPIResponse)
def health_check(probe_reachability: bool = Query(False)):
    groq_health = MultimodalService.check_provider_health("groq", test_connectivity=probe_reachability)
    gemini_health = MultimodalService.check_provider_health("gemini", test_connectivity=probe_reachability)

    return StandardAPIResponse(
        status="success",
        message=f"{APP_TITLE} is healthy and operational.",
        data={
            "app_name": APP_NAME,
            "version": APP_VERSION,
            "tagline": APP_TAGLINE,
            "providers": {
                "groq": groq_health,
                "gemini": gemini_health
            },
            "supported_modalities": ["text", "pdf", "docx", "pptx", "csv", "xlsx", "image", "audio"]
        }
    )

@router.get("/capabilities", response_model=StandardAPIResponse)
def get_capabilities():
    return StandardAPIResponse(
        status="success",
        data={
            "modalities": {
                "text": "Multi-turn grounded conversational reasoning",
                "documents": ["PDF", "DOCX", "PPTX", "TXT", "MD", "CSV", "XLSX"],
                "images": ["JPG", "JPEG", "PNG", "WEBP"],
                "audio": ["WAV", "MP3", "M4A", "WEBM"]
            },
            "features": [
                "Session-isolated semantic hybrid retrieval",
                "Zero-hallucination source attribution with page numbers",
                "Direct Groq Whisper audio transcription",
                "Gemini 2.0 Flash and Groq Llama 3.3 multimodal inference",
                "Browser-native and REST-compatible speech playback"
            ]
        }
    )

@router.get("/llm", response_model=StandardAPIResponse)
async def get_llm_options():
    return StandardAPIResponse(
        status="success",
        data=[provider.title() for provider in MODEL_OPTIONS.keys()]
    )

@router.get("/llm/{model_provider}", response_model=StandardAPIResponse)
async def get_llm_models(model_provider: str):
    model_provider = model_provider.lower()
    if model_provider not in MODEL_OPTIONS:
        return StandardAPIResponse(status="error", message=f"Invalid model provider: '{model_provider}'")

    return StandardAPIResponse(
        status="success",
        data=MODEL_OPTIONS[model_provider]["models"]
    )

@router.get("/models", response_model=StandardAPIResponse)
async def get_all_models():
    return StandardAPIResponse(status="success", data=MODEL_OPTIONS)

@router.post("/upload_and_process_pdfs", response_model=StandardAPIResponse)
@router.post("/documents/upload", response_model=StandardAPIResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    model_provider: str = Form("gemini"),
    session_id: str = Form("default")
):
    """
    Accepts single or multi-file uploads across PDF, DOCX, PPTX, TXT, MD, CSV, and XLSX.
    Indexes chunks into session-isolated vector database.
    """
    try:
        session_id = sanitize_session_id(session_id)
        model_provider = model_provider.lower()
        processed_files = []
        total_chunks = 0

        for file in files:
            file_path = await save_uploaded_file(file, session_id=session_id)
            chunks_indexed = await upsert_vectorstore_from_file(
                file_path=file_path,
                original_filename=file.filename,
                session_id=session_id,
                model_provider=model_provider
            )
            total_chunks += chunks_indexed
            processed_files.append({
                "filename": file.filename,
                "chunks_indexed": chunks_indexed,
                "status": "indexed"
            })

        logger.info(f"Processed {len(files)} files ({total_chunks} chunks) for session {session_id}")
        return StandardAPIResponse(
            status="success",
            message=f"Successfully indexed {len(files)} document(s) with {total_chunks} chunks.",
            data={
                "session_id": session_id,
                "total_chunks": total_chunks,
                "files": processed_files
            }
        )
    except Exception as e:
        logger.exception("Error while uploading documents")
        return StandardAPIResponse(status="error", message=str(e))

@router.get("/documents", response_model=StandardAPIResponse)
async def list_documents(
    session_id: str = Query("default"),
    model_provider: str = Query("gemini")
):
    session_id = sanitize_session_id(session_id)
    store = get_session_vectorstore(session_id=session_id, model_provider=model_provider)
    docs = list(store.documents.values())
    return StandardAPIResponse(
        status="success",
        data={
            "session_id": session_id,
            "document_count": len(docs),
            "total_chunks": store.count(),
            "documents": docs
        }
    )

@router.delete("/documents/{document_id}", response_model=StandardAPIResponse)
async def delete_document(
    document_id: str,
    session_id: str = Query("default"),
    model_provider: str = Query("gemini")
):
    session_id = sanitize_session_id(session_id)
    store = get_session_vectorstore(session_id=session_id, model_provider=model_provider)
    deleted = store.delete_document(document_id)
    if deleted:
        return StandardAPIResponse(status="success", message=f"Document {document_id} deleted successfully.")
    else:
        return StandardAPIResponse(status="error", message=f"Document {document_id} not found.")

@router.delete("/sessions/{session_id}", response_model=StandardAPIResponse)
async def clear_session(session_id: str):
    session_id = sanitize_session_id(session_id)
    for prov in ["gemini", "groq"]:
        store = get_session_vectorstore(session_id=session_id, model_provider=prov)
        store.clear()
    cleaned_count = cleanup_session_files(session_id)
    return StandardAPIResponse(
        status="success",
        message=f"Session {session_id} data cleared ({cleaned_count} uploaded files purged)."
    )

@router.post("/vector_store/search", response_model=StandardAPIResponse)
@router.post("/retrieval/search", response_model=StandardAPIResponse)
async def search_vectorstore(request: SearchQueryRequest):
    try:
        session_id = sanitize_session_id(request.session_id or "default")
        results = find_similar_chunks(
            model_provider=request.model_provider,
            query=request.query,
            session_id=session_id,
            top_k=request.top_k
        )
        return StandardAPIResponse(status="success", data=results)
    except Exception as e:
        logger.exception("Error during similarity search")
        return StandardAPIResponse(status="error", message=str(e))

@router.get("/vector_store/count/{model_provider}", response_model=StandardAPIResponse)
async def get_vectorstore_count(model_provider: str, session_id: str = Query("default")):
    try:
        session_id = sanitize_session_id(session_id)
        count = get_collections_count(model_provider, session_id=session_id)
        return StandardAPIResponse(status="success", data=count)
    except Exception as e:
        logger.exception("Error getting collection count")
        return StandardAPIResponse(status="error", message=str(e))

@router.post("/chat", response_model=StandardAPIResponse)
async def chat(request: ChatRequest):
    try:
        session_id = sanitize_session_id(request.session_id or "default")
        provider = request.get_effective_provider()
        res = generate_rag_response(
            query=request.message,
            session_id=session_id,
            model_provider=provider,
            model_name=request.model_name,
            conversation_history=[m.dict() for m in request.conversation_history] if request.conversation_history else [],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            use_rag=request.use_rag
        )
        return StandardAPIResponse(status="success", data=res)
    except Exception as e:
        logger.exception("Error during chat generation")
        return StandardAPIResponse(status="error", message=str(e))

@router.post("/images/analyze", response_model=StandardAPIResponse)
async def analyze_image_endpoint(
    image: UploadFile = File(...),
    prompt: str = Form("Analyze this image, extract any readable text or data, and explain visible objects in detail."),
    model_provider: str = Form("gemini"),
    session_id: str = Form("default"),
    index_description_for_rag: bool = Form(True)
):
    try:
        session_id = sanitize_session_id(session_id)
        validate_uploaded_file(image, max_size_mb=20, allowed_category="image")
        content = await image.read()
        mime_type = image.content_type or "image/jpeg"

        analysis = MultimodalService.analyze_image(
            image_bytes=content,
            mime_type=mime_type,
            prompt=prompt,
            provider=model_provider
        )

        # Index the extracted description into RAG so subsequent user questions can query it
        if index_description_for_rag and analysis.get("description"):
            from core.document_processor import DocumentChunk
            chunk = DocumentChunk(
                page_content=f"Image Description & OCR Analysis ({image.filename}):\n{analysis['description']}",
                metadata={
                    "source": image.filename,
                    "file_type": "Image",
                    "page": 1
                }
            )
            store = get_session_vectorstore(session_id=session_id, model_provider=model_provider)
            doc_id = f"img_{hash(image.filename + str(len(content)))}"
            store.add_chunks(document_id=doc_id, filename=image.filename, chunks=[chunk])

        return StandardAPIResponse(status="success", data=analysis)
    except Exception as e:
        logger.exception("Error during image analysis")
        return StandardAPIResponse(status="error", message=str(e))

@router.post("/audio/transcribe", response_model=StandardAPIResponse)
async def transcribe_audio_endpoint(
    audio: UploadFile = File(...),
    session_id: str = Form("default"),
    model_provider: str = Form("groq"),
    index_transcription_for_rag: bool = Form(True)
):
    try:
        session_id = sanitize_session_id(session_id)
        validate_uploaded_file(audio, max_size_mb=30, allowed_category="audio")
        content = await audio.read()
        result = MultimodalService.transcribe_audio(
            audio_bytes=content,
            filename=audio.filename,
            provider=model_provider
        )

        # Index the transcript into knowledge base
        if index_transcription_for_rag and result.get("text"):
            from core.document_processor import DocumentChunk
            chunk = DocumentChunk(
                page_content=f"Audio Recording Transcript ({audio.filename}):\n{result['text']}",
                metadata={
                    "source": audio.filename,
                    "file_type": "Audio Transcript",
                    "duration": result.get("duration", 0.0),
                    "page": 1
                }
            )
            store = get_session_vectorstore(session_id=session_id, model_provider=model_provider)
            doc_id = f"aud_{hash(audio.filename + str(len(content)))}"
            store.add_chunks(document_id=doc_id, filename=audio.filename, chunks=[chunk])

        return StandardAPIResponse(status="success", data=result)
    except Exception as e:
        logger.exception("Error during audio transcription")
        return StandardAPIResponse(status="error", message=str(e))

@router.post("/audio/synthesize", response_model=StandardAPIResponse)
async def synthesize_speech_endpoint(request: SynthesizeSpeechRequest):
    return StandardAPIResponse(
        status="success",
        message="Client-side speech synthesis available via Web Speech API.",
        data={
            "supported": True,
            "engine": "Web Speech API (Browser-Native High Fidelity)",
            "text": request.text
        }
    )

import pytest
import io
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from core.document_processor import DocumentChunk, split_text_into_chunks, sanitize_filename
from core.vector_database import SemanticVectorIndex
from core.multimodal.service import MultimodalService

client = TestClient(app)

def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["app"] == "OmniMind AI"
    assert "Multimodal" in data["title"]

def test_health_check_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "OmniMind AI" in data["message"]
    assert "providers" in data["data"]
    assert "groq" in data["data"]["providers"]
    assert "gemini" in data["data"]["providers"]

def test_capabilities_endpoint():
    res = client.get("/capabilities")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "modalities" in data["data"]
    assert "PDF" in data["data"]["modalities"]["documents"]
    assert "DOCX" in data["data"]["modalities"]["documents"]
    assert "PPTX" in data["data"]["modalities"]["documents"]

def test_models_endpoints():
    res1 = client.get("/llm")
    assert res1.status_code == 200
    assert "Groq" in res1.json()["data"]

    res2 = client.get("/llm/gemini")
    assert res2.status_code == 200
    assert len(res2.json()["data"]) > 0

    res3 = client.get("/models")
    assert res3.status_code == 200
    assert "groq" in res3.json()["data"]
    assert "gemini" in res3.json()["data"]

def test_document_processor_chunking():
    doc = DocumentChunk(
        page_content="Word " * 600,
        metadata={"source": "test.txt", "file_type": "Text"}
    )
    chunks = split_text_into_chunks([doc], chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 1
    assert chunks[0].metadata["source"] == "test.txt"

def test_sanitize_filename():
    assert sanitize_filename("my test file!@#$%.pdf") == "my_test_file_____.pdf"
    assert sanitize_filename("normal_file.docx") == "normal_file.docx"

def test_semantic_vector_index_session_isolation():
    idx1 = SemanticVectorIndex(session_id="session_A", provider="gemini")
    idx2 = SemanticVectorIndex(session_id="session_B", provider="gemini")

    idx1.clear()
    idx2.clear()

    chunk1 = DocumentChunk("Artificial intelligence and neural network deep learning", {"source": "ai.pdf"})
    chunk2 = DocumentChunk("Agricultural crop rotation techniques for wheat and corn", {"source": "agri.pdf"})

    idx1.add_chunks("doc_1", "ai.pdf", [chunk1])
    idx2.add_chunks("doc_2", "agri.pdf", [chunk2])

    res1 = idx1.search("neural network", top_k=2)
    assert len(res1) > 0
    assert res1[0]["metadata"]["source"] == "ai.pdf"

    # Verify session B cannot retrieve session A's documents
    res2 = idx2.search("neural network", top_k=2)
    assert all(r["metadata"]["source"] != "ai.pdf" for r in res2)

    # Clean up test indexes
    idx1.clear()
    idx2.clear()

def test_document_upload_and_search_txt():
    txt_content = b"OmniMind AI is a state of the art multimodal AI knowledge assistant."
    file = io.BytesIO(txt_content)

    res = client.post(
        "/documents/upload",
        files={"files": ("readme_test.txt", file, "text/plain")},
        data={"session_id": "test_upload_session", "model_provider": "gemini"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    # Search for uploaded content
    search_res = client.post(
        "/retrieval/search",
        json={"query": "multimodal knowledge assistant", "session_id": "test_upload_session", "model_provider": "gemini"}
    )
    assert search_res.status_code == 200
    results = search_res.json()["data"]
    assert len(results) > 0
    assert "OmniMind" in results[0]["content"]

    # Delete session
    del_res = client.delete("/sessions/test_upload_session")
    assert del_res.status_code == 200

def test_chat_without_rag():
    with patch("core.multimodal.service.MultimodalService.chat_completion") as mock_chat:
        mock_chat.return_value = {
            "text": "Hello! I am OmniMind AI.",
            "model": "gemini-2.0-flash",
            "provider": "gemini",
            "usage": {}
        }
        res = client.post(
            "/chat",
            json={"message": "Hello", "use_rag": False, "model_provider": "gemini"}
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["answer"] == "Hello! I am OmniMind AI."
        assert data["context_used"] is False

def test_chat_with_rag_and_citations():
    idx = SemanticVectorIndex(session_id="citation_test_session", provider="gemini")
    idx.clear()
    idx.add_chunks(
        "doc_test",
        "financial_report.pdf",
        [DocumentChunk("In Q4 2026, the company generated $50 million in revenue.", {"source": "financial_report.pdf", "page": 4, "file_type": "PDF"})]
    )

    with patch("core.multimodal.service.MultimodalService.chat_completion") as mock_chat:
        mock_chat.return_value = {
            "text": "According to the financial report, revenue was $50 million in Q4 2026 [Document: financial_report.pdf, Page 4].",
            "model": "gemini-2.0-flash",
            "provider": "gemini",
            "usage": {}
        }
        res = client.post(
            "/chat",
            json={
                "message": "What was the revenue in Q4 2026?",
                "session_id": "citation_test_session",
                "use_rag": True,
                "model_provider": "gemini"
            }
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["context_used"] is True
        assert len(data["citations"]) > 0
        assert data["citations"][0]["source"] == "financial_report.pdf"

    idx.clear()

def test_image_analysis_endpoint_mocked():
    with patch("core.multimodal.service.MultimodalService.analyze_image") as mock_vision:
        mock_vision.return_value = {
            "description": "A financial bar chart displaying quarterly revenue growth.",
            "provider": "gemini",
            "model": "gemini-2.0-flash",
            "mime_type": "image/png"
        }
        dummy_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        res = client.post(
            "/images/analyze",
            files={"image": ("chart.png", io.BytesIO(dummy_png), "image/png")},
            data={"prompt": "Describe this chart", "model_provider": "gemini", "session_id": "img_test"}
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert "financial bar chart" in data["description"]

def test_audio_transcription_endpoint_mocked():
    with patch("core.multimodal.service.MultimodalService.transcribe_audio") as mock_whisper:
        mock_whisper.return_value = {
            "text": "What is the capital of France?",
            "language": "en",
            "duration": 2.5,
            "model": "whisper-large-v3-turbo",
            "provider": "groq",
            "segments": []
        }
        res = client.post(
            "/audio/transcribe",
            files={"audio": ("speech.wav", io.BytesIO(b"RIFFdummydataWAVE"), "audio/wav")},
            data={"session_id": "audio_test", "model_provider": "groq"}
        )
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["text"] == "What is the capital of France?"

def test_synthesize_speech_endpoint():
    res = client.post("/audio/synthesize", json={"text": "Hello from OmniMind AI"})
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert res.json()["data"]["supported"] is True

def test_model_selection_fallback_logic():
    from config.settings import MODEL_OPTIONS
    # Verify default vision models never contain retired models
    assert "meta-llama/llama-4-scout-17b-16e-instruct" not in MODEL_OPTIONS["groq"]["vision_models"]
    assert "llama-3.2-11b-vision-preview" not in MODEL_OPTIONS["groq"]["vision_models"]
    assert "llama-3.2-90b-vision-preview" not in MODEL_OPTIONS["groq"]["vision_models"]
    assert "gemini-1.5-flash" not in MODEL_OPTIONS["gemini"]["vision_models"]
    assert MODEL_OPTIONS["gemini"]["vision_models"][0] == "gemini-3.8-flash"

    # Verify explicitly requested model falls back on transient error without retrying invalid/auth errors
    with patch("core.multimodal.service.GROQ_API_KEY", "mock_groq_key"), patch("urllib.request.urlopen") as mock_url:
        import urllib.error
        # Simulate transient 503 error for requested model, then success on fallback model
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"choices":[{"message":{"content":"fallback success"}}]}'
        mock_response.__enter__.return_value = mock_response

        mock_url.side_effect = [
            urllib.error.HTTPError("https://api.groq.com", 503, "Service Unavailable", {}, io.BytesIO(b"overloaded")),
            mock_response
        ]

        result = MultimodalService.chat_completion(
            messages=[{"role": "user", "content": "hello"}],
            provider="groq",
            model="openai/gpt-oss-120b"
        )
        assert result["text"] == "fallback success"
        assert result["model"] == "openai/gpt-oss-20b"

    # Verify 401 unauthorized raises immediately without retrying
    with patch("core.multimodal.service.GROQ_API_KEY", "mock_groq_key"), patch("urllib.request.urlopen") as mock_url_auth:
        import urllib.error
        mock_url_auth.side_effect = urllib.error.HTTPError("https://api.groq.com", 401, "Unauthorized", {}, io.BytesIO(b"invalid key"))
        with pytest.raises(RuntimeError) as exc_info:
            MultimodalService.chat_completion(
                messages=[{"role": "user", "content": "hello"}],
                provider="groq",
                model="openai/gpt-oss-120b"
            )
        assert "401" in str(exc_info.value)
        assert mock_url_auth.call_count == 1

def test_http_timeout_and_empty_response_handling():
    import urllib.error
    # 1. Test timeout handling during chat completion
    with patch("core.multimodal.service.GROQ_API_KEY", "mock_groq_key"), patch("urllib.request.urlopen") as mock_url:
        mock_url.side_effect = TimeoutError("The read operation timed out")
        with pytest.raises(TimeoutError) as exc_info:
            MultimodalService.chat_completion(
                messages=[{"role": "user", "content": "hello"}],
                provider="groq",
                model="openai/gpt-oss-120b"
            )
        assert "timed out" in str(exc_info.value).lower()

    # 2. Test empty candidate choices handling in Gemini
    with patch("core.multimodal.service.GOOGLE_API_KEY", "mock_google_key"), patch("urllib.request.urlopen") as mock_url_gemini:
        mock_empty_resp = MagicMock()
        mock_empty_resp.read.return_value = b'{"candidates":[]}'
        mock_empty_resp.__enter__.return_value = mock_empty_resp
        mock_url_gemini.return_value = mock_empty_resp

        with pytest.raises(ValueError) as exc_info:
            MultimodalService.chat_completion(
                messages=[{"role": "user", "content": "hello"}],
                provider="gemini",
                model="gemini-3.8-flash"
            )
        assert "empty candidate choices" in str(exc_info.value).lower()

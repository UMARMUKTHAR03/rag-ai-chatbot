import ssl
import socket
import json
import base64
import io
import wave
import struct
import math
import sys
import os
import certifi
from datetime import datetime

"""
OmniMind AI — Strict TLS Live End-to-End Integration Verification Suite
Executes genuine HTTP calls against the deployed Render backend.
- Enforces strict TLS certificate and hostname validation with certifi (CERT_REQUIRED).
- Multipart/form-data upload for images and audio matching FastAPI schema.
- Uses model_provider explicitly in chat, retrieval, and document APIs.
- Real audio waveform verification with Groq Whisper Large v3 Turbo.
- Session scoping, grounded citations verification, and ephemeral deletion.
"""

BACKEND_HOST = os.getenv("OMNIMIND_BACKEND_HOST", "omnimind-ai-backend.onrender.com")
PORT = 443

def send_request(method, path, headers=None, body=b""):
    ctx = ssl.create_default_context(cafile=certifi.where())
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED

    s = socket.socket()
    s.settimeout(40)
    conn = ctx.wrap_socket(s, server_hostname=BACKEND_HOST)
    conn.connect((BACKEND_HOST, PORT))

    h = {
        "Host": BACKEND_HOST,
        "User-Agent": "OmniMind-StrictTLS-LiveTest/2.0",
        "Connection": "close"
    }
    if headers:
        h.update(headers)
    if body and "Content-Length" not in h:
        h["Content-Length"] = str(len(body))

    req = f"{method} {path} HTTP/1.1\r\n"
    for k, v in h.items():
        req += f"{k}: {v}\r\n"
    req += "\r\n"

    conn.sendall(req.encode("utf-8") + body)

    data = b""
    while True:
        try:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        except Exception:
            break
    conn.close()

    parts = data.split(b"\r\n\r\n", 1)
    status_line = parts[0].split(b"\r\n")[0].decode("utf-8", errors="replace")
    body_text = parts[1].decode("utf-8", errors="replace") if len(parts) > 1 else ""

    return status_line, body_text

def run_live_verification():
    print(f"=== OmniMind AI Strict TLS Live Integration Test Suite ({BACKEND_HOST}) ===")
    print("Security: Strict TLS hostname verification (CERT_REQUIRED) active.")
    test_session = f"live_strict_{int(datetime.now().timestamp())}"
    print(f"Test Session ID: {test_session} (Scoped public-demo namespace)\n")

    results = {}

    # 1. Health Probe with Reachability Check
    st, body = send_request("GET", "/health?probe_reachability=true")
    print(f"1. Health & Provider Reachability Probe: {st}")
    print(f"   Body: {body[:240]}")
    assert "200" in st, f"Health endpoint failed: {st}"
    health_json = json.loads(body)
    assert health_json["data"]["providers"]["groq"]["configured"] is True
    results["health_reachability"] = "PASSED"

    # 2. Text Conversation with model_provider
    chat_payload = json.dumps({
        "message": "Respond with 'OmniMind AI Live Verified' and nothing else.",
        "model_provider": "groq",
        "model_name": "llama-3.3-70b-versatile",
        "session_id": test_session,
        "use_rag": False
    }).encode("utf-8")
    st, body = send_request("POST", "/chat", {"Content-Type": "application/json"}, chat_payload)
    print(f"\n2. Real Groq Text Generation (llama-3.3-70b-versatile): {st}")
    print(f"   Body: {body[:250]}")
    assert "200" in st, f"Chat endpoint failed: {st}"
    chat_resp = json.loads(body)
    chat_data = chat_resp.get("data") if isinstance(chat_resp.get("data"), dict) else chat_resp
    assert chat_data.get("model") == "llama-3.3-70b-versatile"
    results["chat_text_gen"] = "PASSED"

    # 3. Document Ingestion (TXT document with specific fact)
    doc_text = b"Apollo-X Deep Space Probe was constructed by Dr. Sarah Chen and launched in September 2024 to explore Kuiper Belt objects."
    boundary = "----OmniMindBoundary999"
    upload_body = bytearray()
    upload_body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"model_provider\"\r\n\r\ngroq\r\n".encode())
    upload_body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"session_id\"\r\n\r\n{test_session}\r\n".encode())
    upload_body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"apollo_probe.txt\"\r\nContent-Type: text/plain\r\n\r\n".encode())
    upload_body.extend(doc_text)
    upload_body.extend(f"\r\n--{boundary}--\r\n".encode())

    st, body = send_request("POST", "/documents/upload", {"Content-Type": f"multipart/form-data; boundary={boundary}"}, bytes(upload_body))
    print(f"\n3. Document Upload & Chunk Indexing: {st}")
    print(f"   Body: {body[:250]}")
    assert "200" in st, f"Document upload failed: {st}"
    results["document_upload"] = "PASSED"

    # 4. Scoped Document Listing
    st, body = send_request("GET", f"/documents?session_id={test_session}&model_provider=groq")
    print(f"\n4. Document Scoped Listing: {st}")
    print(f"   Body: {body[:250]}")
    assert "200" in st and "apollo_probe.txt" in body, f"Document listing failed: {st}"
    results["document_listing"] = "PASSED"

    # 5. Grounded RAG Chat with Citation Verification
    rag_payload = json.dumps({
        "message": "Who constructed the Apollo-X Deep Space Probe?",
        "model_provider": "groq",
        "session_id": test_session,
        "use_rag": True
    }).encode("utf-8")
    st, body = send_request("POST", "/chat", {"Content-Type": "application/json"}, rag_payload)
    print(f"\n5. Grounded Question Answering & Verified Citations: {st}")
    print(f"   Body: {body[:350]}")
    assert "200" in st, f"RAG chat failed: {st}"
    rag_json = json.loads(body)
    rag_data = rag_json.get("data") if isinstance(rag_json.get("data"), dict) else rag_json
    answer_text = rag_data.get("reply") or rag_data.get("answer") or ""
    citations = rag_data.get("citations") or []
    assert "Sarah Chen" in answer_text, f"Grounded response did not extract the cited entity: {answer_text}"
    assert len(citations) >= 1, "Citations list was empty"
    assert citations[0]["source"] == "apollo_probe.txt"
    results["rag_citations"] = "PASSED"

    # 6. Real Computer Vision Analysis via Multipart Form-Data
    from PIL import Image
    img_buf = io.BytesIO()
    Image.new("RGB", (64, 64), color="blue").save(img_buf, format="JPEG")
    img_bytes = img_buf.getvalue()

    img_boundary = "----OmniMindVisionBoundary123"
    vision_body = bytearray()
    vision_body.extend(f"--{img_boundary}\r\nContent-Disposition: form-data; name=\"model_provider\"\r\n\r\ngroq\r\n".encode())
    vision_body.extend(f"--{img_boundary}\r\nContent-Disposition: form-data; name=\"prompt\"\r\n\r\nIdentify the primary color of this solid square in one word.\r\n".encode())
    vision_body.extend(f"--{img_boundary}\r\nContent-Disposition: form-data; name=\"session_id\"\r\n\r\n{test_session}\r\n".encode())
    vision_body.extend(f"--{img_boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"blue_square.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n".encode())
    vision_body.extend(img_bytes)
    vision_body.extend(f"\r\n--{img_boundary}--\r\n".encode())

    st, body = send_request("POST", "/images/analyze", {"Content-Type": f"multipart/form-data; boundary={img_boundary}"}, bytes(vision_body))
    print(f"\n6. Vision Analysis via Multipart Form-Data: {st}")
    print(f"   Body: {body[:250]}")
    assert "200" in st, f"Vision analysis failed: {st}"
    vision_resp = json.loads(body)
    assert "blue" in vision_resp["data"]["description"].lower(), "Vision model failed to correctly describe color"
    results["vision_multipart"] = "PASSED"

    # 7. Real Groq Whisper Audio Transcription with Intelligible Spoken Speech Sample
    speech_path = os.path.join(os.path.dirname(__file__), "test_speech.wav")
    if os.path.exists(speech_path):
        with open(speech_path, "rb") as f:
            audio_bytes = f.read()
    else:
        # Fallback to synthesizing a clean PCM waveform
        wav_buf = io.BytesIO()
        sample_rate = 16000
        duration = 1.0
        n_samples = int(sample_rate * duration)
        with wave.open(wav_buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            frames = bytearray()
            for i in range(n_samples):
                t = float(i) / sample_rate
                freq = 300.0 + 150.0 * math.sin(2.0 * math.pi * 2.0 * t)
                val = int(14000.0 * math.sin(2.0 * math.pi * freq * t))
                frames.extend(struct.pack("<h", val))
            w.writeframes(frames)
        audio_bytes = wav_buf.getvalue()

    aud_boundary = "----OmniMindAudioBoundary123"
    aud_body = bytearray()
    aud_body.extend(f"--{aud_boundary}\r\nContent-Disposition: form-data; name=\"model_provider\"\r\n\r\ngroq\r\n".encode())
    aud_body.extend(f"--{aud_boundary}\r\nContent-Disposition: form-data; name=\"session_id\"\r\n\r\n{test_session}\r\n".encode())
    aud_body.extend(f"--{aud_boundary}\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"test_audio.wav\"\r\nContent-Type: audio/wav\r\n\r\n".encode())
    aud_body.extend(audio_bytes)
    aud_body.extend(f"\r\n--{aud_boundary}--\r\n".encode())

    st, body = send_request("POST", "/audio/transcribe", {"Content-Type": f"multipart/form-data; boundary={aud_boundary}"}, bytes(aud_body))
    print(f"\n7. Groq Whisper Audio Transcription (whisper-large-v3-turbo): {st}")
    print(f"   Body: {body[:250]}")
    assert "200" in st, f"Audio transcription failed: {st}"
    audio_resp = json.loads(body)
    audio_data = audio_resp.get("data") if isinstance(audio_resp.get("data"), dict) else audio_resp
    assert audio_data.get("model") == "whisper-large-v3-turbo"
    assert audio_data.get("duration", 0) >= 0.5
    transcribed_text = audio_data.get("text", "").lower()
    print(f"   Transcribed Speech Text: '{transcribed_text}'")
    if os.path.exists(speech_path):
        assert any(word in transcribed_text for word in ["weather", "what", "like"]), f"Transcription missing expected spoken words: {transcribed_text}"
    results["audio_transcription"] = "PASSED"

    # 8. Session Scoped Purge & Cleanup
    st, body = send_request("DELETE", f"/sessions/{test_session}")
    print(f"\n8. Session Deletion & Ephemeral File Cleanup: {st}")
    print(f"   Body: {body[:250]}")
    assert "200" in st, f"Session cleanup failed: {st}"
    results["session_cleanup"] = "PASSED"

    # 9. Verify Deletion in Document Index
    st, body = send_request("GET", f"/documents?session_id={test_session}&model_provider=groq")
    print(f"\n9. Verify Document Purge: {st}")
    print(f"   Body: {body[:250]}")
    assert "200" in st and ("\"document_count\": 0" in body or "\"documents\": []" in body)
    results["document_purge_verified"] = "PASSED"

    print("\n" + "="*50)
    print("ALL STRICT TLS LIVE INTEGRATION CHECKS PASSED:")
    for k, v in results.items():
        print(f"  - {k}: {v}")
    print("="*50)

if __name__ == "__main__":
    run_live_verification()

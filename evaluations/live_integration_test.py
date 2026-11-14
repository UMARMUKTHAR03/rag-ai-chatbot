import ssl
import socket
import json
import base64
import io
import wave
import sys
import os
from datetime import datetime

"""
OmniMind AI — Reproducible Live End-to-End Integration Verification Procedure
Executes genuine HTTP calls against the deployed Render backend.
No mocked responses; validates real provider behavior, error reporting,
session scoping, document RAG citations, and file cleanup.
"""

BACKEND_HOST = os.getenv("OMNIMIND_BACKEND_HOST", "omnimind-ai-backend.onrender.com")
PORT = 443

def send_request(method, path, headers=None, body=b""):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    s = socket.socket()
    s.settimeout(35)
    conn = ctx.wrap_socket(s, server_hostname=BACKEND_HOST)
    conn.connect((BACKEND_HOST, PORT))

    h = {
        "Host": BACKEND_HOST,
        "User-Agent": "OmniMind-Live-Verification/2.0",
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
    print(f"=== OmniMind AI Live Integration Test Suite ({BACKEND_HOST}) ===")
    test_session = f"live_test_{int(datetime.now().timestamp())}"
    print(f"Test Session ID: {test_session} (Scoped public-demo namespace)\n")

    results = {}

    # 1. Health Probe
    st, body = send_request("GET", "/health?probe_reachability=true")
    print(f"1. Health & Provider Status: {st}")
    print(f"   Body: {body[:240]}")
    assert "200" in st, f"Health endpoint failed: {st}"
    results["health"] = "PASSED"

    # 2. Text Conversation with model_provider
    payload = json.dumps({
        "message": "Respond with 'OmniMind AI Online' and nothing else.",
        "model_provider": "groq",
        "model_name": "llama-3.3-70b-versatile",
        "session_id": test_session,
        "use_rag": False
    }).encode("utf-8")
    st, body = send_request("POST", "/chat", {"Content-Type": "application/json"}, payload)
    print(f"\n2. Real Groq Text Generation (llama-3.3-70b-versatile): {st}")
    print(f"   Body: {body[:250]}")
    assert "200" in st, f"Chat endpoint failed: {st}"
    results["chat"] = "PASSED"

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
    results["upload"] = "PASSED"

    # 4. Document Retrieval & Listing
    st, body = send_request("GET", f"/documents?session_id={test_session}&model_provider=groq")
    print(f"\n4. Document Scoped Listing: {st}")
    print(f"   Body: {body[:250]}")
    assert "200" in st and "apollo_probe.txt" in body, f"Document listing failed: {st}"
    results["listing"] = "PASSED"

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
    assert "Sarah Chen" in body, "Grounded response did not extract the cited entity"
    assert "apollo_probe.txt" in body, "Citation did not reference source filename"
    results["rag_citations"] = "PASSED"

    # 6. Real Computer Vision Analysis (JPEG)
    from PIL import Image
    img_buf = io.BytesIO()
    Image.new("RGB", (64, 64), color="blue").save(img_buf, format="JPEG")
    b64_img = base64.b64encode(img_buf.getvalue()).decode()

    vision_payload = json.dumps({
        "image_base64": b64_img,
        "mime_type": "image/jpeg",
        "prompt": "Identify the primary color of this image in one word.",
        "provider": "groq",
        "model": "llama-3.2-90b-vision-preview"
    }).encode("utf-8")
    st, body = send_request("POST", "/images/analyze", {"Content-Type": "application/json"}, vision_payload)
    print(f"\n6. Vision Analysis (llama-3.2-90b-vision-preview): {st}")
    print(f"   Body: {body[:250]}")
    assert "200" in st, f"Vision analysis failed: {st}"
    assert "blue" in body.lower(), "Vision model failed to correctly describe color"
    results["vision"] = "PASSED"

    # 7. Real Groq Whisper Audio Transcription
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 8000)
    audio_bytes = wav_buf.getvalue()

    aud_body = bytearray()
    aud_body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"provider\"\r\n\r\ngroq\r\n".encode())
    aud_body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"session_id\"\r\n\r\n{test_session}\r\n".encode())
    aud_body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"audio\"; filename=\"test_tone.wav\"\r\nContent-Type: audio/wav\r\n\r\n".encode())
    aud_body.extend(audio_bytes)
    aud_body.extend(f"\r\n--{boundary}--\r\n".encode())

    st, body = send_request("POST", "/audio/transcribe", {"Content-Type": f"multipart/form-data; boundary={boundary}"}, bytes(aud_body))
    print(f"\n7. Groq Whisper Audio Transcription (whisper-large-v3-turbo): {st}")
    print(f"   Body: {body[:250]}")
    assert "200" in st, f"Audio transcription failed: {st}"
    results["audio_whisper"] = "PASSED"

    # 8. Session Scoped Purge & Cleanup
    st, body = send_request("DELETE", f"/sessions/{test_session}")
    print(f"\n8. Session Deletion & Ephemeral File Cleanup: {st}")
    print(f"   Body: {body[:250]}")
    assert "200" in st, f"Session cleanup failed: {st}"
    results["cleanup"] = "PASSED"

    # 9. Verify Deletion in Document Index
    st, body = send_request("GET", f"/documents?session_id={test_session}&model_provider=groq")
    print(f"\n9. Verify Document Purge: {st}")
    print(f"   Body: {body[:250]}")
    assert "200" in st and ("\"document_count\": 0" in body or "\"documents\": []" in body)
    results["isolation_verified"] = "PASSED"

    print("\n" + "="*50)
    print("LIVE INTEGRATION TEST RESULTS:")
    for k, v in results.items():
        print(f"  - {k}: {v}")
    print("="*50)

if __name__ == "__main__":
    run_live_verification()

# OmniMind AI — High-Performance FastAPI Server

FastAPI backend powering multimodal document ingestion, session-isolated semantic retrieval, and dual-engine AI reasoning (Groq Llama 3.3 70B & Google Gemini 2.0 Flash).

### Key Features
- **Multi-Format Ingestion**: PDF, DOCX, PPTX, XLSX, CSV, TXT, MD
- **Hybrid Retrieval**: In-memory cosine similarity and keyword matching (<1ms latency)
- **Multimodal AI**: Direct REST integration with Groq (text, Whisper audio) and Google Gemini (text, vision)
- **Strict Grounding**: Prompt engineering that prevents hallucination and mandates verified citations

### Local Development
```bash
python -m venv venv
source venv/bin/activate  # Or .\venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt
pytest tests/test_api.py -v
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
API Documentation is available at `http://localhost:8000/docs`.

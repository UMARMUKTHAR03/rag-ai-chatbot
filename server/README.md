# 🤖 RAG PDFBot — Server

This is the **FastAPI backend** for RAG PDFBot. It handles PDF processing, vectorstore embedding via ChromaDB, LLM chain execution through LangChain, and exposes RESTful API endpoints for the Streamlit frontend.

---

## Features

- ✅ Upload and process PDFs (token-based chunking)
- 🧠 Chat with LLM using vectorstore retrieval (RAG)
- 🔍 Inspect document chunks via similarity search
- 🌐 Supports multiple providers (Groq Cloud, Google Gemini)

---

## Project Structure

```
server/
├── api/                        # FastAPI routes and schemas
├── config/                     # Environment and constants
├── core/                       # LLM logic, vectorstore, processing
├── utils/                      # Logger and helpers
├── main.py                     # App entry point
```

---

## 📦 Installation

1. **Clone the repo**

```bash
git clone https://github.com/UMARMUKTHAR03/rag-ai-chatbot.git
cd rag-ai-chatbot
```

2. **Create a virtual environment (optional)**

```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**

```bash
cd server
pip3 install -r requirements.txt
```

---

## Configuration

Set your API keys in `config/settings.py`:

- **Groq**: [console.groq.com](https://console.groq.com/)
- **Gemini**: [ai.google.dev](https://ai.google.dev)

```python
GROQ_API_KEY = "your_groq_key"
GOOGLE_API_KEY = "your_google_key"
```

---

## ▶️ Usage

Run the server:

```bash
cd rag-ai-chatbot/server
uvicorn main:app --reload --port 8000
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload_and_process_pdfs` | POST | Upload & vectorize PDF documents |
| `/chat` | POST | Send query, receive RAG-grounded response |
| `/vector_store/count/{provider}` | GET | Get indexed chunk count |
| `/vector_store/search` | POST | Direct similarity search |
| `/llm` | GET | List available providers |
| `/llm/{provider}` | GET | List models for a provider |
| `/health` | GET | Backend health check |

---

## Logging

Logs are printed to the console and controlled via `utils/logger.py`.

---

**Engineered by UMAR MUKTHAR** • [@UMARMUKTHAR03](https://github.com/UMARMUKTHAR03)

# 🤖 RAG PDFBot — Client

This is the **Streamlit-based frontend** for RAG PDFBot. It provides users with an intuitive conversational interface to upload PDF documents, ask questions grounded strictly in their content, inspect vectorstore similarity search responses, and export chat sessions.

---

## Features

- 📄 Upload and chat with multiple PDFs
- 🧠 Choose between LLM providers (Groq Cloud, Google Gemini)
- 🔬 Inspector tab to test direct vectorstore retrieval
- 📥 Downloadable chat history (CSV export)

---

## Project Structure

```
client/
├── app.py                      # Main Streamlit entry point
├── state/
│   └── session.py              # Handles session state setup
├── components/
│   ├── chat.py                 # Chat UI: input, history, uploads
│   ├── sidebar.py              # Sidebar: model selector, uploader, utilities
│   └── inspector.py            # Inspector to test vectorstore responses
├── utils/
│   ├── api.py                  # Server communication
│   ├── config.py               # API_URL configuration
│   └── helpers.py              # High-level orchestration
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
cd client
pip3 install -r requirements.txt
```

---

## ▶️ Usage

Run the client:

```bash
cd rag-ai-chatbot/client
streamlit run app.py
```

Steps:
1. Select a model provider (Groq or Gemini)
2. Enter your API key
3. Choose a model
4. Upload one or more PDFs
5. Click **Submit**
6. Ask questions about the uploaded PDFs in the chat input

---

## Configuration

Set `API_URL` in `client/utils/config.py` to your FastAPI server:
```python
API_URL = "http://127.0.0.1:8000"
```

---

## 🧼 Tools Panel

- **🔄 Reset**: Clears session state and reruns app
- **🧹 Clear Chat**: Clears chat + PDF submission
- **↩️ Undo**: Removes last question/response

---

## 📦 Download Chat History

Chat history is saved in the session state and can be exported as a CSV with the following columns:

| Question | Answer | Model Provider | Model Name | PDF File | Timestamp |
|----------|--------|----------------|------------|----------|-----------|
| What is this PDF about? | This PDF explains... | Groq | llama3-70b-8192 | document.pdf | 2026-10-27 |

---

## ⚠️ Notes

- Ensure the backend (FastAPI) server is running before launching the client.
- Chat and Inspector require PDFs to be uploaded and processed first.

---

**Engineered by UMAR MUKTHAR** • [@UMARMUKTHAR03](https://github.com/UMARMUKTHAR03)

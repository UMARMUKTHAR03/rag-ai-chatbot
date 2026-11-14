import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = "OmniMind AI"
APP_TITLE = "OmniMind AI – Multimodal Knowledge Assistant"
APP_TAGLINE = "One AI. Every Modality. All Your Knowledge."
APP_VERSION = "2.0.0"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

TEMPFILE_UPLOAD_DIRECTORY = os.getenv("TEMPFILE_UPLOAD_DIRECTORY", "./temp/uploaded_files")
DATA_DIR = os.getenv("DATA_DIR", "./data")

# Active production models
MODEL_OPTIONS = {
    "groq": {
        "playground": "https://console.groq.com",
        "chat_models": ["openai/gpt-oss-120b", "openai/gpt-oss-20b"],
        "vision_models": ["meta-llama/llama-4-scout-17b-16e-instruct", "qwen/qwen3.8-27b"],
        "audio_models": ["whisper-large-v3-turbo"],
        "models": ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
    },
    "gemini": {
        "playground": "https://aistudio.google.com",
        "chat_models": ["gemini-3.8-flash", "gemini-3.5-flash-lite"],
        "vision_models": ["gemini-3.8-flash", "gemini-3.5-flash-lite"],
        "audio_models": [],
        "models": ["gemini-3.8-flash", "gemini-3.5-flash-lite"]
    }
}

VECTORSTORE_DIRECTORY = {
    key.lower(): os.path.join(DATA_DIR, f"{key.lower()}_vector_store")
    for key in MODEL_OPTIONS.keys()
}

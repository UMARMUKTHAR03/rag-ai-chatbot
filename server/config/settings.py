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
        "chat_models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        "vision_models": ["llama-3.2-11b-vision-preview"],
        "audio_models": ["whisper-large-v3-turbo"],
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    },
    "gemini": {
        "playground": "https://aistudio.google.com",
        "chat_models": ["gemini-1.5-flash", "gemini-1.5-pro"],
        "vision_models": ["gemini-1.5-flash", "gemini-1.5-pro"],
        "audio_models": [],
        "models": ["gemini-1.5-flash", "gemini-1.5-pro"]
    }
}

VECTORSTORE_DIRECTORY = {
    key.lower(): os.path.join(DATA_DIR, f"{key.lower()}_vector_store")
    for key in MODEL_OPTIONS.keys()
}

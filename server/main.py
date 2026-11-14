import os
import sys

# Ensure server directory is in sys.path for both uvicorn server.main:app and uvicorn main:app
server_dir = os.path.dirname(os.path.abspath(__file__))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routes import router
from core.vector_database import initialize_empty_vectorstores
from utils.logger import logger
from config.settings import APP_NAME, APP_TITLE, APP_TAGLINE, APP_VERSION

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting up {APP_TITLE} v{APP_VERSION}...")
    initialize_empty_vectorstores()
    logger.info("Startup complete.")
    yield
    logger.info(f"Shutting down {APP_NAME}...")

app = FastAPI(
    title=APP_TITLE,
    description=f"{APP_TAGLINE} — Unified multimodal RAG chatbot for documents, images, and audio.",
    version=APP_VERSION,
    lifespan=lifespan
)

# Enable CORS for local Vite development and GitHub Pages production origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def root():
    return {
        "app": APP_NAME,
        "title": APP_TITLE,
        "tagline": APP_TAGLINE,
        "version": APP_VERSION,
        "docs_url": "/docs",
        "health_url": "/health"
    }

if __name__ == "__main__":
    logger.info("Running OmniMind AI server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

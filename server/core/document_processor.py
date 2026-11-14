import os
import io
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import aiofiles
from fastapi import UploadFile

from config.settings import TEMPFILE_UPLOAD_DIRECTORY
from utils.logger import logger

SUPPORTED_EXTENSIONS = {
    ".pdf": "PDF Document",
    ".docx": "Microsoft Word Document",
    ".txt": "Plain Text Document",
    ".md": "Markdown Document",
    ".pptx": "Microsoft PowerPoint Presentation",
    ".csv": "Comma-Separated Values",
    ".xlsx": "Microsoft Excel Spreadsheet",
    ".jpg": "JPEG Image",
    ".jpeg": "JPEG Image",
    ".png": "PNG Image",
    ".webp": "WebP Image",
    ".mp3": "MP3 Audio",
    ".wav": "WAV Audio",
    ".m4a": "M4A Audio",
    ".webm": "WebM Audio"
}

def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r'[^\w\.\-\_]', '_', filename)
    return cleaned or "uploaded_file"

def validate_uploaded_file(file: UploadFile, max_size_mb: int = 50) -> str:
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in SUPPORTED_EXTENSIONS:
        logger.warning(f"Unsupported file type: {file.filename}")
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported formats: PDF, DOCX, TXT, MD, PPTX, CSV, XLSX, JPG, PNG, WEBP, MP3, WAV, M4A, WEBM."
        )

    file.file.seek(0, os.SEEK_END)
    size_bytes = file.file.tell()
    file.file.seek(0)
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > max_size_mb:
        logger.warning(f"File too large: {file.filename} ({size_mb:.2f} MB)")
        raise ValueError(f"File size exceeds maximum allowed size of {max_size_mb} MB.")

    return ext

async def save_uploaded_file(file: UploadFile, session_id: str = "default") -> str:
    validate_uploaded_file(file)
    session_dir = os.path.join(TEMPFILE_UPLOAD_DIRECTORY, session_id)
    os.makedirs(session_dir, exist_ok=True)

    safe_name = sanitize_filename(file.filename)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stored_name = f"{timestamp}_{safe_name}"
    file_path = os.path.join(session_dir, stored_name)

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    logger.debug(f"Saved file {file.filename} to {file_path}")
    return file_path

class DocumentChunk:
    def __init__(self, page_content: str, metadata: Optional[Dict[str, Any]] = None):
        self.page_content = page_content
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_content": self.page_content,
            "metadata": self.metadata
        }

def extract_text_from_file(file_path: str, original_filename: str) -> List[DocumentChunk]:
    ext = os.path.splitext(file_path.lower())[1]
    chunks: List[DocumentChunk] = []

    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                chunks.append(DocumentChunk(
                    page_content=text.strip(),
                    metadata={
                        "source": original_filename,
                        "file_type": "PDF",
                        "page": idx + 1,
                        "total_pages": len(reader.pages)
                    }
                ))

    elif ext == ".docx":
        import docx
        doc = docx.Document(file_path)
        full_text = []
        for p in doc.paragraphs:
            if p.text.strip():
                full_text.append(p.text.strip())
        joined = "\n\n".join(full_text)
        if joined:
            chunks.append(DocumentChunk(
                page_content=joined,
                metadata={
                    "source": original_filename,
                    "file_type": "DOCX",
                    "paragraphs": len(full_text)
                }
            ))

    elif ext == ".pptx":
        from pptx import Presentation
        prs = Presentation(file_path)
        for idx, slide in enumerate(prs.slides):
            slide_texts = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_texts.append(shape.text.strip())
            content = "\n".join(slide_texts)
            if content.strip():
                chunks.append(DocumentChunk(
                    page_content=content.strip(),
                    metadata={
                        "source": original_filename,
                        "file_type": "PPTX",
                        "slide": idx + 1,
                        "total_slides": len(prs.slides)
                    }
                ))

    elif ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            if content.strip():
                chunks.append(DocumentChunk(
                    page_content=content.strip(),
                    metadata={
                        "source": original_filename,
                        "file_type": "Markdown" if ext == ".md" else "Text",
                        "char_count": len(content)
                    }
                ))

    elif ext == ".csv":
        import pandas as pd
        df = pd.read_csv(file_path, nrows=500)
        csv_text = df.to_string(index=False)
        chunks.append(DocumentChunk(
            page_content=f"CSV Columns: {', '.join(df.columns.astype(str))}\n\nData Sample:\n{csv_text}",
            metadata={
                "source": original_filename,
                "file_type": "CSV",
                "rows": len(df),
                "columns": len(df.columns)
            }
        ))

    elif ext == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows_data = []
            for row in ws.iter_rows(values_only=True):
                non_empty = [str(cell) for cell in row if cell is not None]
                if non_empty:
                    rows_data.append(" | ".join(non_empty))
            sheet_text = "\n".join(rows_data[:200])
            if sheet_text.strip():
                chunks.append(DocumentChunk(
                    page_content=f"Sheet: {sheet_name}\n{sheet_text}",
                    metadata={
                        "source": original_filename,
                        "file_type": "Excel",
                        "sheet": sheet_name,
                        "rows_sample": len(rows_data)
                    }
                ))

    return chunks

def split_text_into_chunks(docs: List[DocumentChunk], chunk_size: int = 500, chunk_overlap: int = 50) -> List[DocumentChunk]:
    split_chunks: List[DocumentChunk] = []

    for doc in docs:
        text = doc.page_content
        words = text.split()
        if not words:
            continue

        step = max(1, chunk_size - chunk_overlap)
        for i in range(0, len(words), step):
            sub_words = words[i:i + chunk_size]
            sub_text = " ".join(sub_words)
            meta = dict(doc.metadata)
            meta["chunk_index"] = len(split_chunks)
            meta["word_count"] = len(sub_words)
            split_chunks.append(DocumentChunk(page_content=sub_text, metadata=meta))

    logger.debug(f"Split {len(docs)} document units into {len(split_chunks)} chunks")
    return split_chunks

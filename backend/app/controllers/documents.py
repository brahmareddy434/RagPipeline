import asyncio
import logging
from pathlib import Path
from fastapi import File, HTTPException, Request, UploadFile
from app.config.settings import get_settings
from app.rag.loading import UnsupportedFile
from app.schemas import IngestResponse
from app.infrastructure.ollama import OllamaUnavailable

from fastapi import APIRouter
from app.controllers.dependencies import container

router = APIRouter()

@router.get("/documents")
async def documents(request: Request):
    rows = await asyncio.to_thread(container(request).store.all_chunks)
    sources = {}
    for row in rows:
        sources[row.source] = sources.get(row.source, 0) + 1
    return {"documents": [{"source": source, "chunks": count} for source, count in sorted(sources.items())]}


@router.delete("/documents/{source}")
async def delete_document(source: str, request: Request):
    deleted = await container(request).store.delete_source(source)
    if not deleted:
        raise HTTPException(404, "No indexed document has that exact filename.")
    return {"source": source, "deleted_chunks": deleted}


@router.delete("/documents")
async def clear_documents(request: Request):
    deleted = await container(request).store.clear()
    return {"deleted_chunks": deleted, "message": "Course index cleared. Upload documents before asking questions."}


@router.get("/sources/{chunk_id}")
async def source(chunk_id: str, request: Request):
    chunk = await asyncio.to_thread(container(request).store.get_chunk, chunk_id)
    if chunk is None:
        raise HTTPException(404, "Source chunk not found. It may have been replaced by a newer document.")
    return chunk


@router.post("/documents", response_model=IngestResponse)
async def upload_document(request: Request, file: UploadFile | None = File(None), files: list[UploadFile] | None = File(None)):
    uploads = ([file] if file else []) + (files or [])
    if not uploads or len(uploads) > 10:
        raise HTTPException(400, "Choose between one and ten files.")
    items = []
    limit = get_settings().max_upload_bytes
    try:
        for upload in uploads:
            if not upload.filename:
                raise HTTPException(400, "Each document needs a filename.")
            if Path(upload.filename).suffix.lower() not in container(request).ingestion.loader.supported:
                raise UnsupportedFile("Use PDF, DOCX, TXT, MD, or HTML.")
            content = await upload.read(limit + 1)
            if len(content) > limit:
                raise HTTPException(413, f"File exceeds {limit} bytes.")
            items.append((upload.filename, content))
        try:
            chunks = await container(request).ingestion.ingest(items)
        except (UnsupportedFile, ValueError, OllamaUnavailable):
            raise
        except Exception as exc:
            logging.exception("Document ingestion failed")
            raise HTTPException(400, "Document could not be parsed or indexed. Check the file and server log.") from exc
        return IngestResponse(files=len(items), chunks=chunks)
    except UnsupportedFile as exc:
        raise HTTPException(415, str(exc)) from exc
    finally:
        for upload in uploads:
            await upload.close()

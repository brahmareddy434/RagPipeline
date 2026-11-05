import asyncio
from fastapi import Request
from fastapi.responses import HTMLResponse
from app.config.paths import PROJECT_ROOT as ROOT

from fastapi import APIRouter
from app.config.paths import PROJECT_ROOT as ROOT
from app.controllers.dependencies import container

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse((ROOT / "backend/app/static/legacy/inspection.html").read_text(encoding="utf-8"))


@router.get("/agent", response_class=HTMLResponse)
async def agent_page():
    """Week 7 demo screen: agent steps and the fixed-workflow comparison, side by side."""
    return HTMLResponse((ROOT / "backend/app/static/legacy/agent.html").read_text(encoding="utf-8"))


@router.get("/health")
async def health(request: Request):
    c = container(request)
    models = await c.ollama.health()
    names = [m["name"] for m in models.get("models", [])]
    def installed(name):
        return name in names or name + ":latest" in names
    ready = installed(c.ollama.chat_model) and installed(c.ollama.embed_model)
    return {"status": "ok" if ready else "missing_models", "ollama_models": names,
            "chat_model": c.ollama.chat_model, "embedding_model": c.ollama.embed_model,
            "collection": c.store.collection.name, "chunks": await asyncio.to_thread(c.store.collection.count)}

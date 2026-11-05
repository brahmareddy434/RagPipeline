from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config.settings import get_settings
from app.bootstrap import Container
from app.infrastructure.ollama import OllamaUnavailable
from app.infrastructure.tracing import TraceLogger
from app.config.paths import PROJECT_ROOT as ROOT

@asynccontextmanager
async def lifespan(app):
    settings = get_settings()
    app.state.container = Container.build(settings)
    app.state.trace_logger = TraceLogger(settings.trace_log_path)
    try:
        yield
    finally:
        await app.state.container.ollama.close()


app = FastAPI(title=get_settings().app_name, version="2.0.0", lifespan=lifespan)


app.mount("/course", StaticFiles(directory=ROOT / "course", html=True), name="course")


app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(OllamaUnavailable)
async def ollama_error(_, exc):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def invalid_value(_, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


from app.controllers import agents, documents, mcp, pages, rag, tools
for controller in (agents, documents, mcp, pages, rag, tools):
    app.include_router(controller.router)
    app.include_router(controller.router, prefix="/api/v1")

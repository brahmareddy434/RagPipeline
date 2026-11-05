from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from app.config.settings import Settings, get_settings
from app.bootstrap import Container
from app.infrastructure.ollama import OllamaUnavailable
from app.infrastructure.tracing import TraceLogger
from app.config.paths import PROJECT_ROOT as ROOT
from app.infrastructure.access import AccessBoundary

async def validation_error(request, exc):
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()]})


async def session(request: Request):
    return request.state.principal.model_dump()


async def ollama_error(_, exc):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


async def invalid_value(_, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


def create_app(settings: Settings | None = None):
    """Build an isolated API instance; tests supply configuration, not global state."""
    initial = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application):
        active = settings or get_settings()
        application.state.settings = active
        application.state.tenant_containers = {}
        application.state.tenant_loggers = {}
        application.state.container = Container.build(active)
        application.state.trace_logger = TraceLogger(active.trace_log_path, active.redact_names)
        try:
            yield
        finally:
            await application.state.container.ollama.close()
            for c in application.state.tenant_containers.values():
                await c.ollama.close()

    application = FastAPI(title=initial.app_name, version="3.0.0", lifespan=lifespan)
    application.state.settings = initial
    application.mount("/course/guides", StaticFiles(directory=ROOT / "course/guides", html=True), name="guides")
    if (ROOT / "frontend/dist/assets").is_dir():
        application.mount("/assets", StaticFiles(directory=ROOT / "frontend/dist/assets"), name="assets")
    application.add_middleware(CORSMiddleware, allow_origins=initial.allowed_origins,
        allow_methods=["GET", "POST", "DELETE"], allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Request-ID", "X-Trace-ID"])
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=initial.allowed_hosts)
    access = AccessBoundary(lambda request: request.app.state.settings)
    application.middleware("http")(access)
    application.add_exception_handler(RequestValidationError, validation_error)
    application.add_exception_handler(OllamaUnavailable, ollama_error)
    application.add_exception_handler(ValueError, invalid_value)
    application.add_api_route("/api/v1/session", session, methods=["GET"])
    from app.controllers import agents, documents, mcp, pages, rag, tools, traces
    for controller in (agents, documents, mcp, pages, rag, tools, traces):
        application.include_router(controller.router)
        application.include_router(controller.router, prefix="/api/v1")
    return application


app = create_app()

from fastapi import Request
import hashlib
from app.bootstrap import Container
from app.infrastructure.tracing import TraceLogger

def container(request: Request):
    identity = request.state.principal
    if request.app.state.settings.access_mode == "local":
        return request.app.state.container
    containers = request.app.state.tenant_containers
    if identity.tenant not in containers:
        suffix = hashlib.sha256(identity.tenant.encode()).hexdigest()[:24]
        settings = request.app.state.settings
        scoped = settings.model_copy(update={
            "collection_name": "documents_" + suffix,
            "memory_collection_name": "memory_" + suffix,
        })
        containers[identity.tenant] = Container.build(scoped)
    return containers[identity.tenant]


def trace_logger(request: Request):
    if request.app.state.settings.access_mode == "local":
        return request.app.state.trace_logger
    tenant = request.state.principal.tenant
    loggers = request.app.state.tenant_loggers
    if tenant not in loggers:
        suffix = hashlib.sha256(tenant.encode()).hexdigest()[:24]
        loggers[tenant] = TraceLogger(request.app.state.settings.trace_log_path.parent / (suffix + ".jsonl"))
    return loggers[tenant]

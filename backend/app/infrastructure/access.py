"""HTTP access boundary. Identity comes from configured credentials, never request data."""
import hashlib
import ipaddress
import secrets
import time
from collections import defaultdict, deque
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from app.config.settings import Principal


class AccessBoundary:
    def __init__(self, settings_provider):
        self.settings_provider = settings_provider
        self.windows = defaultdict(deque)

    async def __call__(self, request: Request, call_next):
        settings = self.settings_provider(request)
        path = request.url.path.removeprefix("/api/v1")
        request_id = str(uuid4())
        request.state.request_id = request_id
        # Public assets contain code/learning guides only, never uploaded data or traces.
        public = path in {"/", "/agent", "/docs", "/redoc", "/openapi.json"} or path.startswith(("/assets/", "/course/"))
        if public or request.method == "OPTIONS":
            return await call_next(request)
        def denied(status, detail):
            return JSONResponse({"detail": detail, "request_id": request_id}, status_code=status,
                                headers={"X-Request-ID": request_id})
        if settings.access_mode == "local":
            try:
                loopback = ipaddress.ip_address(request.client.host).is_loopback
            except (ValueError, AttributeError):
                loopback = False
            if not loopback:
                return denied(403, "Local mode accepts loopback clients only. Configure authenticated mode for remote access.")
            origin = request.headers.get("origin")
            if origin and origin not in settings.allowed_origins and origin != str(request.base_url).rstrip("/"):
                return denied(403, "Browser origin is not allowed.")
            principal = Principal(tenant="local", role="admin")
        else:
            header = request.headers.get("authorization", "")
            if not header.startswith("Bearer ") or len(header) > 4096:
                return denied(401, "Provide a valid Bearer access token.")
            digest = hashlib.sha256(header[7:].encode()).hexdigest()
            principal = next((p for h, p in settings.api_token_hashes.items() if secrets.compare_digest(h, digest)), None)
            if principal is None:
                return denied(401, "Invalid access token.")
        writes = request.method == "DELETE" or (request.method == "POST" and (path == "/documents" or path == "/agent/memory" or path.startswith("/reviews")))
        if writes and principal.role not in {"writer", "admin"}:
            return denied(403, "This operation requires writer or admin access.")
        if request.method == "DELETE" and path == "/documents" and principal.role != "admin":
            return denied(403, "Clearing the index requires admin access.")
        request.state.principal = principal
        now = time.monotonic()
        window = self.windows[principal.tenant]
        while window and window[0] <= now - 60:
            window.popleft()
        if len(window) >= settings.requests_per_minute:
            return denied(429, "Request limit reached; retry after one minute.")
        window.append(now)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

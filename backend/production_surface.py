from __future__ import annotations

from typing import Any

from starlette.responses import JSONResponse


class ProductionSurfaceMiddleware:
    """Fail closed before routing for paths outside the production API surface."""

    def __init__(self, app: Any):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            if path == "/api" or path.startswith("/api/"):
                await JSONResponse({"detail": "Not Found"}, status_code=404)(
                    scope, receive, send
                )
                return
            if path.startswith("/v1/") and not (
                path == "/v1/health" or path.startswith("/v1/repoguard/")
            ):
                await JSONResponse({"detail": "Not Found"}, status_code=404)(
                    scope, receive, send
                )
                return
        await self.app(scope, receive, send)

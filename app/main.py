import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.limiter import limiter
from app.routers import ai_reviews, analytics, approvals, attachments, audit, auth, departments, purchase_orders, requests, users, vendors

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIST_DIR = PROJECT_ROOT / "frontend" / "dist"
FRONTEND_INDEX_FILE = FRONTEND_DIST_DIR / "index.html"
API_EXACT_PATHS = {"/docs", "/health", "/openapi.json", "/redoc"}
API_PREFIX_PATHS = (
    "/analytics",
    "/approvals",
    "/auth",
    "/departments",
    "/invoices",
    "/purchase-orders",
    "/vendors",
)
API_SLASH_PREFIX_PATHS = ("/audit", "/requests", "/users")

_is_production = settings.app_env == "production"

app = FastAPI(
    title="ProcureFlow AI",
    version="0.1.0",
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
    openapi_url=None if _is_production else "/openapi.json",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(departments.router)
app.include_router(vendors.router)
app.include_router(requests.router)
app.include_router(purchase_orders.router)
app.include_router(approvals.router)
app.include_router(audit.router)
app.include_router(ai_reviews.router)
app.include_router(attachments.router)
app.include_router(analytics.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}


def _is_api_path(path: str) -> bool:
    if path in API_EXACT_PATHS:
        return True
    if any(path == prefix or path.startswith(f"{prefix}/") for prefix in API_PREFIX_PATHS):
        return True
    return any(path.startswith(f"{prefix}/") for prefix in API_SLASH_PREFIX_PATHS)


def _frontend_file(path: str) -> Path | None:
    dist_root = FRONTEND_DIST_DIR.resolve()
    candidate = (FRONTEND_DIST_DIR / path).resolve()
    try:
        candidate.relative_to(dist_root)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


@app.get("/{full_path:path}", include_in_schema=False)
def serve_frontend(full_path: str):
    request_path = f"/{full_path}" if full_path else "/"
    if _is_api_path(request_path):
        raise HTTPException(status_code=404, detail="Not Found")

    if full_path:
        static_file = _frontend_file(full_path)
        if static_file:
            return FileResponse(static_file)
        if "." in Path(full_path).name:
            raise HTTPException(status_code=404, detail="Not Found")

    if FRONTEND_INDEX_FILE.is_file():
        return FileResponse(FRONTEND_INDEX_FILE)
    raise HTTPException(status_code=404, detail="Frontend build not found")

"""
Valura AI — API Middleware.

Request timing, error handling, and CORS middleware.
"""

from __future__ import annotations

import time
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.core.exceptions import ValuraError, SafetyError
from src.core.logging import get_logger

logger = get_logger("api.middleware")

# ── Metrics tracking ─────────────────────────────────────────
_metrics = {
    "total_requests": 0,
    "total_errors": 0,
    "total_latency_ms": 0.0,
    "start_time": time.time(),
}


def get_metrics() -> dict:
    """Return current metrics snapshot."""
    uptime = time.time() - _metrics["start_time"]
    avg_latency = (
        _metrics["total_latency_ms"] / _metrics["total_requests"]
        if _metrics["total_requests"] > 0
        else 0
    )
    return {
        "total_requests": _metrics["total_requests"],
        "total_errors": _metrics["total_errors"],
        "avg_latency_ms": round(avg_latency, 2),
        "uptime_seconds": round(uptime, 2),
    }


def setup_middleware(app: FastAPI) -> None:
    """Configure all middleware for the FastAPI application."""

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request timing
    @app.middleware("http")
    async def timing_middleware(request: Request, call_next):
        start = time.perf_counter()
        _metrics["total_requests"] += 1

        try:
            response = await call_next(request)
        except Exception:
            _metrics["total_errors"] += 1
            raise
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            _metrics["total_latency_ms"] += duration_ms
            logger.info(
                f"{request.method} {request.url.path} — {duration_ms:.0f}ms"
            )

        return response

    # Global exception handler
    @app.exception_handler(SafetyError)
    async def safety_error_handler(request: Request, exc: SafetyError):
        return JSONResponse(
            status_code=403,
            content={
                "error": "safety_blocked",
                "message": exc.message,
                "reason": exc.reason,
            },
        )

    @app.exception_handler(ValuraError)
    async def valura_error_handler(request: Request, exc: ValuraError):
        return JSONResponse(
            status_code=500,
            content={
                "error": exc.code,
                "message": exc.message,
            },
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred. Please try again.",
            },
        )

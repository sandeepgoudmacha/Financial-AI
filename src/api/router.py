"""
Valura AI — API Router.

Main API endpoints:
- POST /chat — SSE streaming chat
- GET /health — Health check
- GET /metrics — Basic metrics
- GET /sessions/{session_id} — Session history
- POST /portfolio/upload — CSV portfolio upload
- DELETE /sessions/{session_id} — Clear session
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, UploadFile, File
from sse_starlette.sse import EventSourceResponse

from src.api.dependencies import (
    get_session_manager, get_context_builder,
    get_safety_guard, get_orchestrator,
)
from src.api.middleware import get_metrics
from src.core.exceptions import SafetyError
from src.core.logging import get_logger
from src.memory.context_builder import ContextBuilder
from src.memory.session_manager import SessionManager
from src.models.schemas import (
    ChatRequest, HealthResponse, MetricsResponse,
    PortfolioItem, StreamEventType,
)
from src.orchestrator.engine import OrchestratorEngine
from src.safety.guard import SafetyGuard
from src.streaming.sse import format_sse_event, stream_orchestrator_events

logger = get_logger("api.router")

router = APIRouter()


@router.post("/chat")
async def chat(
    request: Request,
    chat_req: ChatRequest,
    safety: SafetyGuard = Depends(get_safety_guard),
    session_mgr: SessionManager = Depends(get_session_manager),
    ctx_builder: ContextBuilder = Depends(get_context_builder),
    orchestrator: OrchestratorEngine = Depends(get_orchestrator),
):
    """
    Main chat endpoint with SSE streaming.

    Pipeline: Safety → Memory → Classifier → Orchestrator → Agents → Stream
    """

    # 1. Safety check
    safety_result = safety.check(chat_req.message)
    if not safety_result.is_safe:
        raise SafetyError(
            message=safety_result.blocked_reason,
            reason=safety_result.category,
        )

    # 2. Session management
    session_id = chat_req.session_id or str(uuid.uuid4())
    await session_mgr.create_session(session_id)
    await session_mgr.add_message(session_id, "user", chat_req.message)

    # 3. Build context
    context = await ctx_builder.build_context(
        session_id=session_id,
        current_message=chat_req.message,
        risk_profile=chat_req.risk_profile,
        portfolio=chat_req.portfolio,
    )

    # 4. Resolve follow-ups
    effective_query = ctx_builder.resolve_followup(chat_req.message, context)

    # 5. Stream response
    async def event_stream():
        # Yield session ID first
        yield format_sse_event(
            event=StreamEventType.THINKING,
            data=session_id,
            agent="system",
            metadata={"session_id": session_id},
        )

        full_content = ""
        agents_used = []

        async for event in stream_orchestrator_events(
            orchestrator.process(effective_query, context)
        ):
            yield event

            # Capture content for saving to memory
            try:
                import json
                event_data = json.loads(event.get("data", "{}"))
                if event.get("event") == StreamEventType.CONTENT.value:
                    full_content = event_data.get("content", "")
                if event.get("event") == StreamEventType.DONE.value:
                    meta = event_data.get("metadata", {})
                    agents_used = meta.get("agents_used", [])
            except Exception:
                pass

        # Save assistant response to memory
        if full_content:
            await session_mgr.add_message(
                session_id, "assistant", full_content,
                agents_used=agents_used,
            )

    return EventSourceResponse(event_stream())


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/metrics", response_model=MetricsResponse)
async def metrics():
    """Basic metrics endpoint."""
    m = get_metrics()
    session_mgr = get_session_manager()
    active_sessions = await session_mgr.get_session_count()
    return MetricsResponse(
        total_requests=m["total_requests"],
        active_sessions=active_sessions,
        avg_latency_ms=m["avg_latency_ms"],
        uptime_seconds=m["uptime_seconds"],
    )


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    session_mgr: SessionManager = Depends(get_session_manager),
):
    """Retrieve session conversation history."""
    messages = await session_mgr.get_messages(session_id, limit=50)
    return {
        "session_id": session_id,
        "messages": [m.model_dump() for m in messages],
        "count": len(messages),
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    session_mgr: SessionManager = Depends(get_session_manager),
):
    """Delete a session and all its history."""
    await session_mgr.delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}


@router.post("/portfolio/upload")
async def upload_portfolio(file: UploadFile = File(...)):
    """
    Upload a CSV portfolio file.

    Expected CSV columns: ticker, shares, avg_cost, asset_type
    """
    try:
        content = await file.read()
        text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))

        portfolio: list[dict] = []
        for row in reader:
            item = PortfolioItem(
                ticker=row.get("ticker", row.get("symbol", "")).upper().strip(),
                shares=float(row.get("shares", row.get("quantity", 0))),
                avg_cost=float(row.get("avg_cost", row.get("cost", row.get("price", 0)))),
                asset_type=row.get("asset_type", row.get("type", "stock")),
            )
            portfolio.append(item.model_dump())

        return {
            "status": "success",
            "holdings": len(portfolio),
            "portfolio": portfolio,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

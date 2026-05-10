"""
Valura AI — SSE Streaming.

Server-Sent Events formatting and async generator pipeline
for progressive response delivery to the frontend.
"""

from __future__ import annotations

import json
from typing import Any, AsyncGenerator

from src.core.logging import get_logger
from src.models.schemas import StreamEventType

logger = get_logger("streaming.sse")


def format_sse_event(
    event: StreamEventType,
    data: str = "",
    agent: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, str]:
    """
    Format data into an SSE-compatible event dict for sse-starlette.

    Returns:
        Dict with 'event' and 'data' keys.
    """
    payload = {
        "content": data,
        "agent": agent,
    }
    if metadata:
        payload["metadata"] = metadata

    return {
        "event": event.value,
        "data": json.dumps(payload, default=str),
    }


async def stream_orchestrator_events(
    event_generator: AsyncGenerator[dict, None],
) -> AsyncGenerator[dict[str, str], None]:
    """
    Transform orchestrator events into SSE-formatted events.

    Acts as a pipeline stage between the orchestrator and
    the SSE response handler.

    Args:
        event_generator: Async generator from OrchestratorEngine.process()

    Yields:
        SSE-formatted event dicts.
    """
    try:
        async for event in event_generator:
            event_type = event.get("event", StreamEventType.CONTENT)
            data = event.get("data", "")
            agent = event.get("agent", "")
            metadata = event.get("metadata")

            yield format_sse_event(
                event=event_type,
                data=data,
                agent=agent,
                metadata=metadata,
            )
    except Exception as e:
        logger.error(f"Streaming pipeline error: {e}")
        yield format_sse_event(
            event=StreamEventType.ERROR,
            data=f"Streaming error: {str(e)}",
        )
    finally:
        # Ensure done event is always sent
        yield format_sse_event(event=StreamEventType.DONE)

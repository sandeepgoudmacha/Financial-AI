"""
Valura AI — FastAPI Dependencies.

Dependency injection for all services used by API endpoints.
"""

from __future__ import annotations

from functools import lru_cache

from src.services.llm_service import LLMService
from src.memory.session_manager import SessionManager
from src.memory.context_builder import ContextBuilder
from src.safety.guard import SafetyGuard
from src.mcp.registry import ToolRegistry, create_default_registry
from src.orchestrator.engine import OrchestratorEngine


@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    """Singleton LLM service."""
    return LLMService()


@lru_cache(maxsize=1)
def get_session_manager() -> SessionManager:
    """Singleton session manager."""
    return SessionManager()


@lru_cache(maxsize=1)
def get_context_builder() -> ContextBuilder:
    """Singleton context builder."""
    return ContextBuilder(get_session_manager())


@lru_cache(maxsize=1)
def get_safety_guard() -> SafetyGuard:
    """Singleton safety guard."""
    return SafetyGuard(llm_service=get_llm_service())


@lru_cache(maxsize=1)
def get_tool_registry() -> ToolRegistry:
    """Singleton tool registry with all tools registered."""
    return create_default_registry()


@lru_cache(maxsize=1)
def get_orchestrator() -> OrchestratorEngine:
    """Singleton orchestrator engine."""
    return OrchestratorEngine(
        llm_service=get_llm_service(),
        tool_registry=get_tool_registry(),
    )

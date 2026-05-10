"""
Valura AI — Exception Hierarchy.

Centralized exception definitions for clean error handling
across the entire application.
"""

from __future__ import annotations


class ValuraError(Exception):
    """Base exception for all Valura AI errors."""

    def __init__(self, message: str = "An unexpected error occurred", code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class SafetyError(ValuraError):
    """Raised when safety guard blocks a request."""

    def __init__(self, message: str = "Request blocked by safety system", reason: str = ""):
        self.reason = reason
        super().__init__(message=message, code="SAFETY_BLOCKED")


class LLMError(ValuraError):
    """Raised when LLM call fails after retries."""

    def __init__(self, message: str = "LLM service error", model: str = ""):
        self.model = model
        super().__init__(message=message, code="LLM_ERROR")


class LLMTimeoutError(LLMError):
    """Raised when LLM call times out."""

    def __init__(self, message: str = "LLM request timed out", model: str = ""):
        super().__init__(message=message, model=model)
        self.code = "LLM_TIMEOUT"


class AgentError(ValuraError):
    """Raised when an agent fails to execute."""

    def __init__(self, message: str = "Agent execution failed", agent_name: str = ""):
        self.agent_name = agent_name
        super().__init__(message=message, code="AGENT_ERROR")


class ToolError(ValuraError):
    """Raised when a tool execution fails."""

    def __init__(self, message: str = "Tool execution failed", tool_name: str = ""):
        self.tool_name = tool_name
        super().__init__(message=message, code="TOOL_ERROR")


class SessionError(ValuraError):
    """Raised when session operations fail."""

    def __init__(self, message: str = "Session error", session_id: str = ""):
        self.session_id = session_id
        super().__init__(message=message, code="SESSION_ERROR")


class OrchestratorError(ValuraError):
    """Raised when orchestration logic fails."""

    def __init__(self, message: str = "Orchestration failed"):
        super().__init__(message=message, code="ORCHESTRATOR_ERROR")

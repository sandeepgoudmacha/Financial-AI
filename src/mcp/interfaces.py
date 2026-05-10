"""
Valura AI — MCP Abstract Interfaces.

Defines MCP-compatible interfaces for future integration
with external MCP servers, remote context providers,
and pluggable data tools.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.models.schemas import ToolDefinition, ToolResult


class MCPToolProvider(ABC):
    """
    Abstract interface for MCP tool providers.

    Implementations can wrap:
    - Local tools (internal)
    - Remote MCP servers
    - Third-party API adapters
    """

    @abstractmethod
    async def list_tools(self) -> list[ToolDefinition]:
        """List available tools from this provider."""
        ...

    @abstractmethod
    async def invoke_tool(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        """Invoke a tool by name with arguments."""
        ...

    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name for identification."""
        ...


class MCPResourceProvider(ABC):
    """
    Abstract interface for MCP resource providers.

    Resources are read-only data that provide context to agents:
    - File contents
    - Database records
    - API data
    - Configuration
    """

    @abstractmethod
    async def list_resources(self) -> list[dict[str, Any]]:
        """List available resources."""
        ...

    @abstractmethod
    async def read_resource(self, uri: str) -> dict[str, Any]:
        """Read a specific resource by URI."""
        ...


class MCPPromptProvider(ABC):
    """
    Abstract interface for MCP prompt providers.

    Prompts are reusable templates that guide LLM behavior.
    """

    @abstractmethod
    async def list_prompts(self) -> list[dict[str, str]]:
        """List available prompts."""
        ...

    @abstractmethod
    async def get_prompt(self, name: str, arguments: dict[str, str] | None = None) -> str:
        """Get a prompt by name with optional arguments."""
        ...


class LocalToolAdapter(MCPToolProvider):
    """
    Adapter that wraps the internal ToolRegistry as an MCP provider.

    This bridges our internal tool system with the MCP interface,
    allowing internal tools to be exposed via MCP protocol.
    """

    def __init__(self, registry: Any) -> None:
        self._registry = registry

    async def list_tools(self) -> list[ToolDefinition]:
        return self._registry.list_tools()

    async def invoke_tool(self, name: str, arguments: dict[str, Any]) -> ToolResult:
        return await self._registry.invoke(name, **arguments)

    def provider_name(self) -> str:
        return "valura_internal"

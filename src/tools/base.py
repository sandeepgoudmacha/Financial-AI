"""
Valura AI — Abstract Tool Base.

All tools inherit from BaseTool, providing a uniform interface
compatible with the MCP tool registry and agent execution layer.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from src.core.logging import get_logger
from src.models.schemas import ToolDefinition, ToolResult

logger = get_logger("tools.base")


class ToolParameter(BaseModel):
    """Describes a single tool parameter (MCP-compatible)."""
    name: str
    type: str = "string"
    description: str = ""
    required: bool = True
    default: Any = None


class BaseTool(ABC):
    """
    Abstract base class for all Valura AI tools.

    Every tool must:
    - Have a unique name and description
    - Define its parameters
    - Implement async execute()
    - Return ToolResult
    """

    name: str = "base_tool"
    description: str = "Base tool"
    category: str = "general"
    parameters: list[ToolParameter] = []

    def get_definition(self) -> ToolDefinition:
        """Export MCP-compatible tool definition with JSON schema."""
        param_schema = {
            "type": "object",
            "properties": {},
            "required": [],
        }
        for p in self.parameters:
            param_schema["properties"][p.name] = {
                "type": p.type,
                "description": p.description,
            }
            if p.required:
                param_schema["required"].append(p.name)

        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=param_schema,
            category=self.category,
        )

    async def run(self, **kwargs: Any) -> ToolResult:
        """
        Execute tool with timing and error handling.

        Wraps the abstract execute() method with production concerns.
        """
        start = time.perf_counter()
        try:
            data = await self.execute(**kwargs)
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(f"Tool [{self.name}] completed in {duration_ms:.0f}ms")
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=data,
                execution_time_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(f"Tool [{self.name}] failed after {duration_ms:.0f}ms: {e}")
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
                execution_time_ms=duration_ms,
            )

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute the tool logic.

        Subclasses must implement this method.

        Returns:
            Any data produced by the tool.
        """
        ...

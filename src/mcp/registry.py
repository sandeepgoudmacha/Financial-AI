"""
Valura AI — MCP Tool Registry.

Central registry for all tools with MCP-compatible interfaces.
Supports tool discovery, registration, and invocation.
Future: connect to external MCP servers via adapters.
"""

from __future__ import annotations

from typing import Any, Optional

from src.tools.base import BaseTool
from src.models.schemas import ToolDefinition, ToolResult
from src.core.logging import get_logger

logger = get_logger("mcp.registry")


class ToolRegistry:
    """
    Singleton tool registry — MCP-compatible.

    All tools register here and are discoverable by agents.
    Designed to be extended with external MCP server connections.
    """

    _instance: Optional["ToolRegistry"] = None

    def __new__(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: dict[str, BaseTool] = {}
            cls._instance._initialized = False
        return cls._instance

    def register(self, tool: BaseTool) -> None:
        """Register a tool in the registry."""
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name} [{tool.category}]")

    def register_many(self, tools: list[BaseTool]) -> None:
        """Register multiple tools at once."""
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_by_category(self, category: str) -> list[BaseTool]:
        """Get all tools in a category."""
        return [t for t in self._tools.values() if t.category == category]

    def list_tools(self) -> list[ToolDefinition]:
        """List all registered tools as MCP-compatible definitions."""
        return [t.get_definition() for t in self._tools.values()]

    def list_names(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    async def invoke(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Invoke a tool by name with given parameters."""
        tool = self._tools.get(tool_name)
        if not tool:
            return ToolResult(tool_name=tool_name, success=False, error=f"Tool '{tool_name}' not found")
        return await tool.run(**kwargs)

    @property
    def count(self) -> int:
        return len(self._tools)

    def reset(self) -> None:
        """Reset registry (for testing)."""
        self._tools.clear()


def create_default_registry() -> ToolRegistry:
    """Create and populate the default tool registry with all built-in tools."""
    from src.tools.market_tools import (
        StockDataTool, CompanyInfoTool, SectorAnalysisTool,
        NewsSearchTool, StockComparisonTool,
    )
    from src.tools.calculator_tools import (
        CAGRCalculatorTool, SIPCalculatorTool, CompoundInterestTool,
        RetirementProjectionTool, SharpeRatioTool, PortfolioVolatilityTool,
    )
    from src.tools.visualization_tools import (
        LineChartTool, BarChartTool, PieChartTool, PerformanceChartTool,
    )

    registry = ToolRegistry()
    registry.register_many([
        # Market data
        StockDataTool(), CompanyInfoTool(), SectorAnalysisTool(),
        NewsSearchTool(), StockComparisonTool(),
        # Calculators
        CAGRCalculatorTool(), SIPCalculatorTool(), CompoundInterestTool(),
        RetirementProjectionTool(), SharpeRatioTool(), PortfolioVolatilityTool(),
        # Visualization
        LineChartTool(), BarChartTool(), PieChartTool(), PerformanceChartTool(),
    ])
    logger.info(f"Default registry initialized with {registry.count} tools")
    return registry

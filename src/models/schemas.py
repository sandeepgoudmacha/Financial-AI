"""
Valura AI — Pydantic Models & Schemas.

All data contracts for the application are defined here.
Every API request, response, agent output, and internal
message uses these typed schemas.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Enums
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class AgentType(str, Enum):
    MARKET_RESEARCH = "market_research"
    INVESTMENT_STRATEGY = "investment_strategy"
    FINANCIAL_CALCULATOR = "financial_calculator"


class RiskProfile(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class StreamEventType(str, Enum):
    THINKING = "thinking"
    AGENT_ACTIVITY = "agent_activity"
    CONTENT = "content"
    CHART = "chart"
    TABLE = "table"
    SOURCES = "sources"
    ERROR = "error"
    DONE = "done"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API Request / Response
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ChatRequest(BaseModel):
    """Incoming chat message from the frontend."""
    message: str = Field(..., min_length=1, max_length=4000, description="User query")
    session_id: str = Field(default="", description="Session identifier for continuity")
    risk_profile: RiskProfile = Field(default=RiskProfile.MODERATE)
    portfolio: Optional[list[PortfolioItem]] = Field(default=None, description="User portfolio")


class ChatResponse(BaseModel):
    """Final (non-streaming) response structure."""
    session_id: str
    content: str
    agents_used: list[str] = Field(default_factory=list)
    charts: list[ChartData] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StreamEvent(BaseModel):
    """Single SSE event payload."""
    event: StreamEventType
    data: str = ""
    agent: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MetricsResponse(BaseModel):
    """Basic metrics response."""
    total_requests: int = 0
    active_sessions: int = 0
    avg_latency_ms: float = 0.0
    uptime_seconds: float = 0.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Agent Outputs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class AgentResult(BaseModel):
    """Structured output from any agent."""
    agent_name: str
    agent_type: AgentType
    content: str = Field(description="Markdown-formatted response")
    charts: list[ChartData] = Field(default_factory=list)
    tables: list[TableData] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    execution_time_ms: float = 0.0
    error: Optional[str] = None


class ChartData(BaseModel):
    """Chart data for frontend rendering."""
    title: str
    chart_type: str = "line"  # line, bar, pie, area
    image_base64: str = Field(description="Base64-encoded PNG image")
    description: str = ""


class TableData(BaseModel):
    """Tabular data for frontend rendering."""
    title: str
    headers: list[str]
    rows: list[list[str]]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Financial Data
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class StockData(BaseModel):
    """Stock data from financial APIs."""
    ticker: str
    name: str = ""
    current_price: float = 0.0
    previous_close: float = 0.0
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    volume: Optional[int] = None
    sector: str = ""
    industry: str = ""
    change_percent: float = 0.0
    currency: str = "USD"


class PortfolioItem(BaseModel):
    """Single holding in a user portfolio."""
    ticker: str
    shares: float = 0.0
    avg_cost: float = 0.0
    asset_type: str = "stock"  # stock, etf, bond, crypto, cash


class CalculationResult(BaseModel):
    """Result from financial calculations."""
    calculation_type: str
    inputs: dict[str, Any]
    result: float
    formatted_result: str
    breakdown: dict[str, Any] = Field(default_factory=dict)
    explanation: str = ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Safety
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class SafetyCheckResult(BaseModel):
    """Result from safety guard check."""
    is_safe: bool = True
    blocked_reason: str = ""
    category: str = ""
    confidence: float = 1.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Intent Classification
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class IntentClassification(BaseModel):
    """Result from intent classifier."""
    agents: list[AgentType] = Field(description="Which agents to activate")
    parallel: bool = Field(default=False, description="Run agents in parallel")
    entities: dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted entities (tickers, amounts, timeframes)"
    )
    reasoning: str = Field(default="", description="Why these agents were chosen")
    query_reformulation: str = Field(default="", description="Cleaned/expanded query")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Session & Memory
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class SessionMessage(BaseModel):
    """A single message in session history."""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agents_used: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionContext(BaseModel):
    """Context built from session history for LLM."""
    session_id: str
    messages: list[SessionMessage] = Field(default_factory=list)
    mentioned_tickers: list[str] = Field(default_factory=list)
    user_risk_profile: RiskProfile = RiskProfile.MODERATE
    portfolio: Optional[list[PortfolioItem]] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MCP / Tools
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ToolDefinition(BaseModel):
    """MCP-compatible tool definition."""
    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    category: str = "general"


class ToolResult(BaseModel):
    """Result from executing a tool."""
    tool_name: str
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


# Update forward references
ChatResponse.model_rebuild()
ChatRequest.model_rebuild()
AgentResult.model_rebuild()

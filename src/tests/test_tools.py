"""
Valura AI — Calculator & Tool Tests.

Pure math tests — no API keys needed.
"""

import pytest
from src.tools.calculator_tools import (
    CAGRCalculatorTool, SIPCalculatorTool, CompoundInterestTool,
    SharpeRatioTool,
)
from src.mcp.registry import ToolRegistry


class TestCAGRCalculator:
    @pytest.fixture
    def tool(self):
        return CAGRCalculatorTool()

    @pytest.mark.asyncio
    async def test_basic_cagr(self, tool):
        result = await tool.execute(initial_value=10000, final_value=25000, years=5)
        assert 0.15 < result["cagr"] < 0.25  # ~20.11%
        assert result["cagr_percent"] == round(result["cagr"] * 100, 2)

    @pytest.mark.asyncio
    async def test_cagr_double(self, tool):
        result = await tool.execute(initial_value=1000, final_value=2000, years=7)
        assert 0.09 < result["cagr"] < 0.11  # ~10.41%

    @pytest.mark.asyncio
    async def test_cagr_negative_growth(self, tool):
        result = await tool.execute(initial_value=10000, final_value=5000, years=3)
        assert result["cagr"] < 0  # Negative CAGR


class TestSIPCalculator:
    @pytest.fixture
    def tool(self):
        return SIPCalculatorTool()

    @pytest.mark.asyncio
    async def test_basic_sip(self, tool):
        result = await tool.execute(monthly_investment=1000, annual_return=0.12, years=10)
        assert result["future_value"] > result["total_invested"]
        assert result["total_invested"] == 120000
        assert result["wealth_gained"] > 0

    @pytest.mark.asyncio
    async def test_sip_zero_return(self, tool):
        result = await tool.execute(monthly_investment=500, annual_return=0, years=5)
        assert result["future_value"] == result["total_invested"]
        assert result["total_invested"] == 30000

    @pytest.mark.asyncio
    async def test_sip_yearly_breakdown(self, tool):
        result = await tool.execute(monthly_investment=1000, annual_return=0.10, years=5)
        assert len(result["yearly_breakdown"]) == 5
        assert result["yearly_breakdown"][-1]["value"] == result["future_value"]


class TestCompoundInterest:
    @pytest.fixture
    def tool(self):
        return CompoundInterestTool()

    @pytest.mark.asyncio
    async def test_annual_compounding(self, tool):
        result = await tool.execute(principal=10000, rate=0.10, years=10, compounds_per_year=1)
        expected = 10000 * (1.10 ** 10)
        assert abs(result["final_amount"] - round(expected, 2)) < 1

    @pytest.mark.asyncio
    async def test_monthly_compounding(self, tool):
        result = await tool.execute(principal=10000, rate=0.10, years=10, compounds_per_year=12)
        assert result["final_amount"] > 10000 * (1.10 ** 10)  # Monthly > annual


class TestSharpeRatio:
    @pytest.fixture
    def tool(self):
        return SharpeRatioTool()

    @pytest.mark.asyncio
    async def test_good_sharpe(self, tool):
        result = await tool.execute(portfolio_return=0.15, risk_free_rate=0.04, volatility=0.10)
        assert result["sharpe_ratio"] == 1.1  # (0.15 - 0.04) / 0.10
        assert result["rating"] == "Good"

    @pytest.mark.asyncio
    async def test_poor_sharpe(self, tool):
        result = await tool.execute(portfolio_return=0.06, risk_free_rate=0.04, volatility=0.20)
        assert result["sharpe_ratio"] == 0.1
        assert result["rating"] == "Poor"


class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry()
        registry.reset()
        tool = CAGRCalculatorTool()
        registry.register(tool)
        assert registry.get("cagr_calculator") is tool
        assert registry.count == 1

    def test_list_tools(self):
        registry = ToolRegistry()
        registry.reset()
        registry.register(CAGRCalculatorTool())
        registry.register(SIPCalculatorTool())
        definitions = registry.list_tools()
        assert len(definitions) == 2
        names = [d.name for d in definitions]
        assert "cagr_calculator" in names
        assert "sip_calculator" in names

    def test_get_by_category(self):
        registry = ToolRegistry()
        registry.reset()
        registry.register(CAGRCalculatorTool())
        registry.register(SIPCalculatorTool())
        calc_tools = registry.get_by_category("calculator")
        assert len(calc_tools) == 2

    @pytest.mark.asyncio
    async def test_invoke(self):
        registry = ToolRegistry()
        registry.reset()
        registry.register(CAGRCalculatorTool())
        result = await registry.invoke("cagr_calculator", initial_value=1000, final_value=2000, years=5)
        assert result.success is True
        assert result.data["cagr"] > 0

    @pytest.mark.asyncio
    async def test_invoke_missing_tool(self):
        registry = ToolRegistry()
        registry.reset()
        result = await registry.invoke("nonexistent_tool")
        assert result.success is False
        assert "not found" in result.error

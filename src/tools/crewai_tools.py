"""
Valura AI — CrewAI Tools Wrapper.

Wraps our existing base tools into CrewAI compatible tools using the @tool decorator.
"""

from __future__ import annotations

import asyncio
from crewai.tools import tool

from src.tools.market_tools import (
    StockDataTool, CompanyInfoTool, SectorAnalysisTool, NewsSearchTool, StockComparisonTool
)
from src.tools.calculator_tools import (
    CAGRCalculatorTool, SIPCalculatorTool, CompoundInterestTool,
    RetirementProjectionTool, SharpeRatioTool, PortfolioVolatilityTool
)
from src.tools.visualization_tools import (
    LineChartTool, PieChartTool, PerformanceChartTool
)

# Helper to run async tools synchronously for CrewAI compatibility
# CrewAI natively executes tools synchronously in its main loop unless configured otherwise
def run_sync(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an event loop (e.g., fastAPI), run in a new thread
            import threading
            result = None
            exception = None
            def run():
                nonlocal result, exception
                try:
                    result = asyncio.run(coro)
                except Exception as e:
                    exception = e
            thread = threading.Thread(target=run)
            thread.start()
            thread.join()
            if exception:
                raise exception
            return result
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)

# ── Market Tools ──────────────────────────────────────────────

@tool("stock_data")
def get_stock_data(ticker: str, period: str = "1mo") -> str:
    """Get current stock price, key metrics, and recent performance for a given ticker (e.g. 'AAPL')."""
    t = StockDataTool()
    res = run_sync(t.execute(ticker=ticker, period=period))
    return str(res)

@tool("company_info")
def get_company_info(ticker: str) -> str:
    """Get detailed company profile, financials, and analyst recommendations."""
    t = CompanyInfoTool()
    res = run_sync(t.execute(ticker=ticker))
    return str(res)

@tool("sector_analysis")
def get_sector_analysis(sector: str = "all") -> str:
    """Analyze sector performance using major sector ETFs."""
    t = SectorAnalysisTool()
    res = run_sync(t.execute(sector=sector))
    return str(res)

@tool("news_search")
def search_news(query: str, max_results: int = 8) -> str:
    """Search for recent financial news and market analysis."""
    t = NewsSearchTool()
    res = run_sync(t.execute(query=query, max_results=max_results))
    return str(res)

@tool("stock_comparison")
def compare_stocks(tickers: str) -> str:
    """Compare key metrics for multiple stocks (comma-separated)."""
    t = StockComparisonTool()
    res = run_sync(t.execute(tickers=tickers))
    return str(res)

# ── Calculator Tools ──────────────────────────────────────────

@tool("cagr_calculator")
def calculate_cagr(initial_value: float, final_value: float, years: float) -> str:
    """Calculate Compound Annual Growth Rate (CAGR). All inputs are numbers."""
    t = CAGRCalculatorTool()
    res = run_sync(t.execute(initial_value=initial_value, final_value=final_value, years=years))
    return str(res)

@tool("sip_calculator")
def calculate_sip(monthly_investment: float, annual_return: float, years: int) -> str:
    """Calculate returns for a Systematic Investment Plan (SIP). 
    annual_return MUST be a decimal (e.g. 0.12 for 12%)."""
    t = SIPCalculatorTool()
    res = run_sync(t.execute(monthly_investment=monthly_investment, annual_return=annual_return, years=years))
    return str(res)

@tool("compound_interest_calculator")
def calculate_compound_interest(principal: float, rate: float, years: int, compounds_per_year: int = 1) -> str:
    """Calculate compound interest."""
    t = CompoundInterestTool()
    res = run_sync(t.execute(principal=principal, rate=rate, years=years, compounds_per_year=compounds_per_year))
    return str(res)

@tool("retirement_projection")
def calculate_retirement(current_age: int, retirement_age: int, monthly_expense: float, current_savings: float = 0, monthly_saving: float = 0) -> str:
    """Calculate required retirement corpus and savings projection."""
    t = RetirementProjectionTool()
    res = run_sync(t.execute(
        current_age=current_age, retirement_age=retirement_age, 
        monthly_expense=monthly_expense, current_savings=current_savings, 
        monthly_saving=monthly_saving
    ))
    return str(res)

@tool("sharpe_ratio_calculator")
def calculate_sharpe_ratio(portfolio_return: float, volatility: float, risk_free_rate: float = 0.04) -> str:
    """Calculate the Sharpe Ratio for a portfolio."""
    t = SharpeRatioTool()
    res = run_sync(t.execute(portfolio_return=portfolio_return, risk_free_rate=risk_free_rate, volatility=volatility))
    return str(res)

@tool("portfolio_volatility_calculator")
def calculate_volatility(weights: str, volatilities: str, correlations: str) -> str:
    """Calculate the volatility of a multi-asset portfolio. Weights, volatilities and correlations must be comma-separated strings."""
    w = [float(x) for x in weights.split(",")]
    v = [float(x) for x in volatilities.split(",")]
    c = []
    for row in correlations.split(";"):
        c.append([float(x) for x in row.split(",")])
    
    t = PortfolioVolatilityTool()
    res = run_sync(t.execute(weights=w, volatilities=v, correlations=c))
    return str(res)

# ── Visualization Tools ───────────────────────────────────────

@tool("line_chart_generator")
def generate_line_chart(title: str, x_labels: str, y_values: str, series_names: str, y_label: str = "Value") -> str:
    """Generate a line chart and return its Base64 string. y_values can be pipe-separated series of comma-separated floats."""
    t = LineChartTool()
    res = run_sync(t.execute(title=title, x_labels=x_labels, y_values=y_values, series_names=series_names, y_label=y_label))
    return str(res)

@tool("pie_chart_generator")
def generate_pie_chart(title: str, labels: str, values: str) -> str:
    """Generate a pie chart and return its Base64 string."""
    t = PieChartTool()
    res = run_sync(t.execute(title=title, labels=labels, values=values))
    return str(res)

@tool("performance_chart_generator")
def generate_performance_chart(ticker: str, history: str) -> str:
    """Generate a stock performance chart from history dict and return its Base64 string."""
    t = PerformanceChartTool()
    res = run_sync(t.execute(ticker=ticker, history=history))
    return str(res)

# Tool collections for agents
MARKET_TOOLS = [
    get_stock_data, get_company_info, get_sector_analysis, search_news, compare_stocks
]

STRATEGY_TOOLS = [
    get_sector_analysis, get_stock_data
]

CALCULATOR_TOOLS = [
    calculate_cagr, calculate_sip, calculate_compound_interest,
    calculate_retirement, calculate_sharpe_ratio, calculate_volatility
]

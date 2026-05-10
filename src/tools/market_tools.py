"""
Valura AI — Market Data Tools.

Real financial data integration via yfinance and DuckDuckGo search.
All tools fetch LIVE data — nothing is hardcoded.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pandas as pd
import yfinance as yf
from duckduckgo_search import DDGS

from src.tools.base import BaseTool, ToolParameter
from src.core.logging import get_logger

logger = get_logger("tools.market")


class StockDataTool(BaseTool):
    """Fetch live stock price data and key metrics via yfinance."""

    name = "stock_data"
    description = "Get current stock price, key metrics, and recent performance for a given ticker."
    category = "market_data"
    parameters = [
        ToolParameter(name="ticker", type="string", description="Stock ticker symbol (e.g., AAPL)"),
        ToolParameter(name="period", type="string", description="History period", required=False, default="1mo"),
    ]

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        ticker = kwargs.get("ticker", "").upper().strip()
        period = kwargs.get("period", "1mo")
        if not ticker:
            raise ValueError("Ticker symbol is required")

        def _fetch() -> dict[str, Any]:
            stock = yf.Ticker(ticker)
            info = stock.info or {}
            hist = stock.history(period=period)
            current_price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose", 0)
            change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close else 0

            history_data = []
            if not hist.empty:
                for date, row in hist.iterrows():
                    history_data.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "close": round(row.get("Close", 0), 2),
                        "volume": int(row.get("Volume", 0)),
                    })

            return {
                "ticker": ticker, "name": info.get("longName", ticker),
                "current_price": round(current_price, 2), "previous_close": round(prev_close, 2),
                "change_percent": round(change_pct, 2), "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"), "forward_pe": info.get("forwardPE"),
                "dividend_yield": info.get("dividendYield"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "volume": info.get("volume"), "sector": info.get("sector", ""),
                "industry": info.get("industry", ""), "beta": info.get("beta"),
                "eps": info.get("trailingEps"), "profit_margin": info.get("profitMargins"),
                "currency": info.get("currency", "USD"), "history": history_data,
            }
        return await asyncio.to_thread(_fetch)


class CompanyInfoTool(BaseTool):
    """Fetch detailed company information and financial statements."""

    name = "company_info"
    description = "Get detailed company profile, financials, and analyst recommendations."
    category = "market_data"
    parameters = [
        ToolParameter(name="ticker", type="string", description="Stock ticker symbol"),
    ]

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        ticker = kwargs.get("ticker", "").upper().strip()
        if not ticker:
            raise ValueError("Ticker symbol is required")

        def _fetch() -> dict[str, Any]:
            stock = yf.Ticker(ticker)
            info = stock.info or {}
            recommendations = []
            try:
                recs = stock.recommendations
                if recs is not None and not recs.empty:
                    for _, row in recs.tail(5).iterrows():
                        recommendations.append({
                            "firm": row.get("Firm", ""), "grade": row.get("To Grade", ""),
                        })
            except Exception:
                pass

            financials = {}
            try:
                income = stock.income_stmt
                if income is not None and not income.empty:
                    latest = income.iloc[:, 0]
                    for key in ["Total Revenue", "Net Income", "Operating Income", "Gross Profit"]:
                        val = latest.get(key)
                        if pd.notna(val):
                            financials[key.lower().replace(" ", "_")] = float(val)
            except Exception:
                pass

            return {
                "ticker": ticker, "name": info.get("longName", ""),
                "description": info.get("longBusinessSummary", ""),
                "sector": info.get("sector", ""), "industry": info.get("industry", ""),
                "employees": info.get("fullTimeEmployees"), "website": info.get("website", ""),
                "market_cap": info.get("marketCap"), "profit_margins": info.get("profitMargins"),
                "return_on_equity": info.get("returnOnEquity"),
                "debt_to_equity": info.get("debtToEquity"),
                "book_value": info.get("bookValue"), "financials": financials,
                "recommendations": recommendations,
                "target_mean": info.get("targetMeanPrice"),
                "target_high": info.get("targetHighPrice"),
                "target_low": info.get("targetLowPrice"),
            }
        return await asyncio.to_thread(_fetch)


class SectorAnalysisTool(BaseTool):
    """Analyze sector performance using representative ETFs."""

    name = "sector_analysis"
    description = "Analyze sector performance using major sector ETFs."
    category = "market_data"
    parameters = [
        ToolParameter(name="sector", type="string", description="Sector name or 'all'", required=False, default="all"),
    ]

    SECTOR_ETFS = {
        "Technology": "XLK", "Healthcare": "XLV", "Financial": "XLF",
        "Energy": "XLE", "Consumer Discretionary": "XLY", "Consumer Staples": "XLP",
        "Industrials": "XLI", "Materials": "XLB", "Utilities": "XLU",
        "Real Estate": "XLRE", "Communication Services": "XLC",
    }

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        sector = kwargs.get("sector", "all")
        def _fetch() -> dict[str, Any]:
            results = {}
            etfs = self.SECTOR_ETFS if sector == "all" else {
                k: v for k, v in self.SECTOR_ETFS.items() if sector.lower() in k.lower()
            } or self.SECTOR_ETFS

            for name, etf_ticker in etfs.items():
                try:
                    hist = yf.Ticker(etf_ticker).history(period="1mo")
                    if not hist.empty:
                        change_pct = ((hist.iloc[-1]["Close"] - hist.iloc[0]["Close"]) / hist.iloc[0]["Close"]) * 100
                        results[name] = {"etf": etf_ticker, "monthly_change_pct": round(change_pct, 2)}
                except Exception:
                    continue
            return {"sectors": results}
        return await asyncio.to_thread(_fetch)


class NewsSearchTool(BaseTool):
    """Search for financial news using DuckDuckGo."""

    name = "news_search"
    description = "Search for recent financial news and market analysis."
    category = "market_data"
    parameters = [
        ToolParameter(name="query", type="string", description="Search query"),
        ToolParameter(name="max_results", type="integer", description="Max results", required=False, default=8),
    ]

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 8)
        if not query:
            raise ValueError("Search query is required")

        def _search() -> dict[str, Any]:
            results = []
            try:
                with DDGS() as ddgs:
                    for item in ddgs.news(keywords=f"{query} finance stock", max_results=max_results):
                        results.append({
                            "title": item.get("title", ""), "body": item.get("body", ""),
                            "url": item.get("url", ""), "source": item.get("source", ""),
                        })
            except Exception:
                try:
                    with DDGS() as ddgs:
                        for item in ddgs.text(keywords=f"{query} financial", max_results=max_results):
                            results.append({
                                "title": item.get("title", ""), "body": item.get("body", ""),
                                "url": item.get("href", ""),
                            })
                except Exception:
                    pass
            return {"query": query, "results": results, "count": len(results)}
        return await asyncio.to_thread(_search)


class StockComparisonTool(BaseTool):
    """Compare multiple stocks side by side."""

    name = "stock_comparison"
    description = "Compare key metrics for multiple stocks."
    category = "market_data"
    parameters = [
        ToolParameter(name="tickers", type="string", description="Comma-separated tickers"),
    ]

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        tickers = [t.strip().upper() for t in kwargs.get("tickers", "").split(",") if t.strip()]
        if len(tickers) < 2:
            raise ValueError("At least 2 tickers required")

        def _compare() -> dict[str, Any]:
            data = []
            for t in tickers[:5]:
                try:
                    info = yf.Ticker(t).info or {}
                    data.append({
                        "ticker": t, "name": info.get("longName", t),
                        "price": info.get("currentPrice") or info.get("regularMarketPrice", 0),
                        "market_cap": info.get("marketCap"), "pe_ratio": info.get("trailingPE"),
                        "dividend_yield": info.get("dividendYield"), "beta": info.get("beta"),
                        "profit_margin": info.get("profitMargins"), "sector": info.get("sector", ""),
                    })
                except Exception as e:
                    data.append({"ticker": t, "error": str(e)})
            return {"comparisons": data}
        return await asyncio.to_thread(_compare)

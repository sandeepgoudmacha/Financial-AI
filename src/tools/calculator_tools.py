"""
Valura AI — Financial Calculator Tools.

Pure math tools for CAGR, SIP, compound interest, retirement projections,
Sharpe ratio, portfolio volatility, and more. No external APIs needed.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from src.tools.base import BaseTool, ToolParameter


class CAGRCalculatorTool(BaseTool):
    """Calculate Compound Annual Growth Rate."""

    name = "cagr_calculator"
    description = "Calculate CAGR given initial value, final value, and years."
    category = "calculator"
    parameters = [
        ToolParameter(name="initial_value", type="number", description="Starting investment value"),
        ToolParameter(name="final_value", type="number", description="Ending investment value"),
        ToolParameter(name="years", type="number", description="Number of years"),
    ]

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        iv = float(kwargs["initial_value"])
        fv = float(kwargs["final_value"])
        years = float(kwargs["years"])
        if iv <= 0 or years <= 0:
            raise ValueError("Initial value and years must be positive")
        cagr = (fv / iv) ** (1 / years) - 1
        return {
            "cagr": round(cagr, 6), "cagr_percent": round(cagr * 100, 2),
            "initial_value": iv, "final_value": fv, "years": years,
            "explanation": f"An investment of ${iv:,.2f} growing to ${fv:,.2f} over {years} years represents a CAGR of {cagr*100:.2f}%.",
        }


class SIPCalculatorTool(BaseTool):
    """Calculate Systematic Investment Plan returns."""

    name = "sip_calculator"
    description = "Calculate future value of regular monthly SIP investments."
    category = "calculator"
    parameters = [
        ToolParameter(name="monthly_investment", type="number", description="Monthly investment amount"),
        ToolParameter(name="annual_return", type="number", description="Expected annual return rate (e.g. 0.12 for 12%)"),
        ToolParameter(name="years", type="number", description="Investment duration in years"),
    ]

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        monthly = float(kwargs["monthly_investment"])
        annual_return = float(kwargs["annual_return"])
        years = float(kwargs["years"])
        monthly_rate = annual_return / 12
        months = int(years * 12)
        total_invested = monthly * months

        if monthly_rate == 0:
            future_value = total_invested
        else:
            future_value = monthly * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)

        wealth_gained = future_value - total_invested
        yearly_breakdown = []
        for y in range(1, int(years) + 1):
            m = y * 12
            if monthly_rate == 0:
                fv = monthly * m
            else:
                fv = monthly * (((1 + monthly_rate) ** m - 1) / monthly_rate) * (1 + monthly_rate)
            yearly_breakdown.append({"year": y, "invested": round(monthly * m, 2), "value": round(fv, 2)})

        return {
            "future_value": round(future_value, 2), "total_invested": round(total_invested, 2),
            "wealth_gained": round(wealth_gained, 2), "monthly_investment": monthly,
            "annual_return_pct": round(annual_return * 100, 2), "years": years,
            "yearly_breakdown": yearly_breakdown,
        }


class CompoundInterestTool(BaseTool):
    """Calculate compound interest with flexible compounding frequencies."""

    name = "compound_interest"
    description = "Calculate compound interest with various compounding frequencies."
    category = "calculator"
    parameters = [
        ToolParameter(name="principal", type="number", description="Initial principal amount"),
        ToolParameter(name="rate", type="number", description="Annual interest rate (e.g. 0.08 for 8%)"),
        ToolParameter(name="years", type="number", description="Number of years"),
        ToolParameter(name="compounds_per_year", type="integer", description="Compounding frequency", required=False, default=12),
    ]

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        P = float(kwargs["principal"])
        r = float(kwargs["rate"])
        t = float(kwargs["years"])
        n = int(kwargs.get("compounds_per_year", 12))
        A = P * (1 + r / n) ** (n * t)
        interest_earned = A - P
        return {
            "final_amount": round(A, 2), "interest_earned": round(interest_earned, 2),
            "principal": P, "rate_pct": round(r * 100, 2), "years": t,
            "compounding": {1: "Annual", 4: "Quarterly", 12: "Monthly", 365: "Daily"}.get(n, f"{n}x/year"),
        }


class RetirementProjectionTool(BaseTool):
    """Project retirement savings and income needs."""

    name = "retirement_projection"
    description = "Calculate retirement corpus needed and project savings growth."
    category = "calculator"
    parameters = [
        ToolParameter(name="current_age", type="integer", description="Current age"),
        ToolParameter(name="retirement_age", type="integer", description="Target retirement age"),
        ToolParameter(name="monthly_expense", type="number", description="Current monthly expenses"),
        ToolParameter(name="current_savings", type="number", description="Current savings", required=False, default=0),
        ToolParameter(name="monthly_saving", type="number", description="Monthly savings", required=False, default=0),
        ToolParameter(name="expected_return", type="number", description="Expected annual return (e.g. 0.10)", required=False, default=0.10),
        ToolParameter(name="inflation", type="number", description="Annual inflation rate", required=False, default=0.06),
    ]

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        current_age = int(kwargs["current_age"])
        retire_age = int(kwargs["retirement_age"])
        monthly_expense = float(kwargs["monthly_expense"])
        current_savings = float(kwargs.get("current_savings", 0))
        monthly_saving = float(kwargs.get("monthly_saving", 0))
        ret = float(kwargs.get("expected_return", 0.10))
        inflation = float(kwargs.get("inflation", 0.06))

        years_to_retire = retire_age - current_age
        retirement_years = 85 - retire_age  # Assume life expectancy 85

        future_monthly_expense = monthly_expense * (1 + inflation) ** years_to_retire
        future_annual_expense = future_monthly_expense * 12
        real_return = ((1 + ret) / (1 + inflation)) - 1
        corpus_needed = future_annual_expense * ((1 - (1 + real_return) ** (-retirement_years)) / real_return) if real_return > 0 else future_annual_expense * retirement_years

        monthly_rate = ret / 12
        months = years_to_retire * 12
        if monthly_rate > 0:
            projected_savings = current_savings * (1 + ret) ** years_to_retire + monthly_saving * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
        else:
            projected_savings = current_savings + monthly_saving * months

        shortfall = max(0, corpus_needed - projected_savings)

        return {
            "corpus_needed": round(corpus_needed, 2), "projected_savings": round(projected_savings, 2),
            "shortfall": round(shortfall, 2), "future_monthly_expense": round(future_monthly_expense, 2),
            "years_to_retire": years_to_retire, "on_track": projected_savings >= corpus_needed,
        }


class SharpeRatioTool(BaseTool):
    """Calculate Sharpe Ratio for risk-adjusted returns."""

    name = "sharpe_ratio"
    description = "Calculate Sharpe Ratio given returns, risk-free rate, and volatility."
    category = "calculator"
    parameters = [
        ToolParameter(name="portfolio_return", type="number", description="Annual portfolio return (e.g. 0.15 for 15%)"),
        ToolParameter(name="risk_free_rate", type="number", description="Risk-free rate (e.g. 0.04 for 4%)", required=False, default=0.04),
        ToolParameter(name="volatility", type="number", description="Portfolio standard deviation"),
    ]

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        ret = float(kwargs["portfolio_return"])
        rf = float(kwargs.get("risk_free_rate", 0.04))
        vol = float(kwargs["volatility"])
        if vol == 0:
            raise ValueError("Volatility cannot be zero")
        sharpe = (ret - rf) / vol
        rating = "Excellent" if sharpe > 2 else "Good" if sharpe > 1 else "Acceptable" if sharpe > 0.5 else "Poor"
        return {
            "sharpe_ratio": round(sharpe, 4), "rating": rating,
            "portfolio_return_pct": round(ret * 100, 2),
            "risk_free_rate_pct": round(rf * 100, 2),
            "volatility_pct": round(vol * 100, 2),
        }


class PortfolioVolatilityTool(BaseTool):
    """Calculate portfolio volatility from historical returns."""

    name = "portfolio_volatility"
    description = "Calculate annualized volatility from a series of returns."
    category = "calculator"
    parameters = [
        ToolParameter(name="returns", type="string", description="Comma-separated periodic returns (e.g. 0.02,-0.01,0.03)"),
        ToolParameter(name="periods_per_year", type="integer", description="Periods per year (12 for monthly)", required=False, default=12),
    ]

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        returns_str = kwargs.get("returns", "")
        periods = int(kwargs.get("periods_per_year", 12))
        returns = [float(r.strip()) for r in returns_str.split(",") if r.strip()]
        if len(returns) < 2:
            raise ValueError("At least 2 return periods required")
        arr = np.array(returns)
        periodic_vol = float(np.std(arr, ddof=1))
        annualized_vol = periodic_vol * math.sqrt(periods)
        return {
            "periodic_volatility": round(periodic_vol, 6),
            "annualized_volatility": round(annualized_vol, 6),
            "annualized_volatility_pct": round(annualized_vol * 100, 2),
            "mean_return": round(float(np.mean(arr)), 6), "num_periods": len(returns),
        }

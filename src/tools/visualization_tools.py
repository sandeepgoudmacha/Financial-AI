"""
Valura AI — Visualization Tools.

Generate professional financial charts using matplotlib.
Charts are returned as base64-encoded PNG images for frontend rendering.
"""

from __future__ import annotations

import asyncio
import base64
import io
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

from src.tools.base import BaseTool, ToolParameter
from src.core.logging import get_logger

logger = get_logger("tools.visualization")

# ── Professional chart styling ────────────────────────────────
DARK_BG = "#0d1117"
CARD_BG = "#161b22"
GRID_COLOR = "#21262d"
TEXT_COLOR = "#e6edf3"
ACCENT_COLORS = ["#58a6ff", "#3fb950", "#f78166", "#d2a8ff", "#79c0ff", "#56d364", "#ffa657", "#ff7b72"]


def _apply_style(fig: plt.Figure, ax: plt.Axes) -> None:
    """Apply professional dark-theme styling to a chart."""
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(CARD_BG)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRID_COLOR)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)
    ax.grid(True, alpha=0.15, color=GRID_COLOR)


def _fig_to_base64(fig: plt.Figure) -> str:
    """Convert matplotlib figure to base64 PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


class LineChartTool(BaseTool):
    """Generate professional line charts."""

    name = "line_chart"
    description = "Generate a line chart from data points."
    category = "visualization"
    parameters = [
        ToolParameter(name="title", type="string", description="Chart title"),
        ToolParameter(name="x_labels", type="string", description="Comma-separated X-axis labels"),
        ToolParameter(name="y_values", type="string", description="Comma-separated Y values (multiple series separated by |)"),
        ToolParameter(name="series_names", type="string", description="Comma-separated series names", required=False, default=""),
        ToolParameter(name="y_label", type="string", description="Y-axis label", required=False, default="Value"),
    ]

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        def _generate() -> str:
            title = kwargs.get("title", "Chart")
            x_labels = [x.strip() for x in kwargs.get("x_labels", "").split(",")]
            y_series_raw = kwargs.get("y_values", "").split("|")
            series_names = [s.strip() for s in kwargs.get("series_names", "").split(",") if s.strip()]
            y_label = kwargs.get("y_label", "Value")

            fig, ax = plt.subplots(figsize=(10, 5))
            _apply_style(fig, ax)

            for i, series in enumerate(y_series_raw):
                values = [float(v.strip()) for v in series.split(",") if v.strip()]
                x = range(len(values))
                color = ACCENT_COLORS[i % len(ACCENT_COLORS)]
                label = series_names[i] if i < len(series_names) else f"Series {i+1}"
                ax.plot(x, values, color=color, linewidth=2, label=label, marker="o", markersize=4)
                ax.fill_between(x, values, alpha=0.1, color=color)

            if len(x_labels) == len(list(range(len(y_series_raw[0].split(","))))):
                ax.set_xticks(range(len(x_labels)))
                ax.set_xticklabels(x_labels, rotation=45, ha="right", fontsize=8)

            ax.set_ylabel(y_label, fontsize=10)
            ax.set_title(title, fontsize=13, fontweight="bold", pad=15)
            if len(y_series_raw) > 1:
                ax.legend(facecolor=CARD_BG, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR)
            fig.tight_layout()
            return _fig_to_base64(fig)

        img = await asyncio.to_thread(_generate)
        return {"image_base64": img, "chart_type": "line", "title": kwargs.get("title", "Chart")}


class BarChartTool(BaseTool):
    """Generate professional bar charts."""

    name = "bar_chart"
    description = "Generate a bar chart from data."
    category = "visualization"
    parameters = [
        ToolParameter(name="title", type="string", description="Chart title"),
        ToolParameter(name="labels", type="string", description="Comma-separated category labels"),
        ToolParameter(name="values", type="string", description="Comma-separated values"),
        ToolParameter(name="y_label", type="string", description="Y-axis label", required=False, default="Value"),
    ]

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        def _generate() -> str:
            title = kwargs.get("title", "Chart")
            labels = [label.strip() for label in kwargs.get("labels", "").split(",")]
            values = [float(v.strip()) for v in kwargs.get("values", "").split(",") if v.strip()]

            fig, ax = plt.subplots(figsize=(10, 5))
            _apply_style(fig, ax)

            colors = [ACCENT_COLORS[i % len(ACCENT_COLORS)] for i in range(len(values))]
            bars = ax.bar(range(len(values)), values, color=colors, alpha=0.85, edgecolor="none")
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
            ax.set_ylabel(kwargs.get("y_label", "Value"), fontsize=10)
            ax.set_title(title, fontsize=13, fontweight="bold", pad=15)

            for bar, val in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02,
                        f"{val:,.1f}", ha="center", va="bottom", color=TEXT_COLOR, fontsize=8)
            fig.tight_layout()
            return _fig_to_base64(fig)

        img = await asyncio.to_thread(_generate)
        return {"image_base64": img, "chart_type": "bar", "title": kwargs.get("title", "Chart")}


class PieChartTool(BaseTool):
    """Generate professional pie charts for allocation/breakdown views."""

    name = "pie_chart"
    description = "Generate a pie chart for portfolio allocation or data breakdown."
    category = "visualization"
    parameters = [
        ToolParameter(name="title", type="string", description="Chart title"),
        ToolParameter(name="labels", type="string", description="Comma-separated labels"),
        ToolParameter(name="values", type="string", description="Comma-separated values"),
    ]

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        def _generate() -> str:
            title = kwargs.get("title", "Chart")
            labels = [label.strip() for label in kwargs.get("labels", "").split(",")]
            values = [float(v.strip()) for v in kwargs.get("values", "").split(",") if v.strip()]

            fig, ax = plt.subplots(figsize=(8, 8))
            fig.patch.set_facecolor(DARK_BG)
            colors = ACCENT_COLORS[:len(values)]

            wedges, texts, autotexts = ax.pie(
                values, labels=labels, colors=colors, autopct="%1.1f%%",
                startangle=90, pctdistance=0.8,
                wedgeprops=dict(width=0.5, edgecolor=DARK_BG, linewidth=2),
            )
            for t in texts:
                t.set_color(TEXT_COLOR)
                t.set_fontsize(10)
            for t in autotexts:
                t.set_color(TEXT_COLOR)
                t.set_fontsize(9)
                t.set_fontweight("bold")

            ax.set_title(title, fontsize=13, fontweight="bold", color=TEXT_COLOR, pad=20)
            fig.tight_layout()
            return _fig_to_base64(fig)

        img = await asyncio.to_thread(_generate)
        return {"image_base64": img, "chart_type": "pie", "title": kwargs.get("title", "Chart")}


class PerformanceChartTool(BaseTool):
    """Generate stock performance chart from historical data."""

    name = "performance_chart"
    description = "Generate a stock price performance chart from historical data dict."
    category = "visualization"
    parameters = [
        ToolParameter(name="ticker", type="string", description="Stock ticker for title"),
        ToolParameter(name="history", type="string", description="JSON-encoded history list with date/close fields"),
    ]

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        import json
        ticker = kwargs.get("ticker", "")
        history_raw = kwargs.get("history", "[]")
        history = json.loads(history_raw) if isinstance(history_raw, str) else history_raw

        def _generate() -> str:
            if not history:
                fig, ax = plt.subplots(figsize=(10, 5))
                _apply_style(fig, ax)
                ax.text(0.5, 0.5, "No data available", transform=ax.transAxes, ha="center", color=TEXT_COLOR)
                return _fig_to_base64(fig)

            dates = [h["date"] for h in history]
            closes = [h["close"] for h in history]

            fig, ax = plt.subplots(figsize=(10, 5))
            _apply_style(fig, ax)

            color = ACCENT_COLORS[0]
            ax.plot(range(len(closes)), closes, color=color, linewidth=2)
            ax.fill_between(range(len(closes)), closes, alpha=0.15, color=color)

            # Show subset of labels
            step = max(1, len(dates) // 8)
            ax.set_xticks(range(0, len(dates), step))
            ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)], rotation=45, ha="right", fontsize=8)

            ax.set_ylabel("Price ($)", fontsize=10)
            ax.set_title(f"{ticker} Price Performance", fontsize=13, fontweight="bold", pad=15)

            change = ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] else 0
            change_color = "#3fb950" if change >= 0 else "#f85149"
            ax.text(0.02, 0.95, f"{change:+.2f}%", transform=ax.transAxes, fontsize=14,
                    fontweight="bold", color=change_color, va="top")
            fig.tight_layout()
            return _fig_to_base64(fig)

        img = await asyncio.to_thread(_generate)
        return {"image_base64": img, "chart_type": "line", "title": f"{ticker} Performance"}

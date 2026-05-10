"""
Valura AI — Streamlit UI Components.

Reusable components for chat messages, charts, agent badges, etc.
"""

from __future__ import annotations

import base64
import json
from typing import Any

import streamlit as st


def render_chart(chart_data: dict) -> None:
    """Render a base64-encoded chart image."""
    try:
        if isinstance(chart_data, str):
            chart_data = json.loads(chart_data)

        title = chart_data.get("title", "Chart")
        img_b64 = chart_data.get("image_base64", "")

        if img_b64:
            img_bytes = base64.b64decode(img_b64)
            st.image(img_bytes, caption=title, use_container_width=True)
    except Exception as e:
        st.warning(f"Failed to render chart: {e}")


def render_sources(sources_text: str) -> None:
    """Render source citations."""
    sources = [s.strip() for s in sources_text.split("\n") if s.strip()]
    if sources:
        with st.expander("📚 Sources & References", expanded=False):
            for i, source in enumerate(sources, 1):
                if source.startswith("http"):
                    st.markdown(f"{i}. [{source}]({source})")
                else:
                    st.markdown(f"{i}. {source}")


def render_agent_badges(agents: list[str]) -> None:
    """Render agent activity badges."""
    from src.frontend.styles import AGENT_BADGES
    badges_html = " ".join(AGENT_BADGES.get(a, f"🤖 {a}") for a in agents)
    if badges_html:
        st.markdown(badges_html, unsafe_allow_html=True)


def render_sidebar() -> dict[str, Any]:
    """Render the sidebar and return user settings."""
    with st.sidebar:
        st.markdown("## ⚙️ Settings")

        # Risk Profile
        risk = st.selectbox(
            "Risk Profile",
            options=["conservative", "moderate", "aggressive"],
            index=1,
            help="Adjusts investment recommendations to your comfort level",
        )

        st.markdown("---")

        # Session Management
        st.markdown("## 💬 Session")
        if st.button("🗑️ New Session", use_container_width=True):
            st.session_state.messages = []
            st.session_state.session_id = ""
            st.rerun()

        st.markdown("---")

        # Portfolio Upload
        st.markdown("## 📁 Portfolio")
        uploaded = st.file_uploader(
            "Upload CSV",
            type=["csv"],
            help="Columns: ticker, shares, avg_cost, asset_type",
        )

        portfolio = None
        if uploaded:
            import csv
            import io
            text = uploaded.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(text))
            portfolio = []
            for row in reader:
                portfolio.append({
                    "ticker": row.get("ticker", row.get("symbol", "")).upper(),
                    "shares": float(row.get("shares", row.get("quantity", 0))),
                    "avg_cost": float(row.get("avg_cost", row.get("cost", row.get("price", 0)))),
                    "asset_type": row.get("asset_type", "stock"),
                })
            st.success(f"✅ Loaded {len(portfolio)} holdings")

            with st.expander("View Portfolio"):
                for item in portfolio:
                    st.text(f"  {item['ticker']}: {item['shares']} shares @ ${item['avg_cost']:.2f}")

        st.markdown("---")

        # Quick Queries
        st.markdown("## 🚀 Quick Start")
        quick_queries = [
            "Analyze Apple stock",
            "Build a beginner portfolio",
            "Compare MSFT vs GOOGL",
            "Calculate SIP for $500/month at 12% for 10 years",
            "Analyze my portfolio and suggest improvements",
        ]
        selected_query = None
        for q in quick_queries:
            if st.button(q, use_container_width=True, key=f"quick_{q[:20]}"):
                selected_query = q

        st.markdown("---")
        st.markdown(
            '<div class="footer-text">Financial AI v1.0 · Multi-Agent Financial Intelligence</div>',
            unsafe_allow_html=True,
        )

    return {
        "risk_profile": risk,
        "portfolio": portfolio,
        "selected_query": selected_query,
    }

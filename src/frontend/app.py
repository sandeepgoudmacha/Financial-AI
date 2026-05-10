"""
Valura AI — Streamlit Frontend App.

Production-grade chat interface with SSE streaming,
charts, agent activity indicators, and portfolio upload.
"""

from __future__ import annotations

import json
import uuid

import httpx
import streamlit as st

# ── Page Configuration ────────────────────────────────────────
st.set_page_config(
    page_title="Financial AI — Intelligence",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports (after page config) ───────────────────────────────
from src.frontend.styles import CUSTOM_CSS, render_header, render_thinking  # noqa: E402
from src.frontend.components import (  # noqa: E402
    render_chart, render_sources, render_agent_badges, render_sidebar,
)

# ── Apply custom CSS ─────────────────────────────────────────
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Backend URL ──────────────────────────────────────────────
import os  # noqa: E402
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_URL = f"{BACKEND_URL}/api/v1"

# ── Session State Initialization ─────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "processing" not in st.session_state:
    st.session_state.processing = False

# ── Header ───────────────────────────────────────────────────
st.markdown(render_header(), unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────
sidebar_settings = render_sidebar()

# ── Handle Quick Query Selection ─────────────────────────────
if sidebar_settings.get("selected_query") and not st.session_state.processing:
    st.session_state.pending_query = sidebar_settings["selected_query"]

# ── Display Chat History ─────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="💎" if msg["role"] == "assistant" else "👤"):
        if msg.get("agents"):
            render_agent_badges(msg["agents"])
        st.markdown(msg["content"])
        # Render charts if present
        for chart in msg.get("charts", []):
            render_chart(chart)
        # Render sources if present
        if msg.get("sources"):
            render_sources(msg["sources"])


def process_query(query: str) -> None:
    """Process a user query and stream the response."""
    st.session_state.processing = True

    # Add user message
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user", avatar="👤"):
        st.markdown(query)

    # Prepare request
    payload = {
        "message": query,
        "session_id": st.session_state.session_id,
        "risk_profile": sidebar_settings.get("risk_profile", "moderate"),
    }
    if sidebar_settings.get("portfolio"):
        payload["portfolio"] = sidebar_settings["portfolio"]

    # Stream response
    with st.chat_message("assistant", avatar="💎"):
        status_container = st.empty()
        content_container = st.empty()
        charts_container = st.container()
        sources_container = st.empty()

        full_content = ""
        charts_data = []
        sources_text = ""
        agents_used = []

        try:
            with httpx.Client(timeout=180) as client:
                with client.stream(
                    "POST",
                    f"{API_URL}/chat",
                    json=payload,
                    headers={"Accept": "text/event-stream"},
                ) as response:
                    if response.status_code != 200:
                        error_text = response.read().decode()
                        try:
                            error_json = json.loads(error_text)
                            full_content = f"⚠️ {error_json.get('message', 'Request failed')}"
                        except Exception:
                            full_content = f"⚠️ Server error (status {response.status_code})"
                        content_container.markdown(full_content)
                    else:
                        current_event = ""
                        current_data = ""

                        for line in response.iter_lines():
                            if not line:
                                # Process accumulated event
                                if current_event and current_data:
                                    _process_sse_event(
                                        current_event, current_data,
                                        status_container, content_container,
                                        charts_container, sources_container,
                                        locals(),
                                    )
                                current_event = ""
                                current_data = ""
                                continue

                            if line.startswith("event:"):
                                current_event = line[6:].strip()
                            elif line.startswith("data:"):
                                current_data = line[5:].strip()

                                # Process event immediately
                                try:
                                    data = json.loads(current_data)
                                    event_content = data.get("content", "")
                                    agent = data.get("agent", "")
                                    metadata = data.get("metadata", {})

                                    if current_event == "thinking":
                                        status_container.markdown(
                                            render_thinking(event_content),
                                            unsafe_allow_html=True,
                                        )
                                        if metadata.get("session_id"):
                                            st.session_state.session_id = metadata["session_id"]

                                    elif current_event == "agent_activity":
                                        status_container.markdown(
                                            render_thinking(f"🤖 {event_content}"),
                                            unsafe_allow_html=True,
                                        )

                                    elif current_event == "content":
                                        status_container.empty()
                                        full_content = event_content
                                        content_container.markdown(full_content)

                                    elif current_event == "chart":
                                        chart_data = json.loads(event_content) if isinstance(event_content, str) else event_content
                                        charts_data.append(chart_data)
                                        with charts_container:
                                            render_chart(chart_data)

                                    elif current_event == "sources":
                                        sources_text = event_content

                                    elif current_event == "done":
                                        status_container.empty()
                                        agents_used = metadata.get("agents_used", [])

                                    elif current_event == "error":
                                        full_content = f"⚠️ {event_content}"
                                        content_container.markdown(full_content)

                                except json.JSONDecodeError:
                                    pass

        except httpx.ConnectError:
            full_content = (
                "⚠️ **Cannot connect to Valura AI backend.**\n\n"
                f"Make sure the backend is running at `{BACKEND_URL}`\n\n"
                "```bash\n"
                "# Start the backend\n"
                "uvicorn src.main:app --reload --port 8000\n"
                "```"
            )
            content_container.markdown(full_content)
        except Exception as e:
            full_content = f"⚠️ Error: {str(e)}"
            content_container.markdown(full_content)

        # Render sources
        if sources_text:
            with sources_container:
                render_sources(sources_text)

        # Render agent badges
        if agents_used:
            render_agent_badges(agents_used)

    # Save to message history
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_content,
        "charts": charts_data,
        "sources": sources_text,
        "agents": agents_used,
    })

    st.session_state.processing = False


def _process_sse_event(event, data, status, content, charts, sources, ctx):
    """Process a single SSE event (helper for readability)."""
    pass  # Processing is done inline above


# ── Chat Input ───────────────────────────────────────────────
# Handle pending query from sidebar
if hasattr(st.session_state, "pending_query") and st.session_state.pending_query:
    query = st.session_state.pending_query
    st.session_state.pending_query = None
    process_query(query)

# Main chat input
if prompt := st.chat_input("Ask about stocks, portfolios, or financial calculations...", key="main_chat"):
    process_query(prompt)

"""
Valura AI — Streamlit Frontend Styles.

Premium dark-themed CSS for production-grade look.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global ─────────────────────────────────────────────── */
.stApp {
    font-family: 'Inter', sans-serif;
}

/* ── Sidebar ────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
    border-right: 1px solid #21262d;
}

section[data-testid="stSidebar"] .stMarkdown {
    color: #e6edf3;
}

/* ── Chat Messages ──────────────────────────────────────── */
.stChatMessage {
    border-radius: 12px;
    margin: 8px 0;
    padding: 4px;
}

/* ── Agent Badge ────────────────────────────────────────── */
.agent-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 2px 4px 2px 0;
    color: white;
}

.agent-badge.market-research {
    background: linear-gradient(135deg, #1f6feb, #58a6ff);
}

.agent-badge.investment-strategy {
    background: linear-gradient(135deg, #238636, #3fb950);
}

.agent-badge.financial-calculator {
    background: linear-gradient(135deg, #9e6a03, #d29922);
}

/* ── Status Indicator ───────────────────────────────────── */
.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 1.5s infinite;
}

.status-dot.active { background: #3fb950; }
.status-dot.thinking { background: #58a6ff; }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* ── Card ───────────────────────────────────────────────── */
.metric-card {
    background: linear-gradient(135deg, #161b22, #1c2333);
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0;
}

.metric-card h3 {
    font-size: 0.85rem;
    color: #8b949e;
    margin: 0 0 4px 0;
    font-weight: 500;
}

.metric-card .value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #e6edf3;
}

/* ── Thinking animation ─────────────────────────────────── */
.thinking-container {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 8px;
    background: rgba(88, 166, 255, 0.08);
    border: 1px solid rgba(88, 166, 255, 0.2);
    margin: 4px 0;
}

.thinking-dots {
    display: flex;
    gap: 4px;
}

.thinking-dots span {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #58a6ff;
    animation: bounce 1.4s infinite ease-in-out both;
}

.thinking-dots span:nth-child(1) { animation-delay: -0.32s; }
.thinking-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
}

/* ── Header ─────────────────────────────────────────────── */
.valura-header {
    text-align: center;
    padding: 20px 0 10px;
}

.valura-header h1 {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #58a6ff, #3fb950, #d2a8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 4px;
}

.valura-header p {
    color: #8b949e;
    font-size: 0.9rem;
    margin-top: 0;
}

/* ── Footer ─────────────────────────────────────────────── */
.footer-text {
    text-align: center;
    color: #484f58;
    font-size: 0.75rem;
    padding: 20px 0;
    border-top: 1px solid #21262d;
    margin-top: 40px;
}
</style>
"""

AGENT_BADGES = {
    "market_research": '<span class="agent-badge market-research">📈 Market Research</span>',
    "investment_strategy": '<span class="agent-badge investment-strategy">🎯 Strategy</span>',
    "financial_calculator": '<span class="agent-badge financial-calculator">🧮 Calculator</span>',
}


def render_thinking(message: str) -> str:
    """Render a thinking/activity indicator."""
    return f"""
    <div class="thinking-container">
        <div class="thinking-dots"><span></span><span></span><span></span></div>
        <span style="color: #8b949e; font-size: 0.85rem;">{message}</span>
    </div>
    """


def render_header() -> str:
    """Render the app header."""
    return """
    <div class="valura-header">
        <h1>💎 Financial AI</h1>
        <p>Multi-Agent Financial Intelligence Platform</p>
    </div>
    """

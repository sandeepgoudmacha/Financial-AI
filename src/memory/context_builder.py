"""
Valura AI — Context Builder.

Builds LLM-ready context from session history.
Handles follow-up resolution, entity extraction, and context windowing.
"""

from __future__ import annotations

import re
from typing import Optional

from src.models.schemas import SessionContext, SessionMessage, RiskProfile, PortfolioItem
from src.memory.session_manager import SessionManager
from src.core.logging import get_logger

logger = get_logger("memory.context")

# Common ticker patterns
TICKER_PATTERN = re.compile(r'\b([A-Z]{1,5})\b')
KNOWN_TICKERS = {
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "TSLA", "NVDA", "META",
    "NFLX", "AMD", "INTC", "CRM", "ORCL", "ADBE", "PYPL", "SQ",
    "DIS", "BA", "JPM", "GS", "MS", "V", "MA", "WMT", "TGT",
    "KO", "PEP", "JNJ", "PFE", "MRNA", "UNH", "XOM", "CVX",
    "SPY", "QQQ", "VTI", "VOO", "IWM", "DIA", "ARKK",
}

# Common company name → ticker mappings
COMPANY_ALIASES = {
    "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL", "alphabet": "GOOGL",
    "amazon": "AMZN", "tesla": "TSLA", "nvidia": "NVDA", "meta": "META",
    "facebook": "META", "netflix": "NFLX", "amd": "AMD", "intel": "INTC",
    "disney": "DIS", "boeing": "BA", "jpmorgan": "JPM", "goldman": "GS",
    "walmart": "WMT", "coca-cola": "KO", "coca cola": "KO", "pepsi": "PEP",
    "berkshire": "BRK-B", "visa": "V", "mastercard": "MA",
}


class ContextBuilder:
    """
    Build LLM context from session history.

    Handles:
    - Windowed message history
    - Entity extraction (tickers, companies)
    - Follow-up query resolution
    - Context summarization
    """

    def __init__(self, session_manager: SessionManager) -> None:
        self._session_mgr = session_manager

    async def build_context(
        self,
        session_id: str,
        current_message: str,
        risk_profile: RiskProfile = RiskProfile.MODERATE,
        portfolio: Optional[list[PortfolioItem]] = None,
    ) -> SessionContext:
        """
        Build a complete context for the LLM from session history.

        Args:
            session_id: Current session ID.
            current_message: The user's current message.
            risk_profile: User's risk profile.
            portfolio: User's portfolio if provided.

        Returns:
            SessionContext with messages, mentioned tickers, etc.
        """
        messages = await self._session_mgr.get_messages(session_id)
        mentioned_tickers = self._extract_all_tickers(messages, current_message)

        return SessionContext(
            session_id=session_id,
            messages=messages,
            mentioned_tickers=mentioned_tickers,
            user_risk_profile=risk_profile,
            portfolio=portfolio,
        )

    def _extract_all_tickers(
        self, messages: list[SessionMessage], current_message: str,
    ) -> list[str]:
        """Extract all mentioned tickers from conversation history."""
        tickers: set[str] = set()

        # Extract from all messages
        all_text = " ".join(m.content for m in messages) + " " + current_message
        text_lower = all_text.lower()

        # Check company aliases
        for alias, ticker in COMPANY_ALIASES.items():
            if alias in text_lower:
                tickers.add(ticker)

        # Check for known ticker symbols
        for match in TICKER_PATTERN.finditer(all_text):
            candidate = match.group(1)
            if candidate in KNOWN_TICKERS:
                tickers.add(candidate)

        return sorted(tickers)

    def format_context_for_llm(self, context: SessionContext) -> list[dict[str, str]]:
        """
        Format session context into LLM-ready messages.

        Includes conversation history and relevant metadata.
        """
        formatted: list[dict[str, str]] = []

        # Add context preamble if there's history
        if context.messages or context.mentioned_tickers:
            context_parts = []
            if context.mentioned_tickers:
                context_parts.append(f"Previously discussed tickers: {', '.join(context.mentioned_tickers)}")
            if context.user_risk_profile:
                context_parts.append(f"User risk profile: {context.user_risk_profile.value}")
            if context.portfolio:
                holdings = ", ".join(f"{p.ticker}({p.shares} shares)" for p in context.portfolio)
                context_parts.append(f"User portfolio: {holdings}")

            if context_parts:
                formatted.append({
                    "role": "system",
                    "content": "Conversation context:\n" + "\n".join(context_parts),
                })

        # Add recent messages (already windowed by session manager)
        for msg in context.messages:
            formatted.append({"role": msg.role, "content": msg.content})

        return formatted

    def resolve_followup(self, current_message: str, context: SessionContext) -> str:
        """
        Resolve follow-up queries using conversation context.

        E.g., "What about Nvidia?" → adds context from prior discussion.
        """
        followup_indicators = [
            "what about", "how about", "and", "also", "compare with",
            "versus", "vs", "same for", "do the same", "what if",
        ]

        msg_lower = current_message.lower().strip()
        is_followup = any(msg_lower.startswith(ind) for ind in followup_indicators)

        if is_followup and context.mentioned_tickers:
            return f"{current_message} (Context: previously discussed {', '.join(context.mentioned_tickers)})"

        return current_message

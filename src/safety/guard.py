"""
Valura AI — Safety Guard System.

Pattern-based + optional LLM safety checks for financial content.
Blocks: insider trading, guaranteed returns, market manipulation,
money laundering, reckless leverage, pump-and-dump.
Allows: educational discussions ABOUT these topics.
"""

from __future__ import annotations

import re
from typing import Optional

from src.models.schemas import SafetyCheckResult
from src.core.logging import get_logger

logger = get_logger("safety")

# ── Dangerous patterns (block these) ─────────────────────────
BLOCKED_PATTERNS: list[tuple[str, str, str]] = [
    # (pattern, category, reason)
    # Insider trading — words can appear in any order
    (r"(?=.*\b(?:insider\s+trad(?:e|ing)|insider\s+tip))\b.*\b(?:how|profit|use|exploit|can\s+i|do\s+i)\b",
     "insider_trading", "Requests for insider trading advice are prohibited."),
    (r"\b(?:guarantee[ds]?\s+returns?|risk[\s-]*free\s+(?:profit|return|gain))\b",
     "guaranteed_returns", "No investment returns can be guaranteed. This claim is misleading."),
    (r"\b(?:pump\s+and\s+dump|pump[\s&]*dump)\b.*\b(?:how|scheme|strategy|do)\b",
     "market_manipulation", "Pump-and-dump schemes are illegal market manipulation."),
    # Money laundering — lookahead to match any order
    (r"(?=.*\b(?:money\s+launder(?:ing)?|wash\s+(?:money|funds|cash)|launder))(?=.*\b(?:how|method|way|can|through))",
     "money_laundering", "Money laundering is a serious criminal offense."),
    # Market manipulation — lookahead for any order
    (r"(?=.*\b(?:manipulat(?:e|ing))\b)(?=.*\b(?:stock|market|price)\b)(?=.*\b(?:how|can|way)\b)",
     "market_manipulation", "Market manipulation is illegal and harmful."),
    (r"\b(?:100x|1000x)\s+(?:leverage|margin)\b",
     "reckless_leverage", "Extremely high leverage is reckless and can lead to total loss."),
    (r"\b(?:front[\s-]*run(?:ning)?)\b.*\b(?:how|strategy|do)\b",
     "market_manipulation", "Front-running is illegal market manipulation."),
]

# ── Educational bypass patterns ──────────────────────────────
EDUCATIONAL_PATTERNS: list[str] = [
    r"\b(?:what\s+is|explain|define|meaning\s+of|learn\s+about|understand)\b",
    r"\b(?:educational|teach|example|history\s+of|case\s+study)\b",
    r"\b(?:regulation|law|legal|sec\s+rule|compliance|penalty|consequence)\b",
    r"\b(?:how\s+(?:does|do)\s+.*\s+work|overview)\b",
    r"\b(?:risk(?:s)?\s+of|danger(?:s)?\s+of|why\s+.*\s+(?:bad|illegal|wrong))\b",
]


class SafetyGuard:
    """
    Financial content safety system.

    Two-stage pipeline:
    1. Fast pattern matching (local, no API calls)
    2. Optional LLM-based review for borderline cases

    Educational content is explicitly allowed.
    """

    def __init__(self, llm_service: Optional[object] = None) -> None:
        self._llm = llm_service
        self._patterns = [(re.compile(p, re.IGNORECASE), cat, reason)
                          for p, cat, reason in BLOCKED_PATTERNS]
        self._educational = [re.compile(p, re.IGNORECASE) for p in EDUCATIONAL_PATTERNS]

    def check(self, message: str) -> SafetyCheckResult:
        """
        Check if a message is safe for processing.

        Returns SafetyCheckResult with is_safe=True if content is allowed.
        """
        if not message or not message.strip():
            return SafetyCheckResult(is_safe=True)

        text = message.strip().lower()

        # Check if this is an educational query (bypass)
        is_educational = any(pattern.search(text) for pattern in self._educational)

        # Check against blocked patterns
        for pattern, category, reason in self._patterns:
            if pattern.search(text):
                if is_educational:
                    logger.info(f"Educational bypass for category: {category}")
                    return SafetyCheckResult(is_safe=True)

                logger.warning(f"Safety BLOCKED | category={category} | msg={text[:80]}...")
                return SafetyCheckResult(
                    is_safe=False,
                    blocked_reason=reason,
                    category=category,
                    confidence=0.95,
                )

        return SafetyCheckResult(is_safe=True, confidence=1.0)

    async def check_with_llm(self, message: str) -> SafetyCheckResult:
        """
        Enhanced check using LLM for borderline cases.

        Falls back to pattern-based check if LLM is unavailable.
        """
        # Always do pattern check first (fast path)
        result = self.check(message)
        if not result.is_safe:
            return result

        # Optional LLM review for ambiguous content
        if self._llm and hasattr(self._llm, 'generate'):
            try:
                from src.services.llm_service import LLMService
                if isinstance(self._llm, LLMService):
                    response = await self._llm.generate(
                        messages=[
                            {"role": "system", "content": (
                                "You are a financial content safety classifier. "
                                "Analyze the user's message and determine if it requests: "
                                "insider trading advice, guaranteed returns promises, "
                                "market manipulation tactics, money laundering methods, "
                                "or reckless leverage strategies. "
                                "Educational questions ABOUT these topics are SAFE. "
                                "Respond with ONLY 'SAFE' or 'UNSAFE: <reason>'."
                            )},
                            {"role": "user", "content": message},
                        ],
                        model=None,  # Use fast model
                        max_tokens=50,
                    )
                    if response.strip().upper().startswith("UNSAFE"):
                        reason = response.split(":", 1)[-1].strip() if ":" in response else "Content flagged by AI safety review"
                        return SafetyCheckResult(
                            is_safe=False, blocked_reason=reason,
                            category="llm_review", confidence=0.8,
                        )
            except Exception as e:
                logger.warning(f"LLM safety review failed (continuing with pattern result): {e}")

        return result

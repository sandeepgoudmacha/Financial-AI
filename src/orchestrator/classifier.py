"""
Valura AI — Intent Classifier.

LLM-based intent classification to determine which agents to activate
and whether they should run in parallel.
"""

from __future__ import annotations

from src.core.logging import get_logger
from src.models.schemas import AgentType, IntentClassification
from src.services.llm_service import LLMService
from src.prompts.system_prompts import CLASSIFIER_SYSTEM_PROMPT

logger = get_logger("orchestrator.classifier")


class IntentClassifier:
    """
    Classify user intent and route to appropriate agents.

    Uses Groq LLM to determine:
    - Which agents to activate
    - Whether to run them in parallel
    - What entities are mentioned
    """

    def __init__(self, llm_service: LLMService) -> None:
        self._llm = llm_service

    async def classify(self, query: str, context_tickers: list[str] | None = None) -> IntentClassification:
        """
        Classify user intent and return routing decision.
        """
        try:
            context_info = ""
            if context_tickers:
                context_info = f"\nPreviously discussed tickers: {', '.join(context_tickers)}"

            messages = [
                {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"User query: {query}{context_info}\n\n"
                    f"Identify the required specialist agents. "
                    f"Respond with a JSON object where 'agents' is a list of enum STRINGS.\n"
                    f"Example: {{\"agents\": [\"market_research\"], \"parallel\": false, \"entities\": {{}}, \"reasoning\": \"...\", \"query_reformulation\": \"...\"}}"
                )},
            ]

            from src.core.config import get_settings
            result = await self._llm.generate_structured(
                messages=messages,
                response_model=IntentClassification,
                model=get_settings().groq_model, # Use primary model for reliability
                temperature=0.1,
            )

            logger.info(
                f"Classified intent: agents={[a.value for a in result.agents]}, "
                f"parallel={result.parallel}"
            )
            return result

        except Exception as e:
            logger.warning(f"Classification failed, using fallback: {e}")
            return self._fallback_classify(query)

    def _fallback_classify(self, query: str) -> IntentClassification:
        """Rule-based fallback classification when LLM fails."""
        q = query.lower()
        agents: list[AgentType] = []

        # Calculator keywords
        calc_kw = ["calculate", "cagr", "sip", "compound", "interest", "retirement",
                    "sharpe", "volatility", "projection", "roi", "return on"]
        if any(kw in q for kw in calc_kw):
            agents.append(AgentType.FINANCIAL_CALCULATOR)

        # Strategy keywords
        strat_kw = ["portfolio", "allocat", "diversif", "strategy", "invest in",
                     "recommend", "beginner", "rebalance", "etf", "risk profile"]
        if any(kw in q for kw in strat_kw):
            agents.append(AgentType.INVESTMENT_STRATEGY)

        # Research keywords (broad — default fallback)
        research_kw = ["analyze", "analysis", "stock", "company", "sector", "market",
                       "earnings", "news", "compare", "valuation", "price", "buy", "sell"]
        if any(kw in q for kw in research_kw) or not agents:
            agents.append(AgentType.MARKET_RESEARCH)

        # Parallel if multiple agents
        parallel = len(agents) > 1

        # Multi-agent queries
        if "portfolio" in q and ("analyze" in q or "review" in q or "improve" in q):
            agents = [AgentType.MARKET_RESEARCH, AgentType.INVESTMENT_STRATEGY, AgentType.FINANCIAL_CALCULATOR]
            parallel = True

        return IntentClassification(
            agents=agents,
            parallel=parallel,
            reasoning="Fallback rule-based classification",
        )

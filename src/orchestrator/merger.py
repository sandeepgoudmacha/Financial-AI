"""
Valura AI — Response Merger.

Intelligently merges outputs from multiple agents into
one cohesive, professional response.
"""

from __future__ import annotations

import json

from src.core.logging import get_logger
from src.models.schemas import AgentResult
from src.services.llm_service import LLMService
from src.prompts.system_prompts import MERGER_SYSTEM_PROMPT

logger = get_logger("orchestrator.merger")


class ResponseMerger:
    """
    Merge multi-agent outputs into unified responses.

    Uses LLM to create cohesive narratives from separate
    agent analyses, eliminating redundancy while preserving
    all key insights.
    """

    def __init__(self, llm_service: LLMService) -> None:
        self._llm = llm_service

    async def merge(self, results: list[AgentResult], original_query: str) -> str:
        """
        Merge multiple agent results into a single response.

        Args:
            results: List of AgentResult from different agents.
            original_query: The user's original query.

        Returns:
            Unified markdown response.
        """
        if not results:
            return "No results to merge."

        if len(results) == 1:
            return results[0].content

        # Build agent outputs summary for the merger
        agent_outputs = []
        for r in results:
            agent_outputs.append({
                "agent": r.agent_name,
                "type": r.agent_type.value,
                "content": r.content[:3000],  # Truncate per agent to fit context
                "has_charts": len(r.charts) > 0,
                "execution_time_ms": r.execution_time_ms,
            })

        try:
            messages = [
                {"role": "system", "content": MERGER_SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Original User Query: {original_query}\n\n"
                    f"Agent Outputs to Merge:\n{json.dumps(agent_outputs, indent=2, default=str)}\n\n"
                    f"Create a unified, professional response that synthesizes all agent insights "
                    f"into a cohesive report. Include an Executive Summary at the top and "
                    f"Key Takeaways at the end."
                )},
            ]

            merged = await self._llm.generate(messages=messages)
            return merged

        except Exception as e:
            logger.error(f"LLM merge failed, using concatenation fallback: {e}")
            return self._fallback_merge(results)

    def _fallback_merge(self, results: list[AgentResult]) -> str:
        """Simple concatenation fallback when LLM merge fails."""
        sections = ["# 📊 Valura AI Analysis\n"]

        agent_titles = {
            "MarketResearchAgent": "## 📈 Market Research",
            "InvestmentStrategyAgent": "## 🎯 Investment Strategy",
            "FinancialCalculatorAgent": "## 🧮 Financial Calculations",
        }

        for r in results:
            title = agent_titles.get(r.agent_name, f"## {r.agent_name}")
            sections.append(f"\n{title}\n")
            sections.append(r.content)
            sections.append("\n---\n")

        return "\n".join(sections)

"""
Valura AI — Investment Strategy Agent (CrewAI).

Portfolio guidance, allocation strategies, risk profiling.
"""

from __future__ import annotations

from crewai import Agent, LLM


from src.core.config import get_settings
from src.prompts.system_prompts import INVESTMENT_STRATEGY_SYSTEM_PROMPT
from src.tools.crewai_tools import STRATEGY_TOOLS

def create_investment_strategy_agent(step_callback=None) -> Agent:
    """Create the Investment Strategy CrewAI Agent."""
    settings = get_settings()
    llm = LLM(
        model=f"groq/{settings.groq_model}",
        api_key=settings.groq_api_key.get_secret_value(),
        temperature=0.3,
    )

    return Agent(
        role="Chief Investment Strategist",
        goal="Provide thoughtful, personalized portfolio strategies and allocation guidance.",
        backstory=(
            "You are a Chief Investment Strategist with expertise in portfolio construction, "
            "asset allocation, and risk management. You help both novice and experienced "
            "investors build well-diversified portfolios aligned with their goals."
        ),
        tools=STRATEGY_TOOLS,
        llm=llm,
        verbose=True,
        allow_delegation=False,
        step_callback=step_callback,
        system_template=INVESTMENT_STRATEGY_SYSTEM_PROMPT,
    )

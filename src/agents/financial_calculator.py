"""
Valura AI — Financial Calculator Agent (CrewAI).

Performs financial calculations, generates charts, and explains
results step-by-step for novice investors.
"""

from __future__ import annotations

from crewai import Agent, LLM


from src.core.config import get_settings
from src.prompts.system_prompts import FINANCIAL_CALCULATOR_SYSTEM_PROMPT
from src.tools.crewai_tools import CALCULATOR_TOOLS

def create_financial_calculator_agent(step_callback=None) -> Agent:
    """Create the Financial Calculator CrewAI Agent."""
    settings = get_settings()
    llm = LLM(
        model=f"groq/{settings.groq_model}",
        api_key=settings.groq_api_key.get_secret_value(),
        temperature=0.1,
    )

    return Agent(
        role="Financial Calculator Specialist",
        goal="Perform precise financial calculations and explain them clearly.",
        backstory=(
            "You are a quantitative finance specialist who makes complex financial "
            "calculations accessible. You provide step-by-step breakdowns and visual "
            "charts to help investors understand projections and metrics."
        ),
        tools=CALCULATOR_TOOLS,
        llm=llm,
        verbose=True,
        allow_delegation=False,
        step_callback=step_callback,
        system_template=FINANCIAL_CALCULATOR_SYSTEM_PROMPT,
    )

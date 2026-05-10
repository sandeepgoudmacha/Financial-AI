"""
Valura AI — Market Research Agent (CrewAI).

Deep financial analysis with real-time data.
Generates Morgan Stanley / Bloomberg style reports.
"""

from __future__ import annotations

from crewai import Agent, LLM


from src.core.config import get_settings
from src.prompts.system_prompts import MARKET_RESEARCH_SYSTEM_PROMPT
from src.tools.crewai_tools import MARKET_TOOLS

def create_market_research_agent(step_callback=None) -> Agent:
    """Create the Market Research CrewAI Agent."""
    settings = get_settings()
    llm = LLM(
        model=f"groq/{settings.groq_model}",
        api_key=settings.groq_api_key.get_secret_value(),
        temperature=0.2,
    )

    return Agent(
        role="Senior Market Research Analyst",
        goal="Provide institutional-grade market research and stock analysis.",
        backstory=(
            "You are a senior equity research analyst with 15 years of experience at top-tier "
            "investment banks. You provide institutional-grade research with deep fundamental "
            "analysis, technical perspectives, and actionable insights. "
            "You write reports with clear sections: Overview, Key Metrics, Analysis, Outlook."
        ),
        tools=MARKET_TOOLS,
        llm=llm,
        verbose=True,
        allow_delegation=False,
        step_callback=step_callback,
        system_template=MARKET_RESEARCH_SYSTEM_PROMPT,
    )

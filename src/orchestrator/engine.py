"""
Valura AI — CrewAI Orchestration Engine.

Uses CrewAI for multi-agent orchestration with:
- Native crewai.Agent, Task, Crew
- Async execution
- Step callbacks pushed to asyncio.Queue for SSE streaming
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, AsyncGenerator, Optional

from crewai import Task, Crew

from src.agents.market_research import create_market_research_agent
from src.agents.investment_strategy import create_investment_strategy_agent
from src.agents.financial_calculator import create_financial_calculator_agent
from src.core.logging import get_logger
from src.models.schemas import (
    AgentType, SessionContext, StreamEventType, AgentResult,
)
from src.orchestrator.classifier import IntentClassifier
from src.orchestrator.merger import ResponseMerger
from src.services.llm_service import LLMService

logger = get_logger("orchestrator.engine")


class OrchestratorEngine:
    """
    CrewAI-powered multi-agent orchestration engine.

    Manages:
    - Intent classification -> agent routing
    - Crew assembly and Task definition
    - SSE streaming via step callbacks
    """

    def __init__(
        self,
        llm_service: LLMService,
        tool_registry: Any = None, # kept for backward compatibility in dependencies.py
    ) -> None:
        self._llm = llm_service
        self._classifier = IntentClassifier(llm_service)
        self._merger = ResponseMerger(llm_service)
        logger.info("CrewAI Orchestrator initialized")

    async def process(
        self,
        query: str,
        context: Optional[SessionContext] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        Process a user query through the CrewAI pipeline.
        Yields SSE-compatible event dicts progressively.
        """
        start = time.perf_counter()

        yield {
            "event": StreamEventType.THINKING,
            "data": "Analyzing your request...",
            "agent": "orchestrator",
        }

        # 1. Classify intent
        context_tickers = context.mentioned_tickers if context else None
        classification = await self._classifier.classify(query, context_tickers)

        agent_types = [a.value for a in classification.agents]
        yield {
            "event": StreamEventType.THINKING,
            "data": f"Activating Crew: {', '.join(agent_types)}",
            "agent": "orchestrator",
        }

        # 2. Setup streaming queue
        queue = asyncio.Queue()

        def step_callback(step_output):
            """Callback invoked by CrewAI agents after each tool execution/step."""
            import json
            
            # CrewAI step_output is an AgentStep object or a tuple of (AgentAction, result)
            msg = "Processing next step..."
            
            if hasattr(step_output, 'thought') and step_output.thought:
                # Show the core of the thought
                thought = step_output.thought.strip().split('\n')[0]
                msg = f"💭 {thought[:100]}..." if len(thought) > 100 else f"💭 {thought}"
            
            if hasattr(step_output, 'tool'):
                msg = f"🔍 Running tool: **{step_output.tool}**"
            elif isinstance(step_output, tuple) and len(step_output) == 2:
                action, result = step_output
                tool_name = getattr(action, 'tool', 'tool')
                msg = f"✅ Tool **{tool_name}** returned data"
                
                # Check if it returned a chart base64
                if isinstance(result, str) and '"image_base64":' in result:
                    try:
                        # Attempt to extract chart JSON if it is wrapped in string
                        # The tool returns stringified JSON
                        chart_data = json.loads(result.replace("'", '"'))
                        if chart_data.get("image_base64"):
                            queue.put_nowait({
                                "event": StreamEventType.CHART,
                                "agent": "orchestrator",
                                "metadata": chart_data,
                            })
                    except Exception:
                        pass
                
            queue.put_nowait({
                "event": StreamEventType.AGENT_ACTIVITY,
                "data": msg,
                "agent": "crewai_agent",
            })

        # 3. Instantiate Agents
        active_agents = []
        if AgentType.MARKET_RESEARCH in classification.agents:
            active_agents.append(create_market_research_agent(step_callback=step_callback))
        if AgentType.INVESTMENT_STRATEGY in classification.agents:
            active_agents.append(create_investment_strategy_agent(step_callback=step_callback))
        if AgentType.FINANCIAL_CALCULATOR in classification.agents:
            active_agents.append(create_financial_calculator_agent(step_callback=step_callback))
            
        # Fallback if none matched
        if not active_agents:
            active_agents.append(create_market_research_agent(step_callback=step_callback))

        # 4. Define and Execute Tasks in Parallel
        effective_query = classification.query_reformulation or query
        
        # Build context prompt
        context_str = ""
        if context:
            if context.mentioned_tickers:
                context_str += f"\nPrevious tickers: {', '.join(context.mentioned_tickers)}"
            if context.portfolio:
                context_str += f"\nUser Portfolio: {[p.model_dump() for p in context.portfolio]}"
            if context.user_risk_profile:
                context_str += f"\nRisk Profile: {context.user_risk_profile.value}"

        async def run_agent_task(agent, agent_type):
            """Run a single agent task in a thread."""
            task = Task(
                description=(
                    f"User Query: {effective_query}\n"
                    f"Context: {context_str}\n\n"
                    f"CRITICAL: You MUST use your available tools to gather current data (stock prices, news, etc.) "
                    f"before providing any analysis. Do not rely on your internal knowledge for current market metrics.\n"
                    f"Example Tool Usage:\n"
                    f"Action: sip_calculator\n"
                    f"Action Input: {{\"monthly_investment\": 500, \"annual_return\": 0.12, \"years\": 10}}\n\n"
                    f"As the {agent.role}, provide a detailed, data-driven report based on the tool outputs. "
                    f"If the tool returns data, you MUST include the final numbers in your report."
                ),
                expected_output="A detailed markdown report for your specific area of expertise.",
                agent=agent,
                max_iter=10, # Give it more attempts to get the tool usage right
            )
            crew = Crew(agents=[agent], tasks=[task], verbose=False)
            
            start_time = time.perf_counter()
            result = await asyncio.to_thread(crew.kickoff)
            duration = (time.perf_counter() - start_time) * 1000
            
            return AgentResult(
                agent_name=agent.role,
                agent_type=agent_type,
                content=str(result),
                charts=[], # Captured via step_callback
                execution_time_ms=round(duration, 0),
            )

        # Map agent types back to their active instances
        agent_tasks = []
        for agent in active_agents:
            # Infer agent type for the Result object
            a_type = AgentType.MARKET_RESEARCH
            if "Strategist" in agent.role: a_type = AgentType.INVESTMENT_STRATEGY
            if "Calculator" in agent.role: a_type = AgentType.FINANCIAL_CALCULATOR
            
            agent_tasks.append(run_agent_task(agent, a_type))

        # 5. Execute and stream queue events
        # Start all tasks in parallel
        pending_tasks = [asyncio.create_task(t) for t in agent_tasks]
        
        # Yield from queue until all tasks are done
        while any(not t.done() for t in pending_tasks):
            try:
                event = await asyncio.wait_for(queue.get(), timeout=0.1)
                yield event
            except asyncio.TimeoutError:
                continue

        # Collect results
        agent_results = []
        for t in pending_tasks:
            try:
                agent_results.append(await t)
            except Exception as e:
                logger.error(f"Agent task failed: {e}")

        # 6. Merge results
        yield {
            "event": StreamEventType.THINKING,
            "data": "Synthesizing multi-agent insights...",
            "agent": "orchestrator",
        }
        
        final_content = await self._merger.merge(agent_results, query)

        # Drain any remaining queue events
        while not queue.empty():
            yield queue.get_nowait()

        # Yield final content
        yield {
            "event": StreamEventType.CONTENT,
            "data": final_content,
            "agent": "orchestrator",
        }

        elapsed = (time.perf_counter() - start) * 1000
        yield {
            "event": StreamEventType.DONE,
            "data": "",
            "agent": "orchestrator",
            "metadata": {
                "agents_used": agent_types,
                "parallel": False, # Crew executes hierarchically/sequentially
                "total_time_ms": round(elapsed, 0),
            },
        }

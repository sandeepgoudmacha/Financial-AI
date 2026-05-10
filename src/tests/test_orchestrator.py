"""
Valura AI — Orchestrator Tests.

Tests intent classification and routing using mocked LLM.
"""

import pytest
from unittest.mock import AsyncMock
from src.orchestrator.classifier import IntentClassifier
from src.models.schemas import AgentType, IntentClassification


class TestIntentClassifier:
    """Test the fallback (rule-based) classifier — no API keys needed."""

    @pytest.fixture
    def classifier(self, mock_llm_service):
        return IntentClassifier(mock_llm_service)

    def test_fallback_stock_analysis(self, classifier):
        result = classifier._fallback_classify("Analyze Apple stock")
        assert AgentType.MARKET_RESEARCH in result.agents

    def test_fallback_portfolio_guidance(self, classifier):
        result = classifier._fallback_classify("Build me a diversified portfolio")
        assert AgentType.INVESTMENT_STRATEGY in result.agents

    def test_fallback_calculation(self, classifier):
        result = classifier._fallback_classify("Calculate CAGR for $10K to $25K over 5 years")
        assert AgentType.FINANCIAL_CALCULATOR in result.agents

    def test_fallback_compound_query(self, classifier):
        result = classifier._fallback_classify("Analyze my portfolio and suggest improvements")
        assert len(result.agents) == 3
        assert result.parallel is True

    def test_fallback_comparison(self, classifier):
        result = classifier._fallback_classify("Compare MSFT and GOOGL")
        assert AgentType.MARKET_RESEARCH in result.agents

    def test_fallback_etf_recommendation(self, classifier):
        result = classifier._fallback_classify("What ETFs should a beginner invest in?")
        assert AgentType.INVESTMENT_STRATEGY in result.agents

    def test_fallback_default_to_research(self, classifier):
        result = classifier._fallback_classify("Tell me about the current market conditions")
        assert AgentType.MARKET_RESEARCH in result.agents

    @pytest.mark.asyncio
    async def test_classify_with_mock_llm(self, mock_llm_service):
        """Test full classification with mocked LLM."""
        mock_result = IntentClassification(
            agents=[AgentType.MARKET_RESEARCH],
            parallel=False,
            entities={"tickers": ["AAPL"]},
            reasoning="Stock analysis requested",
        )
        mock_llm_service.generate_structured = AsyncMock(return_value=mock_result)
        classifier = IntentClassifier(mock_llm_service)

        result = await classifier.classify("Analyze Apple stock")
        assert AgentType.MARKET_RESEARCH in result.agents

    @pytest.mark.asyncio
    async def test_classify_fallback_on_error(self, mock_llm_service):
        """Test that classification falls back to rules on LLM failure."""
        mock_llm_service.generate_structured = AsyncMock(side_effect=Exception("API Error"))
        classifier = IntentClassifier(mock_llm_service)

        result = await classifier.classify("Calculate compound interest")
        assert AgentType.FINANCIAL_CALCULATOR in result.agents
        assert result.reasoning == "Fallback rule-based classification"

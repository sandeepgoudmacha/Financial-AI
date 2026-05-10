# Multi-Agent Financial Intelligence Platform

> **Production-grade AI-powered financial intelligence system** built with CrewAI orchestration, Groq LLM, FastAPI, and Streamlit.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.37+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036?style=flat)](https://groq.com)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                            │
│  Chat UI · Charts · Portfolio Upload · Agent Activity · SSE     │
└──────────────────────────┬──────────────────────────────────────┘
                           │ SSE (Server-Sent Events)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND                             │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────────┐  │
│  │  Safety   │→│  Memory   │→│ Classifier │→│ Orchestrator  │  │
│  │  Guard    │  │  Manager  │  │  (LLM)    │  │  (CrewAI)    │  │
│  └──────────┘  └──────────┘  └───────────┘  └──────┬───────┘  │
│                                                      │          │
│                          ┌───────────────────────────┼────┐     │
│                          │              │            │    │     │
│                          ▼              ▼            ▼    │     │
│                   ┌────────────┐ ┌────────────┐ ┌────────┴┐   │
│                   │  Market    │ │ Investment │ │Financial │   │
│                   │  Research  │ │ Strategy   │ │Calculator│   │
│                   │  Agent     │ │ Agent      │ │ Agent    │   │
│                   └─────┬──────┘ └─────┬──────┘ └────┬────┘   │
│                         │              │             │         │
│                   ┌─────▼──────────────▼─────────────▼────┐   │
│                   │         MCP Tool Registry              │   │
│                   │  yfinance · DuckDuckGo · Calculators  │   │
│                   │  Charts · Sector Analysis · News      │   │
│                   └───────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐                    │
│  │  SQLite   │  │  SSE     │  │  Response  │                    │
│  │  Memory   │  │ Streamer │  │  Merger    │                    │
│  └──────────┘  └──────────┘  └───────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Request Lifecycle

```
User Message
  → POST /api/v1/chat
  → Safety Guard (pattern matching + optional LLM review)
  → Session Memory (load conversation context)
  → Intent Classifier (LLM-based agent routing)
  → CrewAI Orchestrator (parallel/sequential dispatch)
  → Agent Execution (tools + LLM reasoning)
  → Response Merger (multi-agent synthesis)
  → SSE Stream (progressive delivery to frontend)
```

---

## Agent System

| Agent | Role | Capabilities |
|-------|------|-------------|
| **MarketResearchAgent** | Senior Equity Analyst | Stock analysis, sector analysis, news sentiment, competitor comparison, valuation insights, performance charts |
| **InvestmentStrategyAgent** | Chief Investment Strategist | Portfolio construction, allocation, diversification, risk profiling, ETF recommendations, rebalancing |
| **FinancialCalculatorAgent** | Quantitative Specialist | CAGR, SIP, compound interest, retirement projections, Sharpe ratio, portfolio volatility |

### Parallel Execution

When a query requires multiple agents (e.g., "Analyze my portfolio and suggest improvements"), all three agents execute **in parallel** via `asyncio.gather()` and results are merged into a single cohesive response.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Groq (LLaMA 3.3 70B Versatile) |
| **Orchestration** | CrewAI + Custom async engine |
| **Backend** | FastAPI + sse-starlette |
| **Frontend** | Streamlit |
| **Database** | SQLite (aiosqlite) |
| **Financial Data** | yfinance (live) |
| **Search** | DuckDuckGo |
| **Charts** | Matplotlib (dark theme) |
| **Validation** | Pydantic v2 |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### 1. Clone & Install

```bash
git clone <repo-url>
cd valura-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 3. Start Backend

```bash
uvicorn src.main:app --reload --port 8000
```

### 4. Start Frontend (new terminal)

```bash
streamlit run src/frontend/app.py
or
python -m streamlit run src/frontend/app.py

```

### 5. Open Browser

Navigate to `http://localhost:8501`

---

## 🐳 Docker Deployment

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your GROQ_API_KEY

# Build and run
docker-compose up --build

# Access:
# Frontend: http://localhost:8501
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

```bash
# With coverage
pytest src/tests/ --cov=src --cov-report=html
```

---

## 🛠 API Reference & Testing

You can test the backend endpoints directly using `curl` or the interactive Swagger docs at `http://localhost:8000/docs`.

### 1. Chat Endpoint (SSE Streaming)
The main chat endpoint uses Server-Sent Events to stream agent progress and the final response.

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Analyze Apple stock and calculate SIP for $500 over 5 years",
       "risk_profile": "moderate"
     }'
```

### 2. Health Check
Quickly verify if the server and its services are initialized.

```bash
curl -X GET "http://localhost:8000/api/v1/health"
```

### 3. System Metrics
Get real-time statistics on active sessions and performance.

```bash
curl -X GET "http://localhost:8000/api/v1/metrics"
```

### 4. Session History
Retrieve the conversation history for a specific session ID.

```bash
# Replace <session_id> with a real ID from a chat response
curl -X GET "http://localhost:8000/api/v1/sessions/<session_id>"
```

---

## Project Structure

```
valura-ai/
├── src/
│   ├── main.py                 # FastAPI app entry point
│   ├── core/
│   │   ├── config.py           # Pydantic Settings
│   │   ├── logging.py          # Structured logging
│   │   └── exceptions.py       # Exception hierarchy
│   ├── models/
│   │   └── schemas.py          # All Pydantic schemas
│   ├── services/
│   │   └── llm_service.py      # Groq LLM client
│   ├── tools/
│   │   ├── base.py             # Abstract tool base
│   │   ├── market_tools.py     # yfinance + DuckDuckGo
│   │   ├── calculator_tools.py # Financial calculators
│   │   └── visualization_tools.py  # Chart generation
│   ├── mcp/
│   │   ├── registry.py         # MCP tool registry
│   │   └── interfaces.py       # MCP abstract interfaces
│   ├── safety/
│   │   └── guard.py            # Content safety system
│   ├── memory/
│   │   ├── session_manager.py  # SQLite session storage
│   │   └── context_builder.py  # LLM context builder
│   ├── agents/
│   │   ├── base.py             # Abstract agent base
│   │   ├── market_research.py  # Market analysis agent
│   │   ├── investment_strategy.py  # Strategy agent
│   │   └── financial_calculator.py # Calculator agent
│   ├── orchestrator/
│   │   ├── classifier.py       # Intent classification
│   │   ├── engine.py           # CrewAI orchestration
│   │   └── merger.py           # Response merging
│   ├── api/
│   │   ├── router.py           # API endpoints
│   │   ├── dependencies.py     # Dependency injection
│   │   └── middleware.py       # CORS, timing, errors
│   ├── streaming/
│   │   └── sse.py              # SSE event formatting
│   ├── prompts/
│   │   └── system_prompts.py   # All LLM prompts
│   ├── frontend/
│   │   ├── app.py              # Streamlit application
│   │   ├── components.py       # UI components
│   │   └── styles.py           # CSS styling
│   └── tests/
│       ├── conftest.py         # Shared fixtures
│       ├── test_safety.py      # Safety tests
│       ├── test_tools.py       # Calculator tests
│       ├── test_memory.py      # Memory tests
│       ├── test_orchestrator.py # Routing tests
│       └── test_api.py         # API tests
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Groq over OpenAI** | Ultra-fast inference (~200ms), free tier, OpenAI-compatible SDK |
| **CrewAI + Custom Engine** | CrewAI provides agent abstractions; custom engine adds async parallel execution |
| **SQLite over Redis** | Zero infrastructure, portable, sufficient for single-instance deployments |
| **yfinance + DuckDuckGo** | No API keys required for core financial data and news |
| **Pattern-based Safety First** | Fast (sub-ms) safety checks; LLM review only for borderline cases |
| **SSE over WebSockets** | Simpler protocol, sufficient for server→client streaming |
| **Pydantic Everywhere** | Type safety at every boundary — API, LLM outputs, tool results |

---

## Future Improvements

- [ ] Full CrewAI Flows integration for complex multi-step workflows
- [ ] External MCP server connections (SEC filings, Bloomberg terminal)
- [ ] Redis caching layer for repeated queries
- [ ] Semantic memory with embeddings (ChromaDB/Pinecone)
- [ ] User authentication and multi-tenancy
- [ ] Real-time WebSocket price feeds
- [ ] AI-generated insights dashboard
- [ ] Watchlist management
- [ ] PDF report generation
- [ ] Voice input/output

---




"""
Valura AI — Session Memory Tests.

Tests session CRUD, message history, and context building.
"""

import pytest
from src.memory.session_manager import SessionManager
from src.memory.context_builder import ContextBuilder
from src.models.schemas import RiskProfile


class TestSessionManager:
    @pytest.fixture
    async def session_mgr(self, tmp_db):
        mgr = SessionManager(db_path=tmp_db)
        await mgr.initialize()
        return mgr

    @pytest.mark.asyncio
    async def test_create_session(self, session_mgr):
        sid = await session_mgr.create_session()
        assert sid  # Non-empty UUID

    @pytest.mark.asyncio
    async def test_create_session_with_id(self, session_mgr):
        sid = await session_mgr.create_session("test-session-123")
        assert sid == "test-session-123"

    @pytest.mark.asyncio
    async def test_add_and_get_messages(self, session_mgr):
        sid = await session_mgr.create_session("msg-test")
        await session_mgr.add_message(sid, "user", "Hello")
        await session_mgr.add_message(sid, "assistant", "Hi there!")

        messages = await session_mgr.get_messages(sid)
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[0].content == "Hello"
        assert messages[1].role == "assistant"
        assert messages[1].content == "Hi there!"

    @pytest.mark.asyncio
    async def test_message_ordering(self, session_mgr):
        sid = await session_mgr.create_session("order-test")
        for i in range(5):
            await session_mgr.add_message(sid, "user", f"Message {i}")

        messages = await session_mgr.get_messages(sid)
        assert len(messages) == 5
        for i, msg in enumerate(messages):
            assert msg.content == f"Message {i}"

    @pytest.mark.asyncio
    async def test_message_windowing(self, session_mgr):
        sid = await session_mgr.create_session("window-test")
        for i in range(30):
            await session_mgr.add_message(sid, "user", f"Message {i}")

        messages = await session_mgr.get_messages(sid, limit=5)
        assert len(messages) == 5
        # Should get the LATEST 5 messages
        assert messages[0].content == "Message 25"

    @pytest.mark.asyncio
    async def test_delete_session(self, session_mgr):
        sid = await session_mgr.create_session("delete-test")
        await session_mgr.add_message(sid, "user", "Test")
        await session_mgr.delete_session(sid)
        messages = await session_mgr.get_messages(sid)
        assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_session_count(self, session_mgr):
        await session_mgr.create_session("s1")
        await session_mgr.create_session("s2")
        count = await session_mgr.get_session_count()
        assert count == 2

    @pytest.mark.asyncio
    async def test_risk_profile(self, session_mgr):
        sid = await session_mgr.create_session("risk-test")
        await session_mgr.set_risk_profile(sid, RiskProfile.AGGRESSIVE)
        profile = await session_mgr.get_risk_profile(sid)
        assert profile == RiskProfile.AGGRESSIVE


class TestContextBuilder:
    def test_extract_tickers_from_aliases(self):
        mgr = SessionManager(db_path=":memory:")
        builder = ContextBuilder(mgr)
        tickers = builder._extract_all_tickers([], "Analyze Apple and Microsoft")
        assert "AAPL" in tickers
        assert "MSFT" in tickers

    def test_extract_tickers_from_symbols(self):
        mgr = SessionManager(db_path=":memory:")
        builder = ContextBuilder(mgr)
        tickers = builder._extract_all_tickers([], "What about NVDA and TSLA?")
        assert "NVDA" in tickers
        assert "TSLA" in tickers

    def test_resolve_followup(self):
        from src.models.schemas import SessionContext
        mgr = SessionManager(db_path=":memory:")
        builder = ContextBuilder(mgr)
        context = SessionContext(
            session_id="test",
            mentioned_tickers=["AAPL", "MSFT"],
        )
        resolved = builder.resolve_followup("what about Nvidia?", context)
        assert "AAPL" in resolved
        assert "MSFT" in resolved

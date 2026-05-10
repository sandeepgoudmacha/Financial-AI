"""
Valura AI — API Endpoint Tests.

Tests API endpoints with mocked services.
"""

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    def test_health(self):
        from src.main import app
        client = TestClient(app)
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"


class TestMetricsEndpoint:
    def test_metrics(self):
        from src.main import app
        client = TestClient(app)
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "uptime_seconds" in data


class TestPortfolioUpload:
    def test_upload_csv(self):
        from src.main import app
        client = TestClient(app)

        csv_content = "ticker,shares,avg_cost,asset_type\nAAPL,10,150.00,stock\nMSFT,5,300.00,stock\n"
        response = client.post(
            "/api/v1/portfolio/upload",
            files={"file": ("portfolio.csv", csv_content, "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["holdings"] == 2
        assert data["portfolio"][0]["ticker"] == "AAPL"


class TestSafetyBlocking:
    def test_safety_blocked_request(self):
        from src.main import app
        client = TestClient(app)
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "How can I profit from insider trading tips?",
                "session_id": "test-safety",
            },
        )
        assert response.status_code == 403
        data = response.json()
        assert data["error"] == "safety_blocked"

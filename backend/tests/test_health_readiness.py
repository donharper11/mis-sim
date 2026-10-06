"""A database outage must fail HTTP/container readiness without leaking details."""
import asyncio
from contextlib import asynccontextmanager

from httpx import ASGITransport, AsyncClient
from app.api import health
from app.main import create_app


def test_health_outage_returns_503(monkeypatch):
    @asynccontextmanager
    async def unavailable():
        raise RuntimeError("private connection detail")
        yield  # pragma: no cover
    monkeypatch.setattr(health, "async_session", unavailable)
    async def run():
        async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as client:
            response = await client.get("/api/health")
            assert response.status_code == 503
            assert response.json() == {"status": "degraded", "db": "unreachable"}
            assert "private" not in response.text
    asyncio.run(run())

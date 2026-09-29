import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi import HTTPException
from pydantic import ValidationError


def test_startup_rejects_missing_secret(monkeypatch):
    from app import main
    from app.config import Settings

    monkeypatch.delenv("AGENT_API_KEY", raising=False)
    monkeypatch.setattr(main, "get_settings", lambda: Settings(_env_file=None))

    async def start():
        async with main.lifespan(main.app):
            pytest.fail("Startup accepted missing API key")

    with pytest.raises(ValidationError):
        asyncio.run(start())


def test_concurrent_requests_cannot_exceed_rate_limit(fake_redis):
    from app.rate_limiter import RateLimiter

    barrier = Barrier(12)

    def request(_):
        barrier.wait()
        try:
            RateLimiter(fake_redis, 3).check("shared", now=1000)
            return 200
        except HTTPException as exc:
            return exc.status_code

    with ThreadPoolExecutor(max_workers=12) as pool:
        codes = list(pool.map(request, range(12)))
    assert codes.count(200) == 3
    assert codes.count(429) == 9


def test_budget_reservation_blocks_other_instances_and_refunds(fake_redis):
    from app.cost_guard import CostGuard

    first = CostGuard(fake_redis, 0.005)
    second = CostGuard(fake_redis, 0.005)
    with first.reserve("shared", 0.003) as month:
        with pytest.raises(HTTPException) as err:
            with second.reserve("shared", 0.003):
                pytest.fail("Oversubscribed budget")
        assert err.value.status_code == 402
        first.record("shared", 0.001, month)
    assert first.spent("shared") == pytest.approx(0.001)
    with pytest.raises(RuntimeError):
        with first.reserve("shared", 0.003):
            raise RuntimeError("LLM failed")
    assert first.spent("shared") == pytest.approx(0.001)


def test_insufficient_budget_stops_before_llm(client_factory, auth_headers, monkeypatch):
    from app import main

    def forbidden(*args, **kwargs):
        pytest.fail("LLM called without sufficient budget")

    monkeypatch.setattr(main, "ask_llm", forbidden)
    client = client_factory(budget=0.000001)
    assert client.post("/ask", json={"question": "Hi"}, headers=auth_headers).status_code == 402

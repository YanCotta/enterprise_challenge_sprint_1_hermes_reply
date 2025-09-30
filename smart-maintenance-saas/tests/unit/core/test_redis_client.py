import pytest  # type: ignore

from core import redis_client


class _DummyRedis:
    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:  # pragma: no cover - trivial
        self.closed = True


class _DummyPool:
    def __init__(self) -> None:
        self.closed = False

    async def aclose(self) -> None:  # pragma: no cover - trivial
        self.closed = True


@pytest.mark.asyncio
async def test_init_redis_client_retries_until_success(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts = {"count": 0}

    async def _connect(self: redis_client.RedisClient) -> None:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise ConnectionError("redis not ready")
        self._redis = _DummyRedis()
        self._connection_pool = _DummyPool()

    monkeypatch.setattr(
        redis_client.RedisClient,
        "connect",
        _connect,
        raising=False,
    )

    client = await redis_client.init_redis_client(
        redis_url="redis://test:6379/0",
        retries=2,
        retry_delay=0,
    )

    assert attempts["count"] == 2
    assert client.is_connected

    await redis_client.close_redis_client()


@pytest.mark.asyncio
async def test_close_redis_client_invokes_disconnect(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _connect(self: redis_client.RedisClient) -> None:
        self._redis = _DummyRedis()
        self._connection_pool = _DummyPool()

    disconnect_called = {"flag": False}
    original_disconnect = redis_client.RedisClient.disconnect

    async def _disconnect(self: redis_client.RedisClient) -> None:
        disconnect_called["flag"] = True
        await original_disconnect(self)

    monkeypatch.setattr(
        redis_client.RedisClient,
        "connect",
        _connect,
        raising=False,
    )
    monkeypatch.setattr(
        redis_client.RedisClient,
        "disconnect",
        _disconnect,
        raising=False,
    )

    await redis_client.init_redis_client(
        redis_url="redis://test:6379/0",
        retries=1,
        retry_delay=0,
    )
    await redis_client.close_redis_client()

    assert disconnect_called["flag"] is True
    assert redis_client._redis_client is None  # type: ignore[attr-defined]

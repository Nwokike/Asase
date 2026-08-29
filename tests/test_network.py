"""Tests for NetworkManager and ResilientRetryTransport."""

from unittest.mock import patch

import httpx
import pytest

from core.network import NetworkManager, ResilientRetryTransport


def test_network_manager_singleton():
    client1 = NetworkManager.get_client()
    client2 = NetworkManager.get_client()
    assert client1 is client2
    assert isinstance(client1, httpx.AsyncClient)


@pytest.mark.asyncio
async def test_retry_transport_retries_transient_error():
    transport = ResilientRetryTransport(max_retries=2, backoff_factor=0.01)

    mock_req = httpx.Request("GET", "https://api.open-meteo.com/test")
    call_count = 0

    async def _mock_handle(request):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            return httpx.Response(502, request=request)
        return httpx.Response(200, request=request)

    with patch.object(
        httpx.AsyncHTTPTransport, "handle_async_request", side_effect=_mock_handle
    ):
        resp = await transport.handle_async_request(mock_req)
        assert resp.status_code == 200
        assert call_count == 2

"""Network hooks."""

import httpx
import pytest

from core.network import AUTOCOMPLETE_TIMEOUT, on_request_hook, on_response_hook


def test_autocomplete_timeout_values():
    assert AUTOCOMPLETE_TIMEOUT.connect == 2.5
    assert AUTOCOMPLETE_TIMEOUT.read == 5.0


@pytest.mark.asyncio
async def test_hooks():
    req = httpx.Request("GET", "https://example.com/path")
    await on_request_hook(req)
    assert "User-Agent" in req.headers
    assert "Asase" in req.headers["User-Agent"]
    assert "start_time" in req.extensions
    resp = httpx.Response(200, request=req)
    await on_response_hook(resp)

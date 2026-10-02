"""Pytest configuration and mocks for Asase."""

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import flet as ft
import httpx
import pytest


@pytest.fixture
def mock_page():
    page = MagicMock(spec=ft.Page)
    page.web = False
    page.client_storage = MagicMock()
    page.client_storage.get.return_value = None
    page.client_storage.set.return_value = None
    page.services = []
    page.theme_mode = ft.ThemeMode.SYSTEM
    page.web = False
    page.session_id = None
    page.platform = MagicMock()
    page.platform.is_mobile.return_value = False
    return page


def _response(payload, status=200, headers=None):
    return httpx.Response(
        status,
        json=payload,
        headers=headers or {},
        request=httpx.Request("GET", "https://example.invalid"),
    )


@contextmanager
def mock_pool_response(module_path, response=None, *, exc=None):
    """Variant of :func:`mock_pool_get` taking a ready-made ``httpx.Response``
    (or an exception) instead of building one from a payload. ``module_path``
    is documentation-only; the singleton seam is patched either way. Yields
    the mock pooled client so tests can assert on ``client.get.call_args``.
    """
    _ = module_path
    client = MagicMock()
    if exc is not None:
        client.get = AsyncMock(side_effect=exc)
    else:
        client.get = AsyncMock(return_value=response)
    with patch("core.network.NetworkManager.get_client", return_value=client) as m:
        yield client, m


@contextmanager
def mock_pool_side_effect(module_path, func):
    """Variant taking a routing function ``func(url, **kwargs) -> Response``.

    For services fanning out to multiple URLs (space-weather's 3 NOAA
    feeds, atmospheric's 4 Open-Meteo feeds). Same singleton seam.
    """
    _ = module_path
    client = MagicMock()
    client.get = AsyncMock(side_effect=func)
    with patch("core.network.NetworkManager.get_client", return_value=client) as m:
        yield client, m


@contextmanager
def mock_pool_get(module_path, payload=None, *, status=200, headers=None, exc=None):
    """Patch the REAL seam: the pooled ``NetworkManager.get_client``.

    ``module_path`` names the service under test (kept for readability at
    call sites). The singleton in ``core.network`` is patched as the choke
    point, so validator-based services (seismic/disaster/atmospheric) run
    their real conditional-request code and direct-pool services
    (space-weather/geocoding/AI/update) run their real client code. A
    service that news its own ``httpx.AsyncClient`` bypasses the mock and
    fails loudly — that is the regression proof.
    """
    _ = module_path  # documentation only; the seam is the singleton
    client = MagicMock()
    if exc is not None:
        client.get = AsyncMock(side_effect=exc)
        client.stream = MagicMock(side_effect=exc)
    else:
        resp = _response(payload, status, headers)
        client.get = AsyncMock(return_value=resp)
        client.stream = MagicMock(return_value=resp)
    with patch("core.network.NetworkManager.get_client", return_value=client) as m:
        yield client, m

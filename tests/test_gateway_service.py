"""Tests for Kiri Gateway integration (public /version endpoint only)."""

from unittest.mock import AsyncMock, MagicMock, patch

from services.gateway_service import fetch_latest_version, is_newer_version


def test_is_newer_version_true():
    assert is_newer_version("1.2.0", "1.1.0") is True
    assert is_newer_version("2.0.0", "1.9.9") is True
    assert is_newer_version("1.1.1", "1.1.0") is True


def test_is_newer_version_false():
    assert is_newer_version("1.0.0", "1.1.0") is False
    assert is_newer_version("1.1.0", "1.1.0") is False
    assert is_newer_version("1.1", "1.1.0") is False


def test_is_newer_version_garbage():
    assert is_newer_version("", "1.1.0") is False
    assert is_newer_version("latest", "1.1.0") is False
    assert is_newer_version(None, "1.1.0") is False  # type: ignore[arg-type]


async def test_fetch_latest_version_ok():
    client = MagicMock()
    res = MagicMock(status_code=200)
    res.json.return_value = {"latest_version": "1.2.0", "min_version": "1.0.0"}
    client.get = AsyncMock(return_value=res)
    with patch(
        "services.gateway_service.NetworkManager.get_client", return_value=client
    ):
        assert await fetch_latest_version() == "1.2.0"


async def test_fetch_latest_version_no_field():
    client = MagicMock()
    res = MagicMock(status_code=200)
    res.json.return_value = {"status": "ok"}
    client.get = AsyncMock(return_value=res)
    with patch(
        "services.gateway_service.NetworkManager.get_client", return_value=client
    ):
        assert await fetch_latest_version() is None


async def test_fetch_latest_version_fails_soft():
    with patch(
        "services.gateway_service.NetworkManager.get_client",
        side_effect=RuntimeError("offline"),
    ):
        assert await fetch_latest_version() is None

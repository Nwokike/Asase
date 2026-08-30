"""Kiri Gateway client — public, unauthenticated endpoints only.

Asase's vision is auth-free direct-to-source telemetry; the gateway is used
solely for the public /version endpoint (app update checks), matching how
spaninsight and akili-app use api.kiri.ng. The gateway is strictly optional —
every call fails soft and never blocks app startup.
"""

from __future__ import annotations

import logging

from core.constants import GATEWAY_VERSION_URL
from core.network import NetworkManager

logger = logging.getLogger("asase.gateway")


async def fetch_latest_version() -> str | None:
    """Fetch the latest published Asase version from the gateway, if reachable."""
    try:
        client = NetworkManager.get_client()
        res = await client.get(GATEWAY_VERSION_URL)
        if res.status_code == 200:
            data = res.json()
            version = data.get("latest_version")
            return str(version) if version else None
    except Exception as ex:
        logger.debug("Gateway version check skipped: %s", ex)
    return None


def is_newer_version(latest: str, current: str) -> bool:
    """Dotted-numeric semver compare: True when latest > current."""
    try:
        latest_parts = tuple(int(p) for p in latest.strip().split("."))
        current_parts = tuple(int(p) for p in current.strip().split("."))
        return latest_parts > current_parts
    except (ValueError, AttributeError):
        return False

"""Pytest configuration and mocks for Asase."""

from unittest.mock import MagicMock

import flet as ft
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
    page.session_id = None
    page.platform = MagicMock()
    page.platform.is_mobile.return_value = False
    return page

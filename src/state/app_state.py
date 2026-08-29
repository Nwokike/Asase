"""React-style context for the AppState singleton."""

import flet as ft

from core.state import state

AppStateCtx = ft.create_context(state)

"""Tree-walker slot coverage (Batch S).

Proves walk() descends into the slots it previously missed: dialog
actions, app-bar leading/title, search-bar adornments, list-tile parts,
and map layers.
"""

import flet as ft
import flet_map as fmap
from flet_tree import walk, walk_buttons, walk_texts


def test_walk_sees_dialog_actions():
    dlg = ft.AlertDialog(
        title=ft.Text("Title"),
        content=ft.Text("Body"),
        actions=[ft.TextButton("Cancel"), ft.FilledButton("Go")],
    )
    # String-content buttons are reachable as controls (their labels live
    # in .content, not as ft.Text — a helper limitation, not app code).
    buttons = list(walk_buttons(dlg))
    assert len(buttons) == 2
    assert {b.content for b in buttons} == {"Cancel", "Go"}
    texts = [t.value for t in walk_texts(dlg)]
    assert "Title" in texts and "Body" in texts


def test_walk_sees_appbar_slots():
    bar = ft.AppBar(
        leading=ft.IconButton(icon=ft.Icons.ARROW_BACK_ROUNDED),
        title=ft.Text("Dossier"),
    )
    texts = [t.value for t in walk_texts(bar)]
    assert "Dossier" in texts
    icons = [c for c in walk(bar) if isinstance(c, ft.IconButton)]
    assert len(icons) == 1


def test_walk_sees_searchbar_and_listtile_slots():
    bar = ft.SearchBar(
        bar_leading=ft.Icon(ft.Icons.SEARCH_ROUNDED),
        bar_trailing=[ft.IconButton(icon=ft.Icons.MY_LOCATION_ROUNDED)],
    )
    icons = [c for c in walk(bar) if isinstance(c, (ft.Icon, ft.IconButton))]
    assert len(icons) == 2
    tile = ft.ListTile(
        leading=ft.Icon(ft.Icons.LOCATION_CITY_ROUNDED),
        title=ft.Text("Lagos"),
        subtitle=ft.Text("Nigeria"),
    )
    texts = [t.value for t in walk_texts(tile)]
    assert texts == ["Lagos", "Nigeria"]


def test_walk_sees_map_layers():
    m = fmap.Map(
        layers=[
            fmap.TileLayer(url_template="https://x.test/{z}/{x}/{y}.png"),
            fmap.MarkerLayer(markers=[]),
        ],
        initial_center=fmap.MapLatitudeLongitude(0.0, 0.0),
    )
    layers = [c for c in walk(m) if isinstance(c, fmap.MapLayer)]
    assert len(layers) == 2

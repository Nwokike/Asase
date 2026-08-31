"""Map AI Scan panel — vision analysis of the live hazard map screenshot."""

from __future__ import annotations

import flet as ft

from core import tokens
from core.theme import AppColors, AppStyles


def build_map_scan_section(
    answer: str,
    busy: bool,
    unavailable: bool,
    question: str,
    model: str,
    on_scan,
    on_ask,
    on_question_change,
    is_dark: bool = False,
    on_open_link=None,
) -> ft.Container:
    """Floating bottom panel: 'AI Scan This Map' + streamed answer + follow-up.

    Collapses to a single pill button when idle with no answer, so it never
    fights the map for space until the user asks for it. The answer renders
    as rich Markdown via the family-standard stylesheet.
    """

    def _answer_view() -> ft.Control:
        return ft.Markdown(
            value=answer,
            selectable=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            md_style_sheet=AppStyles.markdown_stylesheet(is_dark),
            on_tap_link=((lambda e: on_open_link(e.data)) if on_open_link else None),
        )

    header = ft.Row(
        [
            ft.Container(
                content=ft.Icon(
                    ft.Icons.PSYCHOLOGY_ROUNDED,
                    size=tokens.ICON_MD,
                    color=AppColors.ATMOSPHERE,
                ),
                width=tokens.ICON_BACKDROP,
                height=tokens.ICON_BACKDROP,
                border_radius=tokens.ICON_BACKDROP_RADIUS,
                bgcolor=ft.Colors.with_opacity(
                    tokens.OPACITY_LIGHT, AppColors.ATMOSPHERE
                ),
                alignment=ft.Alignment.CENTER,
            ),
            ft.Column(
                [
                    ft.Text(
                        "AI Map Scan",
                        size=tokens.FONT_MD,
                        weight=ft.FontWeight.W_600,
                        font_family="Outfit",
                    ),
                    ft.Text(
                        "Send this exact map view to Kiri Intelligence for a visual hazard read.",
                        size=tokens.FONT_XS,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
                spacing=tokens.SPACE_XXS,
                expand=True,
            ),
        ],
        spacing=tokens.SPACE_MD,
    )

    body_rows: list = [header]

    if busy and not answer:
        body_rows.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.ProgressRing(width=18, height=18, stroke_width=2),
                        ft.Text(
                            "Scanning map view...",
                            size=tokens.FONT_XS,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                    spacing=tokens.SPACE_SM,
                ),
                padding=tokens.SPACE_SM,
                alignment=ft.Alignment.CENTER,
            )
        )
    if answer:
        body_rows.append(
            ft.Container(
                content=_answer_view(),
                padding=tokens.SPACE_MD,
                border_radius=tokens.RADIUS_MD,
                bgcolor=ft.Colors.with_opacity(0.06, AppColors.ATMOSPHERE),
                border=ft.Border.all(
                    1, ft.Colors.with_opacity(0.2, AppColors.ATMOSPHERE)
                ),
            )
        )
    if answer and model and not busy:
        body_rows.append(
            ft.Text(
                f"via {model}",
                size=tokens.FONT_XS,
                color=ft.Colors.ON_SURFACE_VARIANT,
                italic=True,
            )
        )
    if unavailable and not busy and not answer:
        body_rows.append(
            ft.Text(
                "AI scan unavailable right now — the map itself is unaffected.",
                size=tokens.FONT_XS,
                color=ft.Colors.ON_SURFACE_VARIANT,
            )
        )

    body_rows.append(
        ft.Row(
            [
                ft.FilledButton(
                    icon=ft.Icons.AUTO_AWESOME_ROUNDED,
                    content=ft.Text(
                        "Rescan View" if answer else "AI Scan This Map",
                        size=tokens.FONT_SM,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.WHITE,
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=AppColors.ATMOSPHERE,
                        shape=ft.RoundedRectangleBorder(radius=tokens.RADIUS_MD),
                    ),
                    on_click=on_scan,
                    disabled=busy,
                ),
                (
                    ft.TextButton(
                        content=ft.Text(
                            "Close",
                            size=tokens.FONT_SM,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        on_click=lambda e: on_scan(close_only=True),
                    )
                    if answer
                    else None
                ),
            ],
            spacing=tokens.SPACE_SM,
        )
    )
    if answer and not busy:
        body_rows.append(
            ft.TextField(
                value=question,
                hint_text="Ask a follow-up about this map view...",
                border_radius=tokens.RADIUS_MD,
                text_size=tokens.FONT_SM,
                content_padding=tokens.SPACE_SM,
                on_submit=on_ask,
                on_change=on_question_change,
            )
        )

    return ft.Container(
        content=AppStyles.glass_card(
            ft.Column(body_rows, spacing=tokens.SPACE_XS, tight=True)
        ),
        padding=ft.Padding(
            tokens.SPACE_LG, tokens.SPACE_LG, tokens.SPACE_LG, tokens.SPACE_XL
        ),
    )


__all__ = ["build_map_scan_section"]

"""Design tokens for Asase Earth Intelligence.

Consistent spacing, typography, radii, icon sizes, and animations.
"""

from __future__ import annotations

# Spacing
SPACE_XXS = 2
SPACE_XS = 4
SPACE_SM = 8
SPACE_MD = 12
SPACE_LG = 16
SPACE_XL = 20
SPACE_XXL = 24
SPACE_XXXL = 32

# Typography
FONT_XXS = 10
FONT_XS = 11
FONT_SM = 13
FONT_MD = 14
FONT_LG = 16
FONT_XL = 18
FONT_XXL = 22
FONT_HERO = 28

# Corner Radii
RADIUS_XS = 4
RADIUS_SM = 8
RADIUS_MD = 12
RADIUS_LG = 16
RADIUS_XL = 20
RADIUS_FULL = 999

# Icon Sizes
ICON_XS = 14
ICON_SM = 18
ICON_MD = 22
ICON_LG = 26
ICON_XL = 32

# Icon Backdrop
ICON_BACKDROP = 36
ICON_BACKDROP_RADIUS = 18

# Opacities
OPACITY_LIGHT = 0.05
OPACITY_SUBTLE = 0.10
OPACITY_MEDIUM = 0.15
OPACITY_DIM = 0.60
OPACITY_HIGH = 0.85

# Animation Durations (ms)
ANIM_FAST = 150
ANIM_NORMAL = 250
ANIM_SLOW = 400

# Responsive Breakpoints (M3 window-size classes)
# Compact (<600): bottom navigation · Medium (600-840): navigation rail ·
# Expanded (>840): collapsible sidebar. Kept legacy aliases (SM/MD/LG map to
# the class edges) because tests pin them; prefer WINDOW_* below.
BREAKPOINT_SM = 360
BREAKPOINT_MD = 600
BREAKPOINT_LG = 900

WINDOW_COMPACT_MAX = 599.0
WINDOW_MEDIUM_MAX = 839.0

# Adaptive chrome widths
SIDEBAR_EXPANDED_WIDTH = 264.0
SIDEBAR_RAIL_WIDTH = 72.0
CONTENT_MAX_WIDTH = 1120.0
CONTENT_NARROW_MAX_WIDTH = 720.0

# Typography — UI face + data (mono) face. Outfit ships as the bundled app
# font; DATA_FONT_FAMILY falls back to platform monospace where JetBrains
# Mono is unavailable (add the TTF under src/assets to use it verbatim).
UI_FONT_FAMILY = "Outfit"
DATA_FONT_FAMILY = "JetBrains Mono"

# Type scale additions for dashboard hero numerals
FONT_DISPLAY = 36
FONT_OVERLINE = 10

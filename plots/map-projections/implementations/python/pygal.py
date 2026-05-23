""" anyplot.ai
map-projections: World Map with Different Projections
Library: pygal 3.1.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-23
"""

import os
import sys


# Remove this script's own directory from sys.path so 'pygal.py' doesn't shadow
# the installed pygal package (a Python gotcha when the file shares a package name)
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _here]

from pygal.style import Style
from pygal_maps_world.maps import World


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# anyplot_seq (4 stops, brand green → dark azure): maps equatorial→polar distortion
# Lerped manually: #009E73 → #003D94 at t = 0, 1/3, 2/3, 1
ZONE_COLORS = ("#009E73", "#007E7E", "#005D89", "#003D94")

# Mercator distortion factor (≈ sec²φ, i.e. area exaggeration vs true size)
# 1.0 = accurate at equator; higher = more bloated toward the poles in Mercator
country_distortion = {
    # Polar zone (60°+ latitude): extreme Mercator distortion
    "gl": 14.3,
    "ru": 3.5,
    "ca": 3.0,
    "no": 2.8,
    "is": 2.6,
    "se": 2.5,
    "fi": 2.4,
    # Temperate zone (30°–60° latitude): significant distortion
    "us": 1.4,
    "gb": 1.4,
    "cl": 1.4,
    "de": 1.3,
    "fr": 1.3,
    "ar": 1.3,
    "nz": 1.3,
    "jp": 1.2,
    "cn": 1.2,
    "au": 1.2,
    # Subtropical zone (15°–30° latitude): moderate distortion
    "za": 1.1,
    "eg": 1.1,
    "mx": 1.1,
    # Equatorial zone (0°–15° latitude): minimal distortion
    "br": 1.0,
    "co": 1.0,
    "ke": 1.0,
    "id": 1.0,
    "ng": 1.0,
    "cd": 1.0,
    "ec": 1.0,
    "ug": 1.0,
    "my": 1.0,
    "th": 1.0,
    "vn": 1.0,
    "ph": 1.0,
}

equatorial_zone = {k: v for k, v in country_distortion.items() if v < 1.1}
subtropical_zone = {k: v for k, v in country_distortion.items() if 1.1 <= v < 1.2}
temperate_zone = {k: v for k, v in country_distortion.items() if 1.2 <= v < 2.4}
polar_zone = {k: v for k, v in country_distortion.items() if v >= 2.4}

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=ZONE_COLORS,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

worldmap = World(
    style=custom_style,
    width=3200,
    height=1800,
    title="map-projections · python · pygal · anyplot.ai",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=40,
    print_values=False,
    print_labels=False,
)

# Zones ordered equatorial→polar so ZONE_COLORS maps low→high distortion
worldmap.add("0°–15°  ·  distortion < 1.1×", equatorial_zone)
worldmap.add("15°–30°  ·  distortion 1.1–1.2×", subtropical_zone)
worldmap.add("30°–60°  ·  distortion 1.2–2.4×", temperate_zone)
worldmap.add("60°+  ·  distortion ≥ 2.4×", polar_zone)

worldmap.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(worldmap.render())

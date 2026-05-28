""" anyplot.ai
bar-3d-categorical: 3D Bar Chart for Categorical Comparison
Library: pygal 3.1.0 | Python 3.13.13
Quality: 81/100 | Created: 2026-05-15
"""

import os
import sys


# Temporarily remove current directory from path to avoid name collision with pygal package
_cwd = sys.path[0] if sys.path[0] else "."
if _cwd in sys.path:
    sys.path.remove(_cwd)

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path.insert(0, _cwd)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data: Crop yield (kg/hectare) across five wheat varieties and four fertilizer treatments
varieties = ["Aster", "Borealis", "Crocus", "Delphi", "Ember"]
yields = {
    "Control": [2850, 3120, 2640, 3380, 2970],
    "Nitrogen+": [3540, 3820, 3290, 4050, 3650],
    "Phosphorus+": [3180, 3460, 2980, 3720, 3310],
    "NPK Blend": [3920, 4210, 3680, 4480, 4020],
}

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

# Plot
chart = pygal.Bar(
    style=custom_style,
    width=4800,
    height=2700,
    title="Crop Yield by Variety & Treatment · bar-3d-categorical · pygal · anyplot.ai",
    x_title="Crop Variety",
    y_title="Yield (kg / hectare)",
    show_legend=True,
    show_y_guides=True,
    show_x_guides=False,
    margin=80,
)

chart.x_labels = varieties

for treatment, values in yields.items():
    chart.add(treatment, values)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())

"""anyplot.ai
scatter-annotated: Annotated Scatter Plot with Text Labels
Library: pygal | Python 3.13
Quality: 91/100 | Updated: 2025-05-13
"""

import os
import sys


# Workaround: pygal.py file in cwd conflicts with pygal package.
# Remove current directory from sys.path before importing.
_original_path = sys.path[:]
while "" in sys.path:
    sys.path.remove("")
if sys.path[0].endswith("implementations/python"):
    sys.path.pop(0)

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path = _original_path


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Okabe-Ito palette: first series = #009E73 (brand green)
OKABE_ITO = (
    "#009E73",  # 1: bluish green (brand)
    "#D55E00",  # 2: vermillion
    "#0072B2",  # 3: blue
    "#CC79A7",  # 4: reddish purple
    "#E69F00",  # 5: orange
    "#56B4E9",  # 6: sky blue
    "#F0E442",  # 7: yellow
    "#009E73",  # 8: cycle back to brand for 8+ companies
    "#D55E00",
    "#0072B2",
    "#CC79A7",
    "#E69F00",
)

# Data - Tech company market performance
companies = [
    "TechFlow",
    "DataPrime",
    "CloudNine",
    "NetWave",
    "CodeSphere",
    "ByteLogic",
    "SoftEdge",
    "DevStack",
    "AppForge",
    "WebCore",
    "CyberLink",
    "DigiTech",
]

# Market cap (x) and annual revenue (y) in billions
market_cap = np.array([15, 45, 75, 105, 135, 25, 55, 85, 115, 145, 35, 95])
revenue = np.array([8, 22, 35, 28, 48, 12, 18, 42, 32, 55, 15, 38])

# Custom style with theme-adaptive colors and chrome
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=16,
    stroke_width=3,
)

# Create scatter chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-annotated · pygal · anyplot.ai",
    x_title="Market Cap (Billion $)",
    y_title="Annual Revenue (Billion $)",
    show_legend=False,
    show_x_guides=True,
    show_y_guides=True,
    dots_size=16,
    stroke=False,
    show_dots=True,
    range=(0, 65),
    xrange=(0, 165),
    print_values=True,
    print_values_position="top",
)

# Add each company as individual series with Okabe-Ito color and annotation
for i, company in enumerate(companies):
    chart.add(
        company,
        [{"value": (market_cap[i], revenue[i]), "label": company, "formatter": lambda x, c=company: c}],
        dots_size=18,
        formatter=lambda x, c=company: c,
    )

# Render to PNG and HTML with theme suffix
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())

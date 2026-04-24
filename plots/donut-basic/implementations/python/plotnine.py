"""anyplot.ai
donut-basic: Basic Donut Chart
Library: plotnine 0.15.3 | Python 3.14
Quality: pending | Created: 2026-04-24
"""

import math
import os
import sys


# Avoid name collision: drop this script's directory from sys.path
# so `from plotnine import ...` resolves to the installed package.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _HERE]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from plotnine import (  # noqa: E402
    aes,
    annotate,
    coord_fixed,
    element_blank,
    element_rect,
    element_text,
    geom_polygon,
    geom_text,
    ggplot,
    labs,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
LABEL_ON_WEDGE = "#F0EFE8"

# Okabe-Ito palette (first segment is always the brand green)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

# Data - Annual budget allocation by department (USD thousands)
categories = ["Engineering", "Marketing", "Operations", "Sales", "Support"]
values = [480, 210, 155, 125, 55]
total = sum(values)

# Ring dimensions
inner_radius = 0.62
outer_radius = 1.0
label_radius = 1.18
pct_radius = (inner_radius + outer_radius) / 2

# Build annular-segment polygons for each category
wedge_rows = []
label_rows = []
pct_rows = []

start_angle = math.pi / 2  # Start at 12 o'clock
for category, value, color in zip(categories, values, OKABE_ITO, strict=True):
    sweep = (value / total) * 2 * math.pi
    end_angle = start_angle - sweep  # Clockwise

    # Slight gap between wedges for crisp separation
    gap = 0.008
    a0 = end_angle + gap
    a1 = start_angle - gap

    n = 80
    inner_arc = np.linspace(a0, a1, n)
    outer_arc = np.linspace(a1, a0, n)

    points = [(inner_radius * math.cos(a), inner_radius * math.sin(a)) for a in inner_arc]
    points += [(outer_radius * math.cos(a), outer_radius * math.sin(a)) for a in outer_arc]

    for order, (x, y) in enumerate(points):
        wedge_rows.append({"x": x, "y": y, "segment": category, "order": order, "fill": color})

    mid_angle = (start_angle + end_angle) / 2
    label_rows.append(
        {"x": label_radius * math.cos(mid_angle), "y": label_radius * math.sin(mid_angle), "label": category}
    )
    pct_rows.append(
        {
            "x": pct_radius * math.cos(mid_angle),
            "y": pct_radius * math.sin(mid_angle),
            "label": f"{value / total * 100:.1f}%",
        }
    )

    start_angle = end_angle

wedge_df = pd.DataFrame(wedge_rows)
label_df = pd.DataFrame(label_rows)
pct_df = pd.DataFrame(pct_rows)

# Plot
plot = (
    ggplot()
    + geom_polygon(aes(x="x", y="y", group="segment", fill="fill"), data=wedge_df, color=PAGE_BG, size=1.2)
    + geom_text(aes(x="x", y="y", label="label"), data=pct_df, size=14, fontweight="bold", color=LABEL_ON_WEDGE)
    + geom_text(aes(x="x", y="y", label="label"), data=label_df, size=16, color=INK)
    + annotate("text", x=0, y=0.13, label="Total budget", size=14, color=INK_SOFT)
    + annotate("text", x=0, y=-0.08, label=f"${total:,}K", size=28, fontweight="bold", color=INK)
    + scale_fill_identity()
    + coord_fixed(ratio=1)
    + scale_x_continuous(limits=(-1.45, 1.45))
    + scale_y_continuous(limits=(-1.35, 1.35))
    + labs(title="Budget by Department · donut-basic · plotnine · anyplot.ai")
    + theme(
        figure_size=(12, 12),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=22, color=INK, ha="center", margin={"b": 18}),
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        legend_position="none",
    )
)

plot.save(f"plot-{THEME}.png", dpi=300)

"""anyplot.ai
scatter-color-mapped: Color-Mapped Scatter Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-08
"""

import os
import sys


# Prevent importing the local pygal.py file instead of the installed package
sys.path = [p for p in sys.path if not p.endswith("/implementations/python")]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette (continuous data uses the imprint_seq ramp below instead)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
N_BINS = 10  # pygal has no continuous colorbar: the ramp is cut into this many legend steps

# Columns: set these to your table's column names
NITROGEN = "Soil nitrogen (mg/kg)"  # role: x
RAINFALL = "Seasonal rainfall (mm)"  # role: y
YIELD = "Wheat yield (t/ha)"  # role: color

# Data: replace this block with your own table, for example df = pd.read_csv("plots.csv")
rng = np.random.default_rng(7)
n_plots = 150
nitrogen = rng.uniform(10, 90, n_plots)
rainfall = rng.uniform(250, 750, n_plots)
# Yield rises with both inputs, saturates, and carries plot-to-plot noise
crop_yield = 2.0 + 4.5 * (1 - np.exp(-nitrogen / 45)) * (1 - np.exp(-rainfall / 300)) + rng.normal(0, 0.45, n_plots)
df = pd.DataFrame({NITROGEN: nitrogen, RAINFALL: rainfall, YIELD: crop_yield})


# Plot
def lerp_hex(c0, c1, t):
    """Linear RGB blend between two hex colors."""
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(u + (v - u) * t):02X}" for u, v in zip(a, b, strict=True))


# imprint_seq: brand green to blue, sampled once per bin
ramp = [lerp_hex("#009E73", "#4467A3", i / (N_BINS - 1)) for i in range(N_BINS)]

# Bin the continuous variable; every point lands in exactly one color step
edges = np.linspace(df[YIELD].min(), df[YIELD].max(), N_BINS + 1)
bin_index = np.clip(np.digitize(df[YIELD], edges[1:-1]), 0, N_BINS - 1)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(ramp),
    title_font_size=60,
    label_font_size=52,
    major_label_font_size=42,
    legend_font_size=40,
    value_font_size=36,
    opacity=0.9,
    opacity_hover=1.0,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="scatter-color-mapped · python · pygal · anyplot.ai",
    x_title=NITROGEN,
    y_title=RAINFALL,
    show_dots=True,
    dots_size=14,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=34,
    truncate_legend=-1,
    margin=40,
)
# Thin page-colored outline keeps both ends of the ramp visible on either page color
chart.config.css.append(f"inline:.dot{{stroke:{PAGE_BG};stroke-width:2px}}")

# One series per color step, labelled with its value range (the legend acts as the colorbar)
for i in range(N_BINS):
    rows = df[bin_index == i]
    label = f"{edges[i]:.1f}–{edges[i + 1]:.1f} t/ha"
    chart.add(label, list(zip(rows[NITROGEN], rows[RAINFALL], strict=True)))

# Save
chart.render_to_png(f"plot-{THEME}.png")
chart.render_to_file(f"plot-{THEME}.html")

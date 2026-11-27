""" anyplot.ai
map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-27
"""

import math
import os
from itertools import pairwise

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for fields (colored cells that fill the plot), as (position, hex) stops
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Columns: set these to your table's column names
REGION = "Region"  # role: region
SHARE = "Renewable share (%)"  # role: value
ROW = "Grid row"  # role: row
COL = "Grid column"  # role: col

# Data: replace this block with your own table, for example df = pd.read_csv("tiles.csv")
# Renewable energy share (%) of gross final energy consumption, European countries
# region: (grid_row, grid_col, approximate_share)
countries = {
    "IS": (0, 2, 78),
    "NO": (1, 4, 71),
    "SE": (1, 5, 66),
    "FI": (1, 6, 52),
    "IE": (2, 0, 14),
    "UK": (2, 1, 21),
    "DK": (2, 4, 43),
    "EE": (2, 7, 32),
    "NL": (3, 1, 15),
    "DE": (3, 3, 21),
    "PL": (3, 4, 17),
    "LV": (3, 7, 44),
    "BE": (4, 1, 14),
    "LU": (4, 2, 12),
    "CZ": (4, 3, 18),
    "SK": (4, 4, 19),
    "LT": (4, 7, 29),
    "FR": (5, 1, 20),
    "CH": (5, 3, 30),
    "AT": (5, 4, 40),
    "HU": (5, 5, 16),
    "RO": (5, 6, 27),
    "PT": (6, 0, 39),
    "ES": (6, 1, 22),
    "IT": (6, 3, 21),
    "SI": (6, 4, 26),
    "HR": (6, 5, 32),
    "BG": (6, 6, 22),
    "MT": (7, 3, 13),
    "GR": (7, 5, 24),
}
np.random.seed(42)
base_share = np.array([v[2] for v in countries.values()], dtype=float)
df = pd.DataFrame(
    {
        REGION: list(countries.keys()),
        ROW: [v[0] for v in countries.values()],
        COL: [v[1] for v in countries.values()],
        SHARE: np.clip(base_share + np.random.normal(0, 2.5, len(countries)), 5, 90),
    }
)

# Plot
# Per-tile label color: ink or off-white by the luminance of the tile's fill on the ramp
LABEL_DARK = "#1A1A17"
LABEL_LIGHT = "#F0EFE8"
share_span = df[SHARE].max() - df[SHARE].min()
norm_share = (df[SHARE] - df[SHARE].min()) / (share_span if share_span > 0 else 1.0)
fill_hex = [ramp_color(SEQ_FIELDS, t) for t in norm_share]
fill_rgb = np.array([[int(h[i : i + 2], 16) for i in (1, 3, 5)] for h in fill_hex])
fill_luminance = fill_rgb @ np.array([0.299, 0.587, 0.114])
df["label_color"] = np.where(fill_luminance > 120, LABEL_DARK, LABEL_LIGHT)

title = "Renewable Energy Share · map-tilegrid · python · letsplot · anyplot.ai"
title_fontsize = round(16 * min(1.0, 67 / len(title)))

plot = (
    ggplot(df, aes(x=COL, y=ROW))
    + geom_tile(aes(fill=SHARE), width=0.94, height=0.94)
    + geom_text(aes(label=REGION, color="label_color"), size=6, fontface="bold")
    + scale_color_identity()
    + scale_fill_gradientn(colors=[ramp_color(SEQ_FIELDS, k / 255) for k in range(256)], name=SHARE)
    + scale_x_continuous(expand=[0.01, 0])
    + scale_y_reverse(expand=[0.01, 0])
    + coord_fixed()
    + labs(x="", y="", title=title)
)

anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG),
    panel_border=element_rect(color=INK_SOFT, size=0.5),
    panel_grid=element_blank(),
    axis_title=element_blank(),
    axis_text=element_blank(),
    axis_ticks=element_blank(),
    axis_line=element_blank(),
    plot_title=element_text(color=INK, size=title_fontsize),
    legend_position="bottom",
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=12),
    legend_title=element_text(color=INK, size=13),
)

# The one-panel grid paints the whole canvas with the page color; the plot keeps its fixed aspect
plot = (
    gggrid([plot + anyplot_theme]) + ggsize(600, 600) + theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")

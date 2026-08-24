""" anyplot.ai
map-tilegrid: Tile Grid Map for Equal-Area Geographic Comparison
Library: letsplot 4.11.0 | Python 3.13.15
Quality: 92/100 | Created: 2026-08-24
"""

import os

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

# Data — renewable energy share (%) of gross final energy consumption, European countries
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
region = list(countries.keys())
grid_row = [v[0] for v in countries.values()]
grid_col = [v[1] for v in countries.values()]
base_share = np.array([v[2] for v in countries.values()], dtype=float)
renewable_share = np.clip(base_share + np.random.normal(0, 2.5, len(region)), 5, 90)

df = pd.DataFrame({"region": region, "grid_row": grid_row, "grid_col": grid_col, "renewable_share": renewable_share})

# Per-tile label color: pick ink or off-white depending on the imprint_seq fill's
# luminance at that value, so labels stay legible across the whole gradient
imprint_seq_low = np.array([0x00, 0x9E, 0x73])
imprint_seq_high = np.array([0x44, 0x67, 0xA3])
norm_share = (df["renewable_share"] - df["renewable_share"].min()) / (
    df["renewable_share"].max() - df["renewable_share"].min()
)
fill_rgb = imprint_seq_low[None, :] + norm_share.to_numpy()[:, None] * (imprint_seq_high - imprint_seq_low)[None, :]
fill_luminance = 0.299 * fill_rgb[:, 0] + 0.587 * fill_rgb[:, 1] + 0.114 * fill_rgb[:, 2]
df["label_color"] = np.where(fill_luminance > 140, "#1A1A17", "#F0EFE8")

# Plot — see default-style-guide.md "Visual Sizing Defaults" for the canvas + sizing values
title = "Renewable Energy Share · map-tilegrid · python · letsplot · anyplot.ai"
title_fontsize = round(16 * min(1.0, 67 / len(title)))

plot = (
    ggplot(df, aes(x="grid_col", y="grid_row"))
    + geom_tile(aes(fill="renewable_share"), width=0.92, height=0.92)
    + geom_text(aes(label="region", color="label_color"), size=4.2, fontface="bold")
    + scale_color_identity()
    + scale_fill_gradient(low="#009E73", high="#4467A3", name="Renewable share (%)")
    + scale_y_reverse()
    + coord_fixed()
    + labs(x="", y="", title=title)
    + ggsize(800, 450)
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
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=element_text(color=INK_SOFT, size=10),
    legend_title=element_text(color=INK, size=11),
)

plot = plot + anyplot_theme

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")

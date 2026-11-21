""" anyplot.ai
cat-box-strip: Box Plot with Strip Overlay
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-21
"""

import os
import pathlib

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BOX_COLOR = IMPRINT_PALETTE[0]
POINT_COLOR = IMPRINT_PALETTE[1]

# Columns
TIER = "Service Tier"  # role: category
UPTIME = "Uptime (%)"  # role: value

# Data - uptime scores across service tiers
rng = np.random.default_rng(42)
tier_params = {  # tier: (mean, sd, n, hand-placed low performers)
    "Basic": (94.5, 2.5, 30, [88.2, 91.5]),
    "Professional": (97.8, 1.8, 38, []),
    "Enterprise": (99.2, 0.9, 34, [96.5]),
    "Elite": (99.7, 0.5, 28, []),
}
frames = []
for tier, (mean, sd, n, extra) in tier_params.items():
    scores = np.concatenate([rng.normal(mean, sd, n), extra])
    frames.append(pd.DataFrame({TIER: tier, UPTIME: np.clip(scores, 85, 100)}))
df = pd.concat(frames, ignore_index=True)

# Plot
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    axis_title=element_text(color=INK, size=12),
    axis_text=element_text(color=INK_SOFT, size=10),
    axis_line=element_line(color=INK_SOFT, size=0.5),
    plot_title=element_text(color=INK, size=16),
)

plot = (
    ggplot(df, aes(x=TIER, y=UPTIME))
    + geom_boxplot(fill=BOX_COLOR, color=INK_SOFT, alpha=0.7, width=0.5, outlier_alpha=0)
    + geom_jitter(color=POINT_COLOR, size=2.5, alpha=0.65, width=0.12)
    + labs(title="cat-box-strip · python · letsplot · anyplot.ai")
    + theme_minimal()
    + anyplot_theme
    + ggsize(800, 450)
)

# Save
output_dir = pathlib.Path.cwd()
ggsave(plot, str(output_dir / f"plot-{THEME}.png"), scale=4)
ggsave(plot, str(output_dir / f"plot-{THEME}.html"))

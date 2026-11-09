""" anyplot.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: letsplot 4.11.0 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_rect,
    geom_segment,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_log10,
    theme,
    theme_minimal,
)


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette; the quantile levels are ordered, so they take steps of imprint_seq
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = ["#009E73", "#4467A3"]

# Constants
MAX_LEVELS = 6  # deepest letter value drawn, however large the sample
MAX_TINT = 0.6  # the deepest level mixes this share of white into its ramp step
MIN_LEVELS = 2
BOX_HALF_WIDTH = 0.4  # half width of the quartile box, in category units
WIDTH_DECAY = 0.85  # each deeper level is this share of the previous width
X_MIN, X_MAX, Y_MIN, Y_MAX = "x_min", "x_max", "y_min", "y_max"
X_POS, X_END, Y_POS = "x", "xend", "y"
LEVEL = "Quantile Range"

# Columns: set these to your table's column names
ENDPOINT = "Server Endpoint"  # role: category
RESPONSE_TIME = "Response Time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
n_per_group = 2000
distributions = {
    "API Gateway": {"base": 45, "scale": 20},
    "Auth Service": {"base": 80, "scale": 35},
    "Database": {"base": 120, "scale": 50},
    "Cache Layer": {"base": 8, "scale": 5},
}
frames = []
for endpoint, d in distributions.items():
    values = np.random.exponential(d["scale"], n_per_group) + d["base"]
    slow_idx = np.random.choice(n_per_group, size=int(n_per_group * 0.05), replace=False)
    values[slow_idx] = values[slow_idx] * np.random.uniform(2, 5, len(slow_idx))
    frames.append(pd.DataFrame({ENDPOINT: endpoint, RESPONSE_TIME: values}))
df = pd.concat(frames, ignore_index=True)

# Plot: reads only df and the constants above
clean = df.dropna(subset=[ENDPOINT, RESPONSE_TIME])
groups = list(clean[ENDPOINT].unique())

box_rows, median_rows, outlier_rows = [], [], []
n_levels = 0
for x_pos, group in enumerate(groups):
    values = np.sort(clean.loc[clean[ENDPOINT] == group, RESPONSE_TIME].to_numpy(dtype=float))
    k = int(np.clip(int(np.log2(len(values))) - 1, MIN_LEVELS, MAX_LEVELS))
    n_levels = max(n_levels, k)

    # Letter values: level i spans the quantiles 0.5**(i + 2) and 1 - 0.5**(i + 2)
    for i in range(k):
        depth = 0.5 ** (i + 2)
        half_width = BOX_HALF_WIDTH * WIDTH_DECAY**i
        box_rows.append(
            {
                X_MIN: x_pos - half_width,
                X_MAX: x_pos + half_width,
                Y_MIN: np.quantile(values, depth),
                Y_MAX: np.quantile(values, 1 - depth),
                LEVEL: i,
            }
        )

    median_rows.append({X_POS: x_pos - BOX_HALF_WIDTH, X_END: x_pos + BOX_HALF_WIDTH, Y_POS: np.median(values)})

    deepest = 0.5 ** (k + 1)
    low, high = np.quantile(values, deepest), np.quantile(values, 1 - deepest)
    outlier_rows.extend({X_POS: x_pos, Y_POS: v} for v in values[(values < low) | (values > high)])

# Level names give the share of observations each box spans; colors step along imprint_seq
# and lighten toward the tails, so neighbouring levels differ in hue and in shade
level_names = [f"{100 * (1 - 0.5 ** (i + 1)):.4g}%" for i in range(n_levels)]
start, end = (np.array([int(c[j : j + 2], 16) for j in (1, 3, 5)]) for c in IMPRINT_SEQ)
steps = np.linspace(0, 1, n_levels) if n_levels > 1 else np.zeros(1)
level_colors = [
    "#{:02X}{:02X}{:02X}".format(
        *np.round((start + t * (end - start)) * (1 - MAX_TINT * t) + 255 * MAX_TINT * t).astype(int)
    )
    for t in steps
]

# Deepest (narrowest, tallest) boxes first, so each wider inner box stays on top
box_df = pd.DataFrame(box_rows).sort_values(LEVEL, ascending=False, kind="stable")
box_df[LEVEL] = box_df[LEVEL].map(dict(enumerate(level_names)))
median_df = pd.DataFrame(median_rows)
outlier_df = pd.DataFrame(outlier_rows, columns=[X_POS, Y_POS])

plot = (
    ggplot()
    + geom_rect(aes(xmin=X_MIN, xmax=X_MAX, ymin=Y_MIN, ymax=Y_MAX, fill=LEVEL), data=box_df, color=INK_SOFT, size=0.4)
    + geom_segment(aes(x=X_POS, xend=X_END, y=Y_POS, yend=Y_POS), data=median_df, color=INK, size=1.2)
    + scale_fill_manual(values=dict(zip(level_names, level_colors, strict=True)), breaks=level_names, name=LEVEL)
    + scale_x_continuous(breaks=list(range(len(groups))), labels=groups)
    + scale_y_log10()
    + labs(x=ENDPOINT, y=RESPONSE_TIME, title="boxen-basic · python · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_title=element_text(size=12, color=INK),
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_line=element_line(color=INK_SOFT),
        plot_title=element_text(size=16, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=11, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
    )
    + ggsize(800, 450)
)

if not outlier_df.empty:
    plot = plot + geom_point(aes(x=X_POS, y=Y_POS), data=outlier_df, color=INK_SOFT, size=1.8, alpha=0.6)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")

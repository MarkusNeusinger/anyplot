"""anyplot.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os
import sys

import numpy as np
import pandas as pd


# Avoid shadowing by removing current directory from path during import
cwd = os.getcwd()
sys.path = [p for p in sys.path if os.path.abspath(p) != cwd]

from plotnine import (  # noqa: E402
    aes,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_rect,
    geom_segment,
    ggplot,
    labs,
    scale_fill_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1

# Columns: set these to your table's column names
ENDPOINT = "Endpoint"  # role: category
RESPONSE_TIME = "Response Time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
n_per_group = 2000
api = np.concatenate([np.random.exponential(50, n_per_group - 20), np.random.uniform(300, 500, 20)])
database = np.concatenate([np.random.normal(30, 10, n_per_group // 2), np.random.normal(100, 20, n_per_group // 2)])
cache = np.maximum(np.random.normal(15, 5, n_per_group), 1)
auth = np.random.gamma(3, 20, n_per_group)
df = pd.DataFrame(
    {
        ENDPOINT: np.repeat(["API", "Database", "Cache", "Auth"], n_per_group),
        RESPONSE_TIME: np.concatenate([api, database, cache, auth]),
    }
)

# Plot: reads only df and the constants above
categories = df[ENDPOINT].unique()
box_data = []
outlier_data = []
median_data = []

base_width = 0.8
width_decay = 0.85  # each nested level is 85% of the previous width

for i, cat in enumerate(categories):
    values = df.loc[df[ENDPOINT] == cat, RESPONSE_TIME].dropna().to_numpy()

    # Adaptive number of letter-value levels, capped at 8
    n = len(values)
    k = min(max(3, int(np.floor(np.log2(n)) - 2)), 8)

    depths = [0.5]
    for j in range(1, k):
        tail = 0.5 ** (j + 1)  # tail probability of letter value j: 1/4, 1/8, 1/16, ...
        depths.append(tail)
        depths.append(1 - tail)

    depths = sorted(set(depths))
    quantiles = np.quantile(values, depths)

    median_idx = depths.index(0.5)
    median_data.append({"x": i, "y": quantiles[median_idx]})

    # Nested boxes: level 0 spans the quartiles, each deeper level spans the next letter value
    n_pairs = (len(depths) - 1) // 2
    for level in range(n_pairs):
        width = base_width * (width_decay**level)
        box_data.append(
            {
                "xmin": i - width / 2,
                "xmax": i + width / 2,
                "ymin": quantiles[median_idx - 1 - level],
                "ymax": quantiles[median_idx + 1 + level],
                "level": level,
            }
        )

    # Observations beyond the deepest letter value
    outliers = values[(values < quantiles[0]) | (values > quantiles[-1])]
    outlier_data.extend({"x": i, "y": o} for o in outliers)

box_df = pd.DataFrame(box_data)
outlier_df = pd.DataFrame(outlier_data, columns=["x", "y"])
median_df = pd.DataFrame(median_data)
median_df["xmin"] = median_df["x"] - 0.35
median_df["xmax"] = median_df["x"] + 0.35

# Gradient from the brand green to a pale tint, one color per quantile level
n_levels = box_df["level"].max() + 1
colors = []
for lvl in range(n_levels):
    t = lvl / max(n_levels - 1, 1)
    colors.append(f"#{int(t * 200):02x}{int(158 + t * 62):02x}{int(115 + t * 125):02x}")

level_labels = [f"{50 * (0.5 ** (lvl + 1)):.1f}%-{100 - 50 * (0.5 ** (lvl + 1)):.1f}%" for lvl in range(n_levels)]

plot = (
    ggplot()
    + geom_rect(
        data=box_df.sort_values(
            "level", ascending=False
        ),  # draw the deepest, narrowest level first so the wider inner boxes sit on top
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="factor(level)"),
        color=INK_SOFT,
        size=0.15,
    )
    + geom_segment(data=median_df, mapping=aes(x="xmin", xend="xmax", y="y", yend="y"), color=INK, size=0.8)
    + geom_point(data=outlier_df, mapping=aes(x="x", y="y"), color=BRAND, size=1.2, alpha=0.5)
    + scale_fill_manual(values=colors, name="Quantile Level", labels=level_labels)
    + scale_x_continuous(breaks=list(range(len(categories))), labels=list(categories))
    + labs(title="boxen-basic · python · plotnine · anyplot.ai", x=ENDPOINT, y=RESPONSE_TIME)
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major=element_line(color=INK, alpha=0.10, size=0.15),
        panel_grid_minor=element_line(color=INK, alpha=0.05, size=0.1),
        panel_border=element_rect(color=INK_SOFT, fill=None, size=0.15),
        axis_line=element_line(color=INK_SOFT, size=0.15),
        plot_title=element_text(size=12, color=INK, weight="bold"),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        axis_text_x=element_text(size=9, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_text=element_text(size=7, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_position="right",
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")

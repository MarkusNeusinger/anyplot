""" anyplot.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
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

# Data - Generate realistic response times for different server endpoints
np.random.seed(42)
endpoints = ["API Gateway", "Auth Service", "Database", "Cache Layer"]
n_per_group = 2000

data = []
distributions = {
    "API Gateway": {"base": 45, "scale": 20, "skew": 0.5},
    "Auth Service": {"base": 80, "scale": 35, "skew": 0.8},
    "Database": {"base": 120, "scale": 50, "skew": 1.2},
    "Cache Layer": {"base": 8, "scale": 5, "skew": 0.3},
}

for endpoint in endpoints:
    d = distributions[endpoint]
    values = np.random.exponential(d["scale"], n_per_group) + d["base"]
    slow_idx = np.random.choice(n_per_group, size=int(n_per_group * 0.05), replace=False)
    values[slow_idx] = values[slow_idx] * np.random.uniform(2, 5, len(slow_idx))
    data.extend([(endpoint, v) for v in values])

df = pd.DataFrame(data, columns=["endpoint", "response_time"])

# Letter value names and colors for legend (deepest at bottom for intuitive ordering)
level_names = ["50%", "75%", "87.5%", "93.75%", "96.875%", "98.4%", "99.2%", "99.6%"]
level_colors = ["#306998", "#4A7FA8", "#6490B8", "#7EA1C8", "#98B2D8", "#B2C3E8", "#CCD4F8", "#E6E5FF"]

# Compute letter values and construct plot data inline
box_data = []
median_data = []
outlier_data = []
max_k = 0

x_positions = {endpoint: i for i, endpoint in enumerate(endpoints)}

for endpoint in endpoints:
    group_data = df[df["endpoint"] == endpoint]["response_time"].values
    sorted_vals = np.sort(group_data)
    n = len(sorted_vals)

    # Number of letter values based on data size
    k = int(np.log2(n)) - 1
    k = max(2, min(k, 8))
    max_k = max(max_k, k)

    x_pos = x_positions[endpoint]

    # Calculate letter values and build boxes
    for i in range(k):
        depth = 0.5 ** (i + 1)
        lower_q = depth
        upper_q = 1 - depth

        lower_val = np.percentile(sorted_vals, lower_q * 100)
        upper_val = np.percentile(sorted_vals, upper_q * 100)

        half_width = 0.4 * (0.85**i)
        box_data.append(
            {
                "x_min": x_pos - half_width,
                "x_max": x_pos + half_width,
                "y_min": lower_val,
                "y_max": upper_val,
                "level": level_names[i],
                "endpoint": endpoint,
            }
        )

    # Calculate median line
    median = np.median(sorted_vals)
    median_data.append({"x": x_pos - 0.38, "xend": x_pos + 0.38, "y": median, "endpoint": endpoint})

    # Calculate outliers beyond deepest letter value
    deepest_depth = 0.5**k
    deepest_lower = np.percentile(sorted_vals, deepest_depth * 100)
    deepest_upper = np.percentile(sorted_vals, (1 - deepest_depth) * 100)
    outliers = sorted_vals[(sorted_vals < deepest_lower) | (sorted_vals > deepest_upper)]

    for o in outliers:
        outlier_data.append({"x": x_pos, "y": o, "endpoint": endpoint})

box_df = pd.DataFrame(box_data)
median_df = pd.DataFrame(median_data)
outlier_df = pd.DataFrame(outlier_data) if outlier_data else pd.DataFrame(columns=["x", "y", "endpoint"])

# Plot
plot = (
    ggplot()
    + geom_rect(
        aes(xmin="x_min", xmax="x_max", ymin="y_min", ymax="y_max", fill="level"),
        data=box_df,
        alpha=0.9,
        color=INK_SOFT,
        size=0.5,
    )
    + geom_segment(aes(x="x", xend="xend", y="y", yend="y"), data=median_df, color="#FFD43B", size=3)
    + scale_fill_manual(
        values=dict(zip(level_names[:max_k], level_colors[:max_k], strict=False)), name="Quantile Range"
    )
    + scale_x_continuous(breaks=[0, 1, 2, 3], labels=endpoints)
    + labs(x="Server Endpoint", y="Response Time (ms)", title="boxen-basic · letsplot · anyplot.ai")
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_rect(color="transparent"),
        panel_grid_minor=element_rect(color="transparent"),
        axis_title=element_text(size=20, color=INK),
        axis_text=element_text(size=16, color=INK_SOFT),
        axis_line=element_text(color=INK_SOFT),
        plot_title=element_text(size=24, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        legend_title=element_text(size=18, color=INK),
        legend_text=element_text(size=14, color=INK_SOFT),
    )
    + ggsize(1600, 900)
)

# Add outliers if present
if not outlier_df.empty:
    plot = plot + geom_point(aes(x="x", y="y"), data=outlier_df, color="#DC2626", size=2, alpha=0.6)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")

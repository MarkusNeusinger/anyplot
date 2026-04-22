""" pyplots.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_line,
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


# Set seed for reproducibility
np.random.seed(42)

# Generate data - server response times by endpoint (1000+ per category)
n_per_group = 2000
endpoints = ["API", "Database", "Cache", "Auth"]

data = []
for endpoint in endpoints:
    if endpoint == "API":
        # Right-skewed with some outliers
        values = np.concatenate(
            [
                np.random.exponential(50, n_per_group - 20),
                np.random.uniform(300, 500, 20),  # Outliers
            ]
        )
    elif endpoint == "Database":
        # Bimodal - some fast, some slow queries
        values = np.concatenate(
            [np.random.normal(30, 10, n_per_group // 2), np.random.normal(100, 20, n_per_group // 2)]
        )
    elif endpoint == "Cache":
        # Fast and tight distribution
        values = np.random.normal(15, 5, n_per_group)
        values = np.maximum(values, 1)  # No negative response times
    else:  # Auth
        # Medium with heavy tail
        values = np.random.gamma(3, 20, n_per_group)

    for v in values:
        data.append({"endpoint": endpoint, "response_time": v})

df = pd.DataFrame(data)


# Compute letter values for each group
categories = df["endpoint"].unique()
box_data = []
outlier_data = []
median_data = []

# Width parameters
base_width = 0.8
width_decay = 0.85  # Each nested level is 85% of previous width

for i, cat in enumerate(categories):
    values = df[df["endpoint"] == cat]["response_time"].values

    # Calculate letter values (quantiles) inline
    n = len(values)
    k = min(max(3, int(np.floor(np.log2(n)) - 2)), 8)  # Adaptive levels, cap at 8

    # Compute quantile depths
    depths = [0.5]  # Start with median
    for j in range(1, k):
        depth = 0.5 ** (j + 1)
        depths.append(0.5 - depth)
        depths.append(0.5 + depth)

    depths = sorted(set(depths))
    quantiles = np.quantile(values, depths)

    # Find median
    median_idx = depths.index(0.5)
    median_val = quantiles[median_idx]
    median_data.append({"x": i, "y": median_val, "endpoint": cat})

    # Create nested boxes from outer to inner
    n_pairs = (len(depths) - 1) // 2
    for level in range(n_pairs):
        lower_idx = level
        upper_idx = len(depths) - 1 - level
        ymin = quantiles[lower_idx]
        ymax = quantiles[upper_idx]
        width = base_width * (width_decay**level)

        box_data.append(
            {
                "endpoint": cat,
                "x": i,
                "xmin": i - width / 2,
                "xmax": i + width / 2,
                "ymin": ymin,
                "ymax": ymax,
                "level": level,
            }
        )

    # Outliers beyond deepest letter value
    lower_bound = quantiles[0]
    upper_bound = quantiles[-1]
    outliers = values[(values < lower_bound) | (values > upper_bound)]
    for o in outliers:
        outlier_data.append({"x": i, "y": o, "endpoint": cat})

box_df = pd.DataFrame(box_data)
outlier_df = pd.DataFrame(outlier_data) if outlier_data else pd.DataFrame(columns=["x", "y", "endpoint"])
median_df = pd.DataFrame(median_data)

# Color palette - Python Blue gradient from dark to light
n_levels = box_df["level"].max() + 1 if len(box_df) > 0 else 1
# Create gradient from dark blue (#1a4971) to light blue (#a8d4f0)
colors = []
for i in range(n_levels):
    t = i / max(n_levels - 1, 1)  # Normalize to 0-1
    r = int(26 + t * (168 - 26))
    g = int(73 + t * (212 - 73))
    b = int(113 + t * (240 - 113))
    colors.append(f"#{r:02x}{g:02x}{b:02x}")

# Create the plot
plot = (
    ggplot()
    + geom_rect(
        data=box_df.sort_values("level", ascending=False),  # Draw outer boxes first
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="factor(level)"),
        color="#1a1a1a",
        size=0.3,
    )
    + geom_segment(data=median_df, mapping=aes(x="x - 0.35", xend="x + 0.35", y="y", yend="y"), color="white", size=1.5)
    + scale_fill_manual(
        values=colors,
        name="Quantile Level",
        labels=[f"{50 * (0.5 ** (i + 1)):.1f}%-{100 - 50 * (0.5 ** (i + 1)):.1f}%" for i in range(n_levels)],
    )
    + labs(title="boxen-basic · plotnine · pyplots.ai", x="Endpoint", y="Response Time (ms)")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_text_x=element_text(size=18),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid_major=element_line(alpha=0.3),
        panel_grid_minor=element_line(alpha=0.15),
    )
)

# Add outliers if present
if len(outlier_df) > 0:
    plot = plot + geom_point(data=outlier_df, mapping=aes(x="x", y="y"), color="#306998", size=2, alpha=0.5)

# Custom x-axis scale for category names
plot = plot + scale_x_continuous(breaks=list(range(len(categories))), labels=list(categories))

# Save the plot
plot.save("plot.png", dpi=300, width=16, height=9)

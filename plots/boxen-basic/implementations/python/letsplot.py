""" pyplots.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
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

# Data - Generate realistic response times for different server endpoints
np.random.seed(42)
endpoints = ["API Gateway", "Auth Service", "Database", "Cache Layer"]
n_per_group = 2000

data = []
# Realistic response time distributions (ms) with different characteristics
distributions = {
    "API Gateway": {"base": 45, "scale": 20, "skew": 0.5},
    "Auth Service": {"base": 80, "scale": 35, "skew": 0.8},
    "Database": {"base": 120, "scale": 50, "skew": 1.2},
    "Cache Layer": {"base": 8, "scale": 5, "skew": 0.3},
}

for endpoint in endpoints:
    d = distributions[endpoint]
    # Generate log-normal like distribution for realistic response times
    values = np.random.exponential(d["scale"], n_per_group) + d["base"]
    # Add occasional slow requests (tail)
    slow_idx = np.random.choice(n_per_group, size=int(n_per_group * 0.05), replace=False)
    values[slow_idx] = values[slow_idx] * np.random.uniform(2, 5, len(slow_idx))
    data.extend([(endpoint, v) for v in values])

df = pd.DataFrame(data, columns=["endpoint", "response_time"])


# Letter value names for legend
level_names = ["50%", "75%", "87.5%", "93.75%", "96.875%", "98.4%", "99.2%", "99.6%"]
level_colors = ["#306998", "#4A7FA8", "#6490B8", "#7EA1C8", "#98B2D8", "#B2C3E8", "#CCD4F8", "#E6E5FF"]


# Calculate letter values for boxen plot
def compute_letter_values(values, k=None):
    """Compute letter values (quantiles) for boxen plot."""
    n = len(values)
    if k is None:
        # Number of letter values based on data size
        k = int(np.log2(n)) - 1
        k = max(2, min(k, 8))

    sorted_vals = np.sort(values)
    letter_values = []

    for i in range(k):
        # Calculate the depth for each letter value
        depth = 0.5 ** (i + 1)
        lower_q = depth
        upper_q = 1 - depth

        lower_val = np.percentile(sorted_vals, lower_q * 100)
        upper_val = np.percentile(sorted_vals, upper_q * 100)
        letter_values.append((lower_val, upper_val, level_names[i]))

    # Calculate outlier bounds (beyond deepest letter value)
    deepest_lower = letter_values[-1][0]
    deepest_upper = letter_values[-1][1]
    outliers = sorted_vals[(sorted_vals < deepest_lower) | (sorted_vals > deepest_upper)]

    return letter_values, np.median(sorted_vals), outliers, k


# Compute letter values for each endpoint
box_data = []
median_data = []
outlier_data = []
max_k = 0

x_positions = {endpoint: i for i, endpoint in enumerate(endpoints)}

for endpoint in endpoints:
    group_data = df[df["endpoint"] == endpoint]["response_time"].values
    letter_vals, median, outliers, k = compute_letter_values(group_data)
    max_k = max(max_k, k)

    x_pos = x_positions[endpoint]

    for idx, (lower, upper, level_name) in enumerate(letter_vals):
        # Width decreases with depth
        half_width = 0.4 * (0.85**idx)
        box_data.append(
            {
                "x_min": x_pos - half_width,
                "x_max": x_pos + half_width,
                "y_min": lower,
                "y_max": upper,
                "level": level_name,
                "endpoint": endpoint,
            }
        )

    median_data.append({"x": x_pos - 0.38, "xend": x_pos + 0.38, "y": median, "endpoint": endpoint})

    for o in outliers:
        outlier_data.append({"x": x_pos, "y": o, "endpoint": endpoint})

box_df = pd.DataFrame(box_data)
median_df = pd.DataFrame(median_data)
outlier_df = pd.DataFrame(outlier_data) if outlier_data else pd.DataFrame(columns=["x", "y", "endpoint"])

# Plot using lets-plot
plot = (
    ggplot()
    + geom_rect(
        aes(xmin="x_min", xmax="x_max", ymin="y_min", ymax="y_max", fill="level"),
        data=box_df,
        alpha=0.9,
        color="#1a1a1a",
        size=0.5,
    )
    + geom_segment(aes(x="x", xend="xend", y="y", yend="y"), data=median_df, color="#FFD43B", size=3)
    + scale_fill_manual(
        values=dict(zip(level_names[:max_k], level_colors[:max_k], strict=False)), name="Quantile Range"
    )
    + scale_x_continuous(breaks=[0, 1, 2, 3], labels=endpoints)
    + labs(x="Server Endpoint", y="Response Time (ms)", title="boxen-basic \u00b7 letsplot \u00b7 pyplots.ai")
    + theme_minimal()
    + theme(
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
    )
    + ggsize(1600, 900)
)

# Add outliers if present
if not outlier_df.empty:
    plot = plot + geom_point(aes(x="x", y="y"), data=outlier_df, color="#DC2626", size=2, alpha=0.6)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")

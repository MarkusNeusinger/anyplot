""" pyplots.ai
ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-02-17
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rect,
    geom_segment,
    geom_step,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy import stats


# Data - credit scoring distributions
np.random.seed(42)
good_scores = np.random.beta(5, 2, 300) * 800 + 200
bad_scores = np.random.beta(2, 4, 300) * 800 + 200

# K-S test
ks_stat, p_value = stats.ks_2samp(good_scores, bad_scores)

# Compute ECDFs using vectorized approach
good_sorted = np.sort(good_scores)
bad_sorted = np.sort(bad_scores)
good_ecdf = np.arange(1, len(good_sorted) + 1) / len(good_sorted)
bad_ecdf = np.arange(1, len(bad_sorted) + 1) / len(bad_sorted)

# Find the point of maximum divergence
all_values = np.sort(np.concatenate([good_sorted, bad_sorted]))
good_cdf_at_all = np.searchsorted(good_sorted, all_values, side="right") / len(good_sorted)
bad_cdf_at_all = np.searchsorted(bad_sorted, all_values, side="right") / len(bad_sorted)
max_idx = np.argmax(np.abs(good_cdf_at_all - bad_cdf_at_all))
max_x = all_values[max_idx]
max_y_good = good_cdf_at_all[max_idx]
max_y_bad = bad_cdf_at_all[max_idx]
y_lo, y_hi = min(max_y_good, max_y_bad), max(max_y_good, max_y_bad)

# Build single DataFrame for ECDF step plots
df = pd.concat(
    [
        pd.DataFrame({"score": good_sorted, "ecdf": good_ecdf, "group": "Good Customers"}),
        pd.DataFrame({"score": bad_sorted, "ecdf": bad_ecdf, "group": "Bad Customers"}),
    ],
    ignore_index=True,
)

# Axis range
x_min, x_max = df["score"].min(), df["score"].max()
x_pad = (x_max - x_min) * 0.04

# Annotation DataFrames for geom layers
df_shade = pd.DataFrame({"xmin": [max_x - 22], "xmax": [max_x + 22], "ymin": [y_lo], "ymax": [y_hi]})
df_seg = pd.DataFrame({"x": [max_x], "xend": [max_x], "y": [y_lo], "yend": [y_hi]})

# Color palette
colors = {"Good Customers": "#306998", "Bad Customers": "#E8873D"}

# Plot
plot = (
    ggplot(df, aes(x="score", y="ecdf", color="group"))
    # Shaded region at max divergence - more prominent
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=df_shade,
        fill="#E74C3C",
        alpha=0.18,
        inherit_aes=False,
    )
    # Max divergence vertical line
    + geom_segment(
        aes(x="x", xend="xend", y="y", yend="yend"),
        data=df_seg,
        color="#C0392B",
        size=1.8,
        linetype="dashed",
        inherit_aes=False,
    )
    # ECDF step functions
    + geom_step(size=2)
    # D label near max divergence
    + annotate(
        "text",
        x=max_x + 22,
        y=(max_y_good + max_y_bad) / 2,
        label=f"D = {ks_stat:.3f}",
        size=15,
        ha="left",
        va="center",
        color="#C0392B",
        fontweight="bold",
    )
    # Statistical summary box - positioned to use empty lower-right space
    + annotate(
        "label",
        x=x_min + 0.52 * (x_max - x_min),
        y=0.07,
        label=f"K-S Statistic = {ks_stat:.3f}  |  p-value = {p_value:.2e}",
        size=13,
        ha="left",
        va="center",
        color="#C0392B",
        fontweight="bold",
        fill="#FDF2F0",
        alpha=0.92,
        label_size=0.8,
        boxstyle="round",
    )
    # Interpretive subtitle as annotation for data storytelling
    + annotate(
        "label",
        x=x_min + 0.50 * (x_max - x_min),
        y=1.06,
        label="Distributions are highly distinct (D > 0.5) — strong evidence the groups differ",
        size=11,
        ha="center",
        va="center",
        color="#555555",
        fontstyle="italic",
        fill="#FAFAFA",
        alpha=1.0,
        label_size=0,
        boxstyle="round",
    )
    + scale_color_manual(name="Distribution", values=colors)
    + scale_y_continuous(limits=(0, 1.10), breaks=np.arange(0, 1.1, 0.2))
    + scale_x_continuous(limits=(x_min - x_pad, x_max + x_pad * 3))
    + labs(
        x="Credit Score (points)", y="Cumulative Proportion (0–1)", title="ks-test-comparison · plotnine · pyplots.ai"
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, family="sans-serif"),
        axis_title_x=element_text(size=20, margin={"t": 14}),
        axis_title_y=element_text(size=20, margin={"r": 14}),
        axis_text=element_text(size=16, color="#444444"),
        plot_title=element_text(size=24, weight="bold", margin={"b": 4}),
        legend_title=element_text(size=18, weight="bold"),
        legend_text=element_text(size=16),
        legend_position=(0.18, 0.80),
        legend_background=element_rect(fill="white", color="#CCCCCC", alpha=0.9, size=0.4),
        legend_key=element_rect(fill="white", color="none"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", alpha=0.5, size=0.4),
        axis_line_x=element_line(color="#888888", size=0.5),
        axis_line_y=element_line(color="#888888", size=0.5),
        panel_border=element_blank(),
        plot_background=element_rect(fill="#FAFAFA", color="none"),
        plot_margin_top=0.02,
        plot_margin_right=0.04,
        plot_margin_bottom=0.02,
    )
)

# Save
plot.save("plot.png", dpi=300)

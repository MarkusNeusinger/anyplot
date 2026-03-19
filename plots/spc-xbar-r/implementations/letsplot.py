""" pyplots.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-19
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data - CNC shaft diameter measurements (subgroups of n=5)
np.random.seed(42)
n_samples = 30
target_diameter = 25.0  # mm
process_std = 0.05  # mm

# Generate subgroup measurements with a few out-of-control points
measurements = np.random.normal(target_diameter, process_std, (n_samples, 5))
# Inject shifts for out-of-control points
measurements[7] += 0.15  # Sudden shift up
measurements[18] -= 0.18  # Sudden shift down
measurements[24] += 0.12  # Another shift up

sample_ids = np.arange(1, n_samples + 1)
sample_means = measurements.mean(axis=1)
sample_ranges = measurements.max(axis=1) - measurements.min(axis=1)

# Control chart constants for n=5
A2 = 0.577
D3 = 0.0
D4 = 2.114

# X-bar chart limits
xbar_bar = sample_means.mean()
r_bar = sample_ranges.mean()
xbar_ucl = xbar_bar + A2 * r_bar
xbar_lcl = xbar_bar - A2 * r_bar
xbar_uwl = xbar_bar + (2 / 3) * A2 * r_bar  # +2 sigma warning
xbar_lwl = xbar_bar - (2 / 3) * A2 * r_bar  # -2 sigma warning

# R chart limits
r_ucl = D4 * r_bar
r_lcl = D3 * r_bar
r_uwl = r_bar + (2 / 3) * (r_ucl - r_bar)

# Identify out-of-control points
xbar_ooc = (sample_means > xbar_ucl) | (sample_means < xbar_lcl)
r_ooc = (sample_ranges > r_ucl) | (sample_ranges < r_lcl)

# DataFrames
df_xbar = pd.DataFrame(
    {"sample": sample_ids, "mean": sample_means, "status": np.where(xbar_ooc, "Out of Control", "In Control")}
)

df_r = pd.DataFrame(
    {"sample": sample_ids, "range": sample_ranges, "status": np.where(r_ooc, "Out of Control", "In Control")}
)

df_xbar_ooc = df_xbar[df_xbar["status"] == "Out of Control"]

# Limit line dataframes for X-bar
xbar_limits = pd.DataFrame(
    {
        "sample": np.tile([1, n_samples], 5),
        "y": [xbar_ucl] * 2 + [xbar_lcl] * 2 + [xbar_bar] * 2 + [xbar_uwl] * 2 + [xbar_lwl] * 2,
        "line": ["UCL"] * 2 + ["LCL"] * 2 + ["CL"] * 2 + ["UWL"] * 2 + ["LWL"] * 2,
    }
)

# Limit line dataframes for R chart
r_limits = pd.DataFrame(
    {
        "sample": np.tile([1, n_samples], 4),
        "y": [r_ucl] * 2 + [r_lcl] * 2 + [r_bar] * 2 + [r_uwl] * 2,
        "line": ["UCL"] * 2 + ["LCL"] * 2 + ["CL"] * 2 + ["UWL"] * 2,
    }
)

# Label positions - offset overlapping labels vertically to avoid collision
# UCL and UWL are close, LWL and LCL are close - nudge them apart
label_nudge = (xbar_ucl - xbar_lcl) * 0.06
xbar_labels = pd.DataFrame(
    {
        "sample": [n_samples + 0.5] * 5,
        "y": [
            xbar_ucl + label_nudge,  # UCL nudged up
            xbar_lcl - label_nudge,  # LCL nudged down
            xbar_bar,  # CL stays
            xbar_uwl - label_nudge,  # UWL nudged down (away from UCL)
            xbar_lwl + label_nudge,  # LWL nudged up (away from LCL)
        ],
        "label": ["UCL", "LCL", "CL", "UWL", "LWL"],
    }
)

r_label_nudge = (r_ucl - r_lcl) * 0.06
r_labels = pd.DataFrame(
    {
        "sample": [n_samples + 0.5] * 3,
        "y": [r_ucl + r_label_nudge, r_bar - r_label_nudge, r_uwl + r_label_nudge],
        "label": ["UCL", "R̄", "UWL"],
    }
)

# Colors - muted tones for limit lines, bold for data/OOC
blue = "#306998"
red_ooc = "#DC2626"
limit_color = "#9CA3AF"  # Muted gray for UCL/LCL
warning_color = "#D1D5DB"  # Lighter gray for UWL/LWL
center_color = "#6B7280"  # Medium gray for center line

# X-bar chart
xbar_plot = (
    ggplot()
    # Warning limit lines (muted)
    + geom_line(
        data=xbar_limits[xbar_limits["line"].isin(["UWL", "LWL"])],
        mapping=aes(x="sample", y="y", group="line"),
        linetype="dotted",
        color=warning_color,
        size=0.8,
    )
    # Control limit lines (muted)
    + geom_line(
        data=xbar_limits[xbar_limits["line"].isin(["UCL", "LCL"])],
        mapping=aes(x="sample", y="y", group="line"),
        linetype="dashed",
        color=limit_color,
        size=1.0,
    )
    # Center line
    + geom_line(
        data=xbar_limits[xbar_limits["line"] == "CL"],
        mapping=aes(x="sample", y="y", group="line"),
        linetype="solid",
        color=center_color,
        size=1.0,
    )
    # Data line
    + geom_line(data=df_xbar, mapping=aes(x="sample", y="mean"), color=blue, size=1.5)
    # In-control points
    + geom_point(
        data=df_xbar[df_xbar["status"] == "In Control"],
        mapping=aes(x="sample", y="mean"),
        color=blue,
        fill="white",
        size=5,
        shape=21,
        stroke=1.5,
    )
    # Out-of-control points
    + geom_point(
        data=df_xbar_ooc, mapping=aes(x="sample", y="mean"), color=red_ooc, fill=red_ooc, size=6, shape=21, stroke=1.5
    )
    # Limit labels
    + geom_text(
        data=xbar_labels,
        mapping=aes(x="sample", y="y", label="label"),
        size=13,
        color="#555555",
        fontface="bold",
        hjust=0,
    )
    + scale_x_continuous(breaks=list(range(1, n_samples + 1, 5)) + [n_samples], limits=[0.5, n_samples + 4.5])
    + labs(title="spc-xbar-r · letsplot · pyplots.ai", y="X̄ (Sample Mean, mm)", x="")
    + theme(
        plot_title=element_text(size=24, color="#222222", face="bold"),
        axis_title_y=element_text(size=20, color="#333333"),
        axis_text_y=element_text(size=16, color="#555555"),
        axis_text_x=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#EEEEEE", size=0.4),
        panel_background=element_rect(fill="white", color="white"),
        plot_background=element_rect(fill="white", color="white"),
        axis_line_x=element_line(color="#AAAAAA", size=0.8),
        axis_line_y=element_line(color="#AAAAAA", size=0.8),
        axis_ticks=element_line(color="#CCCCCC", size=0.4),
        legend_position="none",
        plot_margin=[30, 60, 5, 20],
    )
    + ggsize(1600, 500)
)

# R chart
r_plot = (
    ggplot()
    # Warning limit line (muted)
    + geom_line(
        data=r_limits[r_limits["line"] == "UWL"],
        mapping=aes(x="sample", y="y", group="line"),
        linetype="dotted",
        color=warning_color,
        size=0.8,
    )
    # Control limit lines (muted)
    + geom_line(
        data=r_limits[r_limits["line"].isin(["UCL", "LCL"])],
        mapping=aes(x="sample", y="y", group="line"),
        linetype="dashed",
        color=limit_color,
        size=1.0,
    )
    # Center line
    + geom_line(
        data=r_limits[r_limits["line"] == "CL"],
        mapping=aes(x="sample", y="y", group="line"),
        linetype="solid",
        color=center_color,
        size=1.0,
    )
    # Data line
    + geom_line(data=df_r, mapping=aes(x="sample", y="range"), color=blue, size=1.5)
    # In-control points
    + geom_point(
        data=df_r[df_r["status"] == "In Control"],
        mapping=aes(x="sample", y="range"),
        color=blue,
        fill="white",
        size=5,
        shape=21,
        stroke=1.5,
    )
    # Out-of-control points
    + geom_point(
        data=df_r[df_r["status"] == "Out of Control"],
        mapping=aes(x="sample", y="range"),
        color=red_ooc,
        fill=red_ooc,
        size=6,
        shape=21,
        stroke=1.5,
    )
    # Limit labels
    + geom_text(
        data=r_labels, mapping=aes(x="sample", y="y", label="label"), size=13, color="#555555", fontface="bold", hjust=0
    )
    + scale_x_continuous(breaks=list(range(1, n_samples + 1, 5)) + [n_samples], limits=[0.5, n_samples + 4.5])
    + labs(x="Sample Number", y="R (Sample Range, mm)")
    + theme(
        axis_title=element_text(size=20, color="#333333"),
        axis_text=element_text(size=16, color="#555555"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#EEEEEE", size=0.4),
        panel_background=element_rect(fill="white", color="white"),
        plot_background=element_rect(fill="white", color="white"),
        axis_line_x=element_line(color="#AAAAAA", size=0.8),
        axis_line_y=element_line(color="#AAAAAA", size=0.8),
        axis_ticks=element_line(color="#CCCCCC", size=0.4),
        legend_position="none",
        plot_margin=[5, 60, 30, 20],
    )
    + ggsize(1600, 400)
)

# Add tooltip layers for HTML interactivity (lets-plot distinctive feature)
xbar_plot_interactive = xbar_plot + geom_point(
    data=df_xbar,
    mapping=aes(x="sample", y="mean"),
    size=5,
    alpha=0.01,
    tooltips=layer_tooltips().line("Sample|@sample").line("X̄|@mean").line("Status|@status").format("mean", ".4f"),
)

r_plot_interactive = r_plot + geom_point(
    data=df_r,
    mapping=aes(x="sample", y="range"),
    size=5,
    alpha=0.01,
    tooltips=layer_tooltips().line("Sample|@sample").line("Range|@range").line("Status|@status").format("range", ".4f"),
)

# Combine X-bar and R charts
combined = gggrid([xbar_plot, r_plot], ncol=1, heights=[0.55, 0.45])
combined_interactive = gggrid([xbar_plot_interactive, r_plot_interactive], ncol=1, heights=[0.55, 0.45])

# Save
ggsave(combined, "plot.png", scale=3, path=".")
ggsave(combined_interactive, "plot.html", path=".")

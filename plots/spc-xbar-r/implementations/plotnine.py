""" pyplots.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-19
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    facet_wrap,
    geom_hline,
    geom_label,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_identity,
    scale_shape_identity,
    scale_size_identity,
    scale_x_continuous,
    theme,
    theme_minimal,
)


# Data — CNC shaft diameter measurements, subgroups of n=5
np.random.seed(42)
n_samples = 30
subgroup_size = 5

# Control chart constants for n=5
A2 = 0.577
D3 = 0.0
D4 = 2.114

# Generate realistic process data (target diameter: 25.00 mm)
target = 25.0
process_std = 0.02
measurements = np.random.normal(target, process_std, (n_samples, subgroup_size))

# Inject out-of-control points
measurements[7] += 0.06  # Shift up
measurements[18] -= 0.07  # Shift down
measurements[24] += np.array([0.1, -0.08, 0.09, -0.07, 0.1])  # High variability

sample_means = measurements.mean(axis=1)
sample_ranges = measurements.max(axis=1) - measurements.min(axis=1)

# Control limits
xbar_bar = sample_means.mean()
r_bar = sample_ranges.mean()

xbar_ucl = xbar_bar + A2 * r_bar
xbar_lcl = xbar_bar - A2 * r_bar
xbar_uwl = xbar_bar + (2 / 3) * A2 * r_bar
xbar_lwl = xbar_bar - (2 / 3) * A2 * r_bar

r_ucl = D4 * r_bar
r_lcl = D3 * r_bar
r_uwl = r_bar + (2 / 3) * (r_ucl - r_bar)
r_lwl = max(0, r_bar - (2 / 3) * (r_bar - r_lcl))

# Build long-format dataframe for faceting
sample_ids = np.arange(1, n_samples + 1)

xbar_ooc = (sample_means > xbar_ucl) | (sample_means < xbar_lcl)
r_ooc = (sample_ranges > r_ucl) | (sample_ranges < r_lcl)

xbar_df = pd.DataFrame(
    {"sample": sample_ids, "value": sample_means, "chart": "X\u0304 Chart · Sample Mean (mm)", "ooc": xbar_ooc}
)

r_df = pd.DataFrame(
    {"sample": sample_ids, "value": sample_ranges, "chart": "R Chart · Sample Range (mm)", "ooc": r_ooc}
)

df = pd.concat([xbar_df, r_df], ignore_index=True)
df["color"] = np.where(df["ooc"], "#C44E52", "#306998")
df["point_size"] = np.where(df["ooc"], 6, 4)
df["point_shape"] = np.where(df["ooc"], "D", "o")

chart_order = ["X\u0304 Chart · Sample Mean (mm)", "R Chart · Sample Range (mm)"]
df["chart"] = pd.Categorical(df["chart"], categories=chart_order, ordered=True)

# Colorblind-safe palette
cl_color = "#4C72B0"  # Steel blue for center line
limit_color = "#C44E52"  # Muted red for UCL/LCL
warn_color = "#DD8452"  # Amber for warning limits

# Control limit lines for each chart
limit_lines = pd.DataFrame(
    [
        {"chart": chart_order[0], "yintercept": xbar_ucl, "ltype": "UCL", "color": limit_color},
        {"chart": chart_order[0], "yintercept": xbar_lcl, "ltype": "LCL", "color": limit_color},
        {"chart": chart_order[0], "yintercept": xbar_bar, "ltype": "CL", "color": cl_color},
        {"chart": chart_order[0], "yintercept": xbar_uwl, "ltype": "UWL", "color": warn_color},
        {"chart": chart_order[0], "yintercept": xbar_lwl, "ltype": "LWL", "color": warn_color},
        {"chart": chart_order[1], "yintercept": r_ucl, "ltype": "UCL", "color": limit_color},
        {"chart": chart_order[1], "yintercept": r_bar, "ltype": "CL", "color": cl_color},
        {"chart": chart_order[1], "yintercept": r_uwl, "ltype": "UWL", "color": warn_color},
        {"chart": chart_order[1], "yintercept": r_lwl, "ltype": "LWL", "color": warn_color},
    ]
)
limit_lines["chart"] = pd.Categorical(limit_lines["chart"], categories=chart_order, ordered=True)

# Also need LCL=0 line for R chart (even if no label)
r_lcl_line = pd.DataFrame([{"chart": chart_order[1], "yintercept": r_lcl, "ltype": "LCL", "color": limit_color}])
r_lcl_line["chart"] = pd.Categorical(r_lcl_line["chart"], categories=chart_order, ordered=True)

all_lines = pd.concat([limit_lines, r_lcl_line], ignore_index=True)
cl_lines = all_lines[all_lines["ltype"] == "CL"]
ucl_lcl_lines = all_lines[all_lines["ltype"].isin(["UCL", "LCL"])]
warn_lines = all_lines[all_lines["ltype"].isin(["UWL", "LWL"])]

# Labels placed at left edge of chart — avoids right-side crowding
label_df = limit_lines.copy()  # Excludes R chart LCL=0
label_df["sample"] = 0.0  # Left position

# De-overlap labels within each chart panel
for chart_name in chart_order:
    mask = label_df["chart"] == chart_name
    chart_labels = label_df.loc[mask].sort_values("yintercept")
    if len(chart_labels) < 2:
        label_df.loc[chart_labels.index, "y_label"] = chart_labels["yintercept"].values
        continue
    vals = chart_labels["yintercept"].values
    chart_range = vals[-1] - vals[0]
    min_gap = chart_range * 0.15

    adjusted = vals.copy()
    for i in range(1, len(adjusted)):
        if adjusted[i] - adjusted[i - 1] < min_gap:
            adjusted[i] = adjusted[i - 1] + min_gap
    offset = np.mean(vals) - np.mean(adjusted)
    adjusted += offset
    label_df.loc[chart_labels.index, "y_label"] = adjusted

label_df["fill"] = "#fafafa"

# Plot
plot = (
    ggplot(df, aes(x="sample", y="value"))
    # Control lines
    + geom_hline(aes(yintercept="yintercept", color="color"), data=cl_lines, size=1.3, linetype="solid")
    + geom_hline(aes(yintercept="yintercept", color="color"), data=ucl_lcl_lines, size=1.0, linetype="dashed")
    + geom_hline(aes(yintercept="yintercept", color="color"), data=warn_lines, size=0.7, linetype="dotted", alpha=0.7)
    # Data line and points
    + geom_line(color="#306998", size=1.2, alpha=0.5)
    + geom_point(aes(color="color", size="point_size", shape="point_shape"), stroke=0.8)
    # Left-edge labels with background for readability
    + geom_label(
        aes(x="sample", y="y_label", label="ltype", color="color", fill="fill"),
        data=label_df,
        size=9,
        ha="right",
        fontweight="bold",
        label_size=0,
        alpha=0.85,
    )
    # Scales
    + scale_color_identity()
    + scale_size_identity()
    + scale_shape_identity()
    + scale_fill_identity()
    + scale_x_continuous(breaks=range(1, n_samples + 1, 2), limits=(-1.5, n_samples + 0.5))
    + facet_wrap("chart", ncol=1, scales="free_y")
    + labs(
        x="Sample Number",
        y="Measurement (mm)",
        title="CNC Shaft Diameter Monitoring · spc-xbar-r · plotnine · pyplots.ai",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 10),
        text=element_text(size=14, color="#2a2a2a"),
        axis_title=element_text(size=20, weight="bold"),
        axis_text=element_text(size=16, color="#444444"),
        plot_title=element_text(size=24, weight="bold", color="#1a1a1a"),
        strip_text=element_text(size=18, weight="bold", color="#1a1a1a"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#e0e0e0", size=0.3),
        panel_spacing_y=0.25,
        axis_line=element_line(color="#333333", size=0.6),
        plot_background=element_rect(fill="#fafafa", color="none"),
        panel_background=element_rect(fill="#fafafa", color="none"),
        strip_background=element_rect(fill="#e8e8e8", color="#cccccc", size=0.3),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)

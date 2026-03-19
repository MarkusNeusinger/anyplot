"""pyplots.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-19
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
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_identity,
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

xbar_df = pd.DataFrame({"sample": sample_ids, "value": sample_means, "chart": "X̄ Chart (Sample Mean)", "ooc": xbar_ooc})

r_df = pd.DataFrame({"sample": sample_ids, "value": sample_ranges, "chart": "R Chart (Sample Range)", "ooc": r_ooc})

df = pd.concat([xbar_df, r_df], ignore_index=True)
df["color"] = np.where(df["ooc"], "#D62728", "#306998")
df["point_size"] = np.where(df["ooc"], 5, 3)
df["point_shape"] = np.where(df["ooc"], "D", "o")

chart_order = ["X̄ Chart (Sample Mean)", "R Chart (Sample Range)"]
df["chart"] = pd.Categorical(df["chart"], categories=chart_order, ordered=True)

# Control limit lines for each chart
limit_lines = pd.DataFrame(
    [
        {"chart": "X̄ Chart (Sample Mean)", "yintercept": xbar_ucl, "ltype": "UCL", "color": "#D62728"},
        {"chart": "X̄ Chart (Sample Mean)", "yintercept": xbar_lcl, "ltype": "LCL", "color": "#D62728"},
        {"chart": "X̄ Chart (Sample Mean)", "yintercept": xbar_bar, "ltype": "CL", "color": "#2CA02C"},
        {"chart": "X̄ Chart (Sample Mean)", "yintercept": xbar_uwl, "ltype": "UWL", "color": "#FF7F0E"},
        {"chart": "X̄ Chart (Sample Mean)", "yintercept": xbar_lwl, "ltype": "LWL", "color": "#FF7F0E"},
        {"chart": "R Chart (Sample Range)", "yintercept": r_ucl, "ltype": "UCL", "color": "#D62728"},
        {"chart": "R Chart (Sample Range)", "yintercept": r_lcl, "ltype": "LCL", "color": "#D62728"},
        {"chart": "R Chart (Sample Range)", "yintercept": r_bar, "ltype": "CL", "color": "#2CA02C"},
        {"chart": "R Chart (Sample Range)", "yintercept": r_uwl, "ltype": "UWL", "color": "#FF7F0E"},
        {"chart": "R Chart (Sample Range)", "yintercept": r_lwl, "ltype": "LWL", "color": "#FF7F0E"},
    ]
)
limit_lines["chart"] = pd.Categorical(limit_lines["chart"], categories=chart_order, ordered=True)

cl_lines = limit_lines[limit_lines["ltype"] == "CL"]
ucl_lcl_lines = limit_lines[limit_lines["ltype"].isin(["UCL", "LCL"])]
warn_lines = limit_lines[limit_lines["ltype"].isin(["UWL", "LWL"])]

# Plot
plot = (
    ggplot(df, aes(x="sample", y="value"))
    + geom_hline(aes(yintercept="yintercept", color="color"), data=cl_lines, size=1.2, linetype="solid")
    + geom_hline(aes(yintercept="yintercept", color="color"), data=ucl_lcl_lines, size=1.0, linetype="dashed")
    + geom_hline(aes(yintercept="yintercept", color="color"), data=warn_lines, size=0.7, linetype="dotted", alpha=0.7)
    + geom_line(color="#306998", size=1.2, alpha=0.6)
    + geom_point(aes(color="color", size="point_size", shape="point_shape"), stroke=0.8)
    + scale_color_identity()
    + scale_size_identity()
    + scale_shape_identity()
    + scale_x_continuous(breaks=range(1, n_samples + 1, 2))
    + facet_wrap("chart", ncol=1, scales="free_y")
    + labs(x="Sample Number", y="Value", title="CNC Shaft Diameter Monitoring · spc-xbar-r · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 12),
        text=element_text(size=14, color="#2a2a2a"),
        axis_title=element_text(size=20, weight="bold"),
        axis_text=element_text(size=16, color="#444444"),
        plot_title=element_text(size=22, weight="bold", color="#1a1a1a"),
        strip_text=element_text(size=18, weight="bold", color="#1a1a1a"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#e0e0e0", size=0.4),
        panel_spacing_y=0.4,
        axis_line=element_line(color="#333333", size=0.6),
        plot_background=element_rect(fill="#fafafa", color="none"),
        panel_background=element_rect(fill="#fafafa", color="none"),
        strip_background=element_rect(fill="#eeeeee", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)

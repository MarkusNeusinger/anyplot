"""anyplot.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 78/100 | Updated: 2026-06-20
"""

import os
import sys


# Prevent this file from shadowing the installed plotnine package
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _script_dir]

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


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette assignments
TEAL = "#009E73"  # Imprint[0] — primary data line / in-control points
BLUE = "#4467A3"  # Imprint[2] — center line
RED = "#AE3030"  # Imprint[4] — UCL/LCL limits and out-of-control points
AMBER = "#DDCC77"  # ANYPLOT_AMBER — warning limits (±2σ)

# Data — CNC shaft diameter measurements, subgroups of n=5
np.random.seed(42)
n_samples = 30
subgroup_size = 5

# Control chart constants for n=5
A2 = 0.577
D3 = 0.0
D4 = 2.114

target = 25.0
process_std = 0.02
measurements = np.random.normal(target, process_std, (n_samples, subgroup_size))

# Inject out-of-control signals
measurements[7] += 0.06  # Upward mean shift
measurements[18] -= 0.07  # Downward mean shift
measurements[24] += np.array([0.06, -0.05, 0.06, -0.05, 0.06])  # Elevated variability

sample_means = measurements.mean(axis=1)
sample_ranges = measurements.max(axis=1) - measurements.min(axis=1)

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

sample_ids = np.arange(1, n_samples + 1)
xbar_ooc = (sample_means > xbar_ucl) | (sample_means < xbar_lcl)
r_ooc = (sample_ranges > r_ucl) | (sample_ranges < r_lcl)

CHART_XBAR = "X̄ Chart · Sample Mean (mm)"
CHART_R = "R Chart · Sample Range (mm)"
chart_order = [CHART_XBAR, CHART_R]

xbar_df = pd.DataFrame({"sample": sample_ids, "value": sample_means, "chart": CHART_XBAR, "ooc": xbar_ooc})
r_df = pd.DataFrame({"sample": sample_ids, "value": sample_ranges, "chart": CHART_R, "ooc": r_ooc})
df = pd.concat([xbar_df, r_df], ignore_index=True)
df["color"] = np.where(df["ooc"], RED, TEAL)
df["point_size"] = np.where(df["ooc"], 4.0, 2.5)
df["point_shape"] = np.where(df["ooc"], "D", "o")
df["chart"] = pd.Categorical(df["chart"], categories=chart_order, ordered=True)

# Control limit lines — limit_lines excludes R chart LCL=0 so labels don't appear at y=0
limit_rows = [
    {"chart": CHART_XBAR, "yintercept": xbar_ucl, "ltype": "UCL", "color": RED},
    {"chart": CHART_XBAR, "yintercept": xbar_lcl, "ltype": "LCL", "color": RED},
    {"chart": CHART_XBAR, "yintercept": xbar_bar, "ltype": "CL", "color": BLUE},
    {"chart": CHART_XBAR, "yintercept": xbar_uwl, "ltype": "UWL", "color": AMBER},
    {"chart": CHART_XBAR, "yintercept": xbar_lwl, "ltype": "LWL", "color": AMBER},
    {"chart": CHART_R, "yintercept": r_ucl, "ltype": "UCL", "color": RED},
    {"chart": CHART_R, "yintercept": r_bar, "ltype": "CL", "color": BLUE},
    {"chart": CHART_R, "yintercept": r_uwl, "ltype": "UWL", "color": AMBER},
    {"chart": CHART_R, "yintercept": r_lwl, "ltype": "LWL", "color": AMBER},
]
limit_lines = pd.DataFrame(limit_rows)
limit_lines["chart"] = pd.Categorical(limit_lines["chart"], categories=chart_order, ordered=True)

# R chart LCL at y=0 — rendered as dashed line only, no label
r_lcl_row = pd.DataFrame([{"chart": CHART_R, "yintercept": r_lcl, "ltype": "LCL", "color": RED}])
r_lcl_row["chart"] = pd.Categorical(r_lcl_row["chart"], categories=chart_order, ordered=True)

all_lines = pd.concat([limit_lines, r_lcl_row], ignore_index=True)
cl_lines = all_lines[all_lines["ltype"] == "CL"]
ucl_lcl_lines = all_lines[all_lines["ltype"].isin(["UCL", "LCL"])]
warn_lines = all_lines[all_lines["ltype"].isin(["UWL", "LWL"])]

# Right-edge labels with de-overlap logic to reduce crowding
label_df = limit_lines.copy()
label_df["sample"] = n_samples + 0.5

for chart_name in chart_order:
    mask = label_df["chart"] == chart_name
    chart_labels = label_df.loc[mask].sort_values("yintercept")
    vals = chart_labels["yintercept"].values
    if len(vals) < 2:
        label_df.loc[chart_labels.index, "y_label"] = vals
        continue
    chart_range = vals[-1] - vals[0]
    min_gap = chart_range * 0.30

    adjusted = vals.copy().astype(float)
    for i in range(1, len(adjusted)):
        if adjusted[i] - adjusted[i - 1] < min_gap:
            adjusted[i] = adjusted[i - 1] + min_gap
    offset = np.mean(vals) - np.mean(adjusted)
    adjusted += offset
    label_df.loc[chart_labels.index, "y_label"] = adjusted

label_df["fill"] = ELEVATED_BG

# Plot
plot = (
    ggplot(df, aes(x="sample", y="value"))
    + geom_hline(aes(yintercept="yintercept", color="color"), data=cl_lines, size=1.2, linetype="solid")
    + geom_hline(aes(yintercept="yintercept", color="color"), data=ucl_lcl_lines, size=0.9, linetype="dashed")
    + geom_hline(aes(yintercept="yintercept", color="color"), data=warn_lines, size=0.6, linetype="dotted", alpha=0.85)
    + geom_line(color=TEAL, size=0.9, alpha=0.55)
    + geom_point(aes(color="color", size="point_size", shape="point_shape"), stroke=0.8)
    + geom_label(
        aes(x="sample", y="y_label", label="ltype", color="color", fill="fill"),
        data=label_df,
        size=3,
        ha="right",
        fontweight="bold",
        label_size=0,
        alpha=0.9,
    )
    + scale_color_identity()
    + scale_size_identity()
    + scale_shape_identity()
    + scale_fill_identity()
    + scale_x_continuous(breaks=range(1, n_samples + 1, 2), limits=(-2.0, n_samples + 0.5))
    + facet_wrap("chart", ncol=1, scales="free_y")
    + labs(
        x="Sample Number",
        y="Measurement (mm)",
        title="CNC Shaft Diameter Monitoring · spc-xbar-r · python · plotnine · anyplot.ai",
    )
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7, color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, weight="bold", color=INK),
        strip_text=element_text(size=9, weight="bold", color=INK),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color=INK, size=0.3, alpha=0.15),
        panel_spacing_y=0.05,
        axis_line=element_line(color=INK_SOFT, size=0.6),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        strip_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.3),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)

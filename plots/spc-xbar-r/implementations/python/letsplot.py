"""anyplot.ai
spc-xbar-r: Statistical Process Control Chart (X-bar/R)
Library: letsplot 4.10.1 | Python 3.13.14
Quality: pending | Updated: 2026-06-20
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette (canonical order); position 1 is always the first series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
DATA_COLOR = IMPRINT_PALETTE[0]
OOC_COLOR = IMPRINT_PALETTE[4]  # semantic red for out-of-control

# Constants: control chart constants for subgroups of n=5
SUBGROUP_SIZE = 5
A2 = 0.577
D3 = 0.0
D4 = 2.114

# Column names, written the way the axis titles read
SAMPLE = "Sample Number"  # role: sample_id
MEAN = "X̄ (Sample Mean, mm)"  # role: sample_mean
RANGE = "R (Sample Range, mm)"  # role: sample_range
UCL = "X̄ Upper Control Limit (mm)"  # role: ucl
LCL = "X̄ Lower Control Limit (mm)"  # role: lcl
CENTER = "X̄ Center Line (mm)"  # role: center_line

# Data: CNC shaft diameters in subgroups of 5; replace this block with your own table of
# per-sample mean, range and limits, for example df = pd.read_csv("samples.csv")
np.random.seed(42)
n_samples = 30
target_diameter = 25.0  # mm
process_std = 0.05  # mm
measurements = np.random.normal(target_diameter, process_std, (n_samples, SUBGROUP_SIZE))

# Inject mean shifts for X-bar out-of-control points
measurements[7] += 0.15  # sudden upward shift
measurements[18] -= 0.18  # sudden downward shift
measurements[24] += 0.12  # upward drift

# Inject extreme spread for R chart OOC at sample 12 (preserves mean, inflates range)
measurements[11, 0] -= 0.16
measurements[11, 4] += 0.16

sample_means = measurements.mean(axis=1)
sample_ranges = measurements.max(axis=1) - measurements.min(axis=1)
grand_mean = sample_means.mean()
mean_range = sample_ranges.mean()
df = pd.DataFrame(
    {
        SAMPLE: np.arange(1, n_samples + 1),
        MEAN: sample_means,
        RANGE: sample_ranges,
        UCL: grand_mean + A2 * mean_range,
        LCL: grand_mean - A2 * mean_range,
        CENTER: grand_mean,
    }
)

# Plot
first, last = int(df[SAMPLE].min()), int(df[SAMPLE].max())
xbar_ucl, xbar_lcl, xbar_bar = df[UCL].iloc[0], df[LCL].iloc[0], df[CENTER].iloc[0]
r_bar = df[RANGE].mean()
r_ucl = D4 * r_bar
r_lcl = D3 * r_bar

# Warning limits at +-2 sigma (2/3 of the control limit distance)
xbar_uwl = xbar_bar + (2 / 3) * (xbar_ucl - xbar_bar)
xbar_lwl = xbar_bar - (2 / 3) * (xbar_bar - xbar_lcl)
r_uwl = r_bar + (2 / 3) * (r_ucl - r_bar)

# Classify in-control vs out-of-control
STATUS = "Status"
IN_CONTROL, OUT_OF_CONTROL = "In Control", "Out of Control"
xbar_signal = (df[MEAN] > df[UCL]) | (df[MEAN] < df[LCL])
df_xbar = df[[SAMPLE, MEAN]].copy()
df_xbar[STATUS] = np.where(xbar_signal, OUT_OF_CONTROL, IN_CONTROL)
df_r = df[[SAMPLE, RANGE]].copy()
df_r[STATUS] = np.where(df[RANGE] > r_ucl, OUT_OF_CONTROL, IN_CONTROL)

# Limit line dataframes (each line = 2 rows: start and end sample)
LIMIT_Y, LIMIT_LINE, LABEL = "y", "line", "label"


def limit_lines(levels):
    return pd.DataFrame(
        {
            SAMPLE: np.tile([first, last], len(levels)),
            LIMIT_Y: np.repeat(list(levels.values()), 2),
            LIMIT_LINE: np.repeat(list(levels.keys()), 2),
        }
    )


xbar_limits = limit_lines({"UCL": xbar_ucl, "LCL": xbar_lcl, "CL": xbar_bar, "UWL": xbar_uwl, "LWL": xbar_lwl})
r_limits = limit_lines({"UCL": r_ucl, "LCL": r_lcl, "CL": r_bar, "UWL": r_uwl})

# Label annotations placed just past the last data point (within the x-axis range)
label_x = last + 1
xbar_labels = pd.DataFrame(
    {SAMPLE: [label_x] * 3, LIMIT_Y: [xbar_ucl, xbar_bar, xbar_lcl], LABEL: ["UCL", "CL", "LCL"]}
)
r_labels = pd.DataFrame({SAMPLE: [label_x] * 3, LIMIT_Y: [r_ucl, r_bar, r_lcl], LABEL: ["UCL", "R̄", "LCL"]})
x_breaks = list(range(first, last + 1, 5)) + [last]
x_limits = [first - 0.5, last + 4.5]

# Shared chrome for both panels; the panel border is removed so the axis lines form an L
chrome = dict(
    panel_border=element_blank(),
    panel_grid_major_x=element_blank(),
    panel_grid_minor=element_blank(),
    panel_grid_major_y=element_line(color=INK_SOFT, size=0.25),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    axis_line_x=element_line(color=INK_SOFT, size=0.6),
    axis_line_y=element_line(color=INK_SOFT, size=0.6),
    axis_ticks=element_line(color=INK_SOFT, size=0.3),
    legend_position="none",
)

# Top panel (X-bar chart): title here, no x-axis labels
theme_top = theme(
    plot_title=element_text(size=16, color=INK, face="bold"),
    axis_title_y=element_text(size=12, color=INK),
    axis_text_y=element_text(size=10, color=INK_SOFT),
    axis_text_x=element_blank(),
    axis_title_x=element_blank(),
    plot_margin=[20, 50, 5, 15],
    **chrome,
)

# Bottom panel (R chart): x-axis labels here
theme_bottom = theme(
    axis_title=element_text(size=12, color=INK),
    axis_text=element_text(size=10, color=INK_SOFT),
    plot_margin=[5, 50, 20, 15],
    **chrome,
)


def control_chart(values, limits, labels, y_col, y_title, status, height):
    """One control-chart panel: limit lines, data line, status points, limit labels."""
    uwl_lwl = limits[LIMIT_LINE].isin(["UWL", "LWL"])
    ucl_lcl = limits[LIMIT_LINE].isin(["UCL", "LCL"])
    ok = values[STATUS] == IN_CONTROL
    return (
        ggplot()
        + geom_line(
            data=limits[uwl_lwl],
            mapping=aes(x=SAMPLE, y=LIMIT_Y, group=LIMIT_LINE),
            linetype="dotted",
            color=INK_MUTED,
            size=0.8,
        )
        + geom_line(
            data=limits[ucl_lcl],
            mapping=aes(x=SAMPLE, y=LIMIT_Y, group=LIMIT_LINE),
            linetype="dashed",
            color=INK_SOFT,
            size=1.0,
        )
        + geom_line(
            data=limits[limits[LIMIT_LINE] == "CL"],
            mapping=aes(x=SAMPLE, y=LIMIT_Y),
            linetype="solid",
            color=INK,
            size=0.9,
        )
        + geom_line(data=values, mapping=aes(x=SAMPLE, y=y_col), color=DATA_COLOR, size=1.5)
        + geom_point(
            data=values[ok],
            mapping=aes(x=SAMPLE, y=y_col),
            color=DATA_COLOR,
            fill=PAGE_BG,
            size=5,
            shape=21,
            stroke=1.5,
        )
        + geom_point(
            data=values[~ok],
            mapping=aes(x=SAMPLE, y=y_col),
            color=OOC_COLOR,
            fill=OOC_COLOR,
            size=6,
            shape=21,
            stroke=1.5,
        )
        + geom_text(
            data=labels,
            mapping=aes(x=SAMPLE, y=LIMIT_Y, label=LABEL),
            size=5.5,
            color=INK_SOFT,
            fontface="bold",
            hjust=0,
        )
        + scale_x_continuous(breaks=x_breaks, limits=x_limits)
        + scale_y_continuous(expand=[0.12, 0])
        + labs(y=y_title, x=SAMPLE)
        + ggsize(800, height)
    )


xbar_plot = (
    control_chart(df_xbar, xbar_limits, xbar_labels, MEAN, MEAN, STATUS, 260)
    + labs(title="spc-xbar-r · python · letsplot · anyplot.ai")
    + theme_top
)
r_plot = control_chart(df_r, r_limits, r_labels, RANGE, RANGE, STATUS, 190) + theme_bottom


def hover_points(plot, y_col):
    """Invisible points that carry the tooltips of the interactive HTML export."""
    tips = layer_tooltips().line(f"Sample|@{{{SAMPLE}}}").line(f"Value|@{{{y_col}}}").line(f"Status|@{STATUS}")
    return plot + geom_point(
        data=df_xbar if y_col == MEAN else df_r, mapping=aes(x=SAMPLE, y=y_col), size=5, alpha=0.01, tooltips=tips
    )


# Combine top (X-bar, 260) + bottom (R, 190) = 800x450 logical -> 3200x1800 at scale=4;
# the composite carries the page color, otherwise its margin is painted white
page = theme(plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG))
combined = gggrid([xbar_plot, r_plot], ncol=1) + ggsize(800, 450) + page
combined_interactive = (
    gggrid([hover_points(xbar_plot, MEAN), hover_points(r_plot, RANGE)], ncol=1) + ggsize(800, 450) + page
)

# Save
ggsave(combined, f"plot-{THEME}.png", scale=4, path=".")
ggsave(combined_interactive, f"plot-{THEME}.html", path=".")

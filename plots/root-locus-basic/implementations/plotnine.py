""" pyplots.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    arrow,
    coord_fixed,
    element_blank,
    element_line,
    element_text,
    geom_hline,
    geom_path,
    geom_point,
    geom_segment,
    geom_vline,
    ggplot,
    labs,
    scale_color_manual,
    theme,
    theme_minimal,
)


# Data - Transfer function G(s) = 1 / [s(s+1)(s+3)]
# Open-loop poles at s = 0, -1, -3; no zeros
# Characteristic equation: s^3 + 4s^2 + 3s + K = 0
open_loop_poles = np.array([0.0, -1.0, -3.0])
open_loop_zeros = np.array([])

num_coeffs = np.array([1.0])
den_coeffs = np.poly(open_loop_poles)

gains = np.concatenate(
    [
        np.linspace(0, 0.5, 200),
        np.linspace(0.5, 2, 300),
        np.linspace(2, 6, 400),
        np.linspace(6, 20, 400),
        np.linspace(20, 80, 300),
    ]
)

branch_data = []
for K in gains:
    char_eq = den_coeffs.copy()
    char_eq[-1] += K * num_coeffs[-1]
    roots = np.roots(char_eq)
    roots = np.sort_complex(roots)
    for branch_idx, root in enumerate(roots):
        branch_data.append({"real": root.real, "imaginary": root.imag, "gain": K, "branch": f"Branch {branch_idx + 1}"})

df = pd.DataFrame(branch_data)

# Find imaginary axis crossings (stability boundary)
crossings = []
for branch in df["branch"].unique():
    branch_df = df[df["branch"] == branch].reset_index(drop=True)
    for i in range(1, len(branch_df)):
        r0 = branch_df.loc[i - 1, "real"]
        r1 = branch_df.loc[i, "real"]
        if r0 * r1 < 0:
            frac = abs(r0) / (abs(r0) + abs(r1))
            cross_imag = branch_df.loc[i - 1, "imaginary"] + frac * (
                branch_df.loc[i, "imaginary"] - branch_df.loc[i - 1, "imaginary"]
            )
            cross_gain = branch_df.loc[i - 1, "gain"] + frac * (branch_df.loc[i, "gain"] - branch_df.loc[i - 1, "gain"])
            crossings.append({"real": 0.0, "imaginary": cross_imag, "gain": cross_gain})

# Real axis segments: to the left of an odd number of real poles+zeros
real_features = np.sort(np.concatenate([open_loop_poles, open_loop_zeros]))
real_axis_segments = []
x_min_axis = -5.0
test_points = np.linspace(x_min_axis, 1.0, 2000)
for x in test_points:
    count = np.sum(real_features >= x)
    if count % 2 == 1:
        real_axis_segments.append(x)

# Build segment intervals
seg_intervals = []
if len(real_axis_segments) > 0:
    seg_start = real_axis_segments[0]
    for i in range(1, len(real_axis_segments)):
        if real_axis_segments[i] - real_axis_segments[i - 1] > 0.01:
            seg_intervals.append((seg_start, real_axis_segments[i - 1]))
            seg_start = real_axis_segments[i]
    seg_intervals.append((seg_start, real_axis_segments[-1]))

seg_df = pd.DataFrame(seg_intervals, columns=["x_start", "x_end"])
seg_df["y"] = 0.0

# Arrow indicators for direction of increasing gain
arrows = []
for branch in df["branch"].unique():
    branch_df = df[df["branch"] == branch].reset_index(drop=True)
    mid_idx = len(branch_df) // 3
    if mid_idx > 0:
        arrows.append(
            {
                "x": branch_df.loc[mid_idx - 1, "real"],
                "y": branch_df.loc[mid_idx - 1, "imaginary"],
                "xend": branch_df.loc[mid_idx, "real"],
                "yend": branch_df.loc[mid_idx, "imaginary"],
            }
        )

arrow_df = pd.DataFrame(arrows)

# Poles and zeros markers
pole_df = pd.DataFrame({"real": open_loop_poles, "imaginary": np.zeros(len(open_loop_poles)), "type": "Pole"})

crossing_df = pd.DataFrame(crossings)

# Damping ratio lines
damping_ratios = [0.2, 0.4, 0.6, 0.8]
damp_lines = []
radius = 5.0
for zeta in damping_ratios:
    angle = np.arccos(zeta)
    x_end = -radius * np.cos(np.pi - angle)
    y_end_pos = radius * np.sin(np.pi - angle)
    damp_lines.append({"x": 0, "y": 0, "xend": x_end, "yend": y_end_pos, "label": f"ζ={zeta}"})
    damp_lines.append({"x": 0, "y": 0, "xend": x_end, "yend": -y_end_pos, "label": f"ζ={zeta}"})

damp_df = pd.DataFrame(damp_lines)

# Natural frequency circles
wn_values = [1.0, 2.0, 3.0, 4.0]
wn_data = []
for wn in wn_values:
    theta = np.linspace(0, 2 * np.pi, 100)
    for t in theta:
        wn_data.append({"real": wn * np.cos(t), "imaginary": wn * np.sin(t), "wn": f"ωn={wn}"})

wn_df = pd.DataFrame(wn_data)

# Branch colors
branch_colors = ["#306998", "#E8833A", "#5BA65B"]

# Plot
plot = (
    ggplot()
    # Damping ratio guide lines
    + geom_segment(
        damp_df, aes(x="x", y="y", xend="xend", yend="yend"), color="#CCCCCC", linetype="dashed", size=0.5, alpha=0.5
    )
    # Natural frequency circles
    + geom_path(
        wn_df, aes(x="real", y="imaginary", group="wn"), color="#CCCCCC", linetype="dotted", size=0.4, alpha=0.4
    )
    # Real axis segments of root locus
    + geom_segment(seg_df, aes(x="x_start", y="y", xend="x_end", yend="y"), color="#306998", size=1.8, alpha=0.7)
    # Root locus branches
    + geom_path(df, aes(x="real", y="imaginary", color="branch", group="branch"), size=1.5, alpha=0.85)
    # Direction arrows
    + geom_segment(
        arrow_df, aes(x="x", y="y", xend="xend", yend="yend"), color="#222222", size=1.2, arrow=arrow(length=0.15)
    )
    # Open-loop poles (× markers)
    + geom_point(pole_df, aes(x="real", y="imaginary"), shape="x", size=6, color="#222222", stroke=2)
    # Imaginary axis crossings (stability boundary)
    + geom_point(crossing_df, aes(x="real", y="imaginary"), shape="D", size=4, color="#D62728", stroke=1.5)
    # Axes
    + geom_hline(yintercept=0, color="#999999", size=0.4)
    + geom_vline(xintercept=0, color="#999999", size=0.4)
    + scale_color_manual(values=branch_colors)
    + coord_fixed(ratio=1, xlim=(-5, 1.5), ylim=(-4, 4))
    + labs(title="root-locus-basic · plotnine · pyplots.ai", x="Real Axis (σ)", y="Imaginary Axis (jω)", color="Branch")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_major=element_line(color="#EEEEEE", size=0.3),
        panel_grid_minor=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)

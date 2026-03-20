""" pyplots.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from mizani.formatters import custom_format
from plotnine import (
    aes,
    annotate,
    arrow,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    geom_vline,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_shape_manual,
    scale_x_continuous,
    scale_y_continuous,
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

# Find breakaway point on the real axis (where branches depart from real axis)
# dK/ds = 0 => derivative of -(s^3 + 4s^2 + 3s) = -(3s^2 + 8s + 3) = 0
breakaway_roots = np.roots([3, 8, 3])
breakaway_s = breakaway_roots[(breakaway_roots > -1) & (breakaway_roots < 0)][0]
breakaway_K = -(breakaway_s**3 + 4 * breakaway_s**2 + 3 * breakaway_s)

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

# Poles markers
pole_df = pd.DataFrame({"real": open_loop_poles, "imaginary": np.zeros(len(open_loop_poles)), "type": "Open-loop Pole"})

crossing_df = pd.DataFrame(crossings)

# Breakaway point marker
breakaway_df = pd.DataFrame([{"real": breakaway_s, "imaginary": 0.0, "type": "Breakaway Point"}])

# Combined markers for legend via scale_shape_manual
marker_df = pd.concat([pole_df, breakaway_df], ignore_index=True)

# Damping ratio lines — radiate from origin into the LEFT half-plane (stable region)
damping_ratios = [0.2, 0.4, 0.6, 0.8]
damp_lines = []
radius = 4.8
for zeta in damping_ratios:
    theta = np.arccos(zeta)
    x_end = -radius * zeta
    y_end_pos = radius * np.sin(theta)
    damp_lines.append({"x": 0, "y": 0, "xend": x_end, "yend": y_end_pos, "label": f"ζ={zeta}"})
    damp_lines.append({"x": 0, "y": 0, "xend": x_end, "yend": -y_end_pos, "label": f"ζ={zeta}"})

damp_df = pd.DataFrame(damp_lines)

# Damping ratio labels (placed along upper lines, offset from endpoints)
damp_label_df = damp_df[damp_df["yend"] > 0].copy()
damp_label_df["lx"] = damp_label_df["xend"] * 0.75
damp_label_df["ly"] = damp_label_df["yend"] * 0.75

# Natural frequency circles
wn_values = [1.0, 2.0, 3.0, 4.0]
wn_data = []
for wn in wn_values:
    theta = np.linspace(0, 2 * np.pi, 100)
    for t in theta:
        wn_data.append({"real": wn * np.cos(t), "imaginary": wn * np.sin(t), "wn": f"ωn={wn}"})

wn_df = pd.DataFrame(wn_data)

# Natural frequency labels (placed at top-left of each circle)
wn_label_df = pd.DataFrame([{"real": -0.45, "imaginary": wn + 0.15, "label": f"ωn={wn}"} for wn in wn_values])

# Crossing annotations
crossing_label_df = crossing_df.copy()
crossing_label_df["label"] = crossing_label_df["gain"].apply(lambda g: f"K={g:.1f}")

# Branch colors — cohesive palette starting with Python Blue
branch_colors = ["#306998", "#E8833A", "#5BA65B"]

# Mizani custom formatters for axis labels (distinctive plotnine feature)
sigma_fmt = custom_format("{:.0f}")
jw_fmt = custom_format("{:.0f}j")

# Plot — square format (3600x3600) for coord_fixed root locus
plot = (
    ggplot()
    # Subtle stability region shading
    + annotate("rect", xmin=-5.5, xmax=0, ymin=-5, ymax=5, fill="#E8F5E9", alpha=0.25)
    + annotate("rect", xmin=0, xmax=2.5, ymin=-5, ymax=5, fill="#FFEBEE", alpha=0.2)
    + annotate("text", x=-4.6, y=4.2, label="Stable", color="#2E7D32", size=9, fontstyle="italic", alpha=0.6)
    + annotate("text", x=1.3, y=4.2, label="Unstable", color="#C62828", size=9, fontstyle="italic", alpha=0.6)
    # Damping ratio guide lines — increased visibility
    + geom_segment(
        damp_df, aes(x="x", y="y", xend="xend", yend="yend"), color="#AAAAAA", linetype="dashed", size=0.6, alpha=0.7
    )
    # Damping ratio labels directly on plot
    + geom_text(
        damp_label_df, aes(x="lx", y="ly", label="label"), color="#777777", size=8, fontstyle="italic", ha="center"
    )
    # Natural frequency circles — increased visibility
    + geom_path(
        wn_df, aes(x="real", y="imaginary", group="wn"), color="#BBBBBB", linetype="dotted", size=0.5, alpha=0.55
    )
    # Natural frequency labels
    + geom_text(wn_label_df, aes(x="real", y="imaginary", label="label"), color="#888888", size=7, fontstyle="italic")
    # Real axis segments of root locus
    + geom_segment(
        seg_df, aes(x="x_start", y="y", xend="x_end", yend="y"), color="#8B5E3C", size=2.5, alpha=0.55, linetype="solid"
    )
    # Root locus branches
    + geom_path(df, aes(x="real", y="imaginary", color="branch", group="branch"), size=1.5, alpha=0.9)
    # Direction arrows
    + geom_segment(
        arrow_df, aes(x="x", y="y", xend="xend", yend="yend"), color="#222222", size=1.2, arrow=arrow(length=0.15)
    )
    # Open-loop poles and breakaway point via shape mapping
    + geom_point(
        marker_df, aes(x="real", y="imaginary", shape="type"), size=5, color="#222222", stroke=2, fill="#222222"
    )
    + scale_shape_manual(values={"Open-loop Pole": "x", "Breakaway Point": "s"}, name="Markers")
    # Imaginary axis crossings (stability boundary)
    + geom_point(crossing_df, aes(x="real", y="imaginary"), shape="D", size=4.5, color="#D62728", stroke=1.5)
    # Crossing gain annotations — offset to avoid overlap
    + geom_text(
        crossing_label_df,
        aes(x="real", y="imaginary", label="label"),
        color="#D62728",
        size=9,
        ha="left",
        nudge_x=0.4,
        nudge_y=0.3,
        fontweight="bold",
    )
    # Breakaway annotation — moved further from origin to reduce clutter
    + annotate(
        "text",
        x=breakaway_s - 0.6,
        y=-0.55,
        label=f"Breakaway\nK={breakaway_K:.2f}",
        color="#555555",
        size=8,
        ha="center",
        fontweight="bold",
    )
    # Axes
    + geom_hline(yintercept=0, color="#888888", size=0.5)
    + geom_vline(xintercept=0, color="#888888", size=0.5, linetype="solid")
    + scale_color_manual(values=branch_colors)
    # Mizani formatters for axis tick labels (distinctive plotnine/mizani feature)
    + scale_x_continuous(labels=sigma_fmt, breaks=[-5, -4, -3, -2, -1, 0, 1, 2])
    + scale_y_continuous(labels=jw_fmt, breaks=[-4, -3, -2, -1, 0, 1, 2, 3, 4])
    + coord_fixed(ratio=1, xlim=(-5.2, 2.2), ylim=(-4.8, 4.8))
    + labs(title="root-locus-basic · plotnine · pyplots.ai", x="Real Axis (σ)", y="Imaginary Axis (jω)", color="Branch")
    # Plotnine guides() for legend customization (distinctive feature)
    + guides(
        shape=guide_legend(order=1, override_aes={"size": 4}), color=guide_legend(order=2, override_aes={"size": 2})
    )
    + theme_minimal()
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, weight="bold", ha="center"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_background=element_rect(fill="#FAFAFA", color="#DDDDDD", size=0.5),
        legend_key_size=20,
        panel_grid_major=element_line(color="#F0F0F0", size=0.3),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
    )
)

# Save as square format for coord_fixed root locus
plot.save("plot.png", dpi=300, verbose=False)

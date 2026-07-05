""" anyplot.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: plotnine 0.15.7 | Python 3.13.13
Quality: 89/100 | Updated: 2026-06-18
"""

import sys


# sys.path[0] is the script directory — remove it so 'plotnine' resolves to the installed package
sys.path.pop(0)

import os

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


# Theme tokens — Imprint style guide
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — branch colors at positions 1, 2, 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
branch_colors = IMPRINT_PALETTE[:3]

# Stability region shading — theme-adaptive warm tints
STABLE_FILL = "#E8F5E9" if THEME == "light" else "#0F2015"
UNSTABLE_FILL = "#FFEBEE" if THEME == "light" else "#200F0F"

# Transfer function G(s) = 1 / [s(s+1)(s+3)]
# Open-loop poles at s=0, -1, -3; no open-loop zeros
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

# Imaginary axis crossings (stability boundary)
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

# Breakaway point: dK/ds = 0  →  -(3s^2 + 8s + 3) = 0
breakaway_roots = np.roots([3, 8, 3])
breakaway_s = breakaway_roots[(breakaway_roots > -1) & (breakaway_roots < 0)][0]
breakaway_K = -(breakaway_s**3 + 4 * breakaway_s**2 + 3 * breakaway_s)

# Real axis segments on the root locus (left of odd count of poles+zeros)
real_features = np.sort(np.concatenate([open_loop_poles, open_loop_zeros]))
real_axis_segs = []
for x in np.linspace(-5.0, 1.0, 2000):
    if np.sum(real_features >= x) % 2 == 1:
        real_axis_segs.append(x)

seg_intervals = []
if real_axis_segs:
    seg_start = real_axis_segs[0]
    for i in range(1, len(real_axis_segs)):
        if real_axis_segs[i] - real_axis_segs[i - 1] > 0.01:
            seg_intervals.append((seg_start, real_axis_segs[i - 1]))
            seg_start = real_axis_segs[i]
    seg_intervals.append((seg_start, real_axis_segs[-1]))

seg_df = pd.DataFrame(seg_intervals, columns=["x_start", "x_end"])
seg_df["y"] = 0.0

# Direction-of-increasing-gain arrows on each branch
arrows = []
for branch in df["branch"].unique():
    b_df = df[df["branch"] == branch].reset_index(drop=True)
    mid = len(b_df) * 2 // 5
    if mid > 0:
        arrows.append(
            {
                "x": b_df.loc[mid - 1, "real"],
                "y": b_df.loc[mid - 1, "imaginary"],
                "xend": b_df.loc[mid, "real"],
                "yend": b_df.loc[mid, "imaginary"],
            }
        )

arrow_df = pd.DataFrame(arrows)

# Markers: open-loop poles and breakaway point
pole_df = pd.DataFrame({"real": open_loop_poles, "imaginary": np.zeros(len(open_loop_poles)), "type": "Open-loop Pole"})
breakaway_df = pd.DataFrame([{"real": breakaway_s, "imaginary": 0.0, "type": "Breakaway Point"}])
marker_df = pd.concat([pole_df, breakaway_df], ignore_index=True)

crossing_df = pd.DataFrame(crossings)
crossing_label_df = crossing_df.copy()
crossing_label_df["label"] = crossing_label_df["gain"].apply(lambda g: f"K={g:.1f}")

# Damping ratio guide lines radiating from origin into left half-plane
radius = 4.8
damp_lines = []
for zeta in [0.2, 0.4, 0.6, 0.8]:
    theta = np.arccos(zeta)
    x_end = -radius * zeta
    y_pos = radius * np.sin(theta)
    damp_lines += [
        {"x": 0, "y": 0, "xend": x_end, "yend": y_pos, "label": f"ζ={zeta}"},
        {"x": 0, "y": 0, "xend": x_end, "yend": -y_pos, "label": f"ζ={zeta}"},
    ]

damp_df = pd.DataFrame(damp_lines)
damp_label_df = damp_df[damp_df["yend"] > 0].copy()
damp_label_df["lx"] = damp_label_df["xend"] * 0.75
damp_label_df["ly"] = damp_label_df["yend"] * 0.75

# Natural frequency circles
wn_data = []
for wn in [1.0, 2.0, 3.0, 4.0]:
    for t in np.linspace(0, 2 * np.pi, 100):
        wn_data.append({"real": wn * np.cos(t), "imaginary": wn * np.sin(t), "wn": f"ωn={wn}"})

wn_df = pd.DataFrame(wn_data)
wn_label_df = pd.DataFrame(
    [{"real": -0.5, "imaginary": wn + 0.2, "label": f"ωn={int(wn)}"} for wn in [1.0, 2.0, 3.0, 4.0]]
)

# Axis label formatters (mizani)
sigma_fmt = custom_format("{:.0f}")


# Plot
plot = (
    ggplot()
    # Stability region shading
    + annotate("rect", xmin=-5.5, xmax=0, ymin=-5, ymax=5, fill=STABLE_FILL, alpha=0.45)
    + annotate("rect", xmin=0, xmax=2.5, ymin=-5, ymax=5, fill=UNSTABLE_FILL, alpha=0.45)
    + annotate("text", x=-4.6, y=4.3, label="Stable", color="#009E73", size=3.5, fontstyle="italic")
    + annotate("text", x=1.3, y=4.3, label="Unstable", color="#AE3030", size=3.5, fontstyle="italic")
    # Damping ratio guide lines
    + geom_segment(
        damp_df, aes(x="x", y="y", xend="xend", yend="yend"), color=INK_SOFT, linetype="dashed", size=0.45, alpha=0.5
    )
    + geom_text(
        damp_label_df, aes(x="lx", y="ly", label="label"), color=INK_MUTED, size=3.2, fontstyle="italic", ha="center"
    )
    # Natural frequency circles
    + geom_path(
        wn_df, aes(x="real", y="imaginary", group="wn"), color=INK_SOFT, linetype="dotted", size=0.35, alpha=0.5
    )
    + geom_text(wn_label_df, aes(x="real", y="imaginary", label="label"), color=INK_MUTED, size=3.2, fontstyle="italic")
    # Real axis segments
    + geom_segment(
        seg_df, aes(x="x_start", y="y", xend="x_end", yend="y"), color=INK_SOFT, size=2.0, alpha=0.45, linetype="solid"
    )
    # Root locus branches — Imprint palette positions 1, 2, 3
    + geom_path(df, aes(x="real", y="imaginary", color="branch", group="branch"), size=1.1, alpha=0.9)
    # Direction-of-increasing-gain arrows
    + geom_segment(arrow_df, aes(x="x", y="y", xend="xend", yend="yend"), color=INK, size=0.9, arrow=arrow(length=0.15))
    # Open-loop poles (×) and breakaway point (□)
    + geom_point(marker_df, aes(x="real", y="imaginary", shape="type"), size=4, color=INK, stroke=1.5, fill=INK)
    + scale_shape_manual(values={"Open-loop Pole": "x", "Breakaway Point": "s"}, name="Markers")
    # Imaginary axis crossings — Imprint matte red: semantic role (instability boundary)
    + geom_point(crossing_df, aes(x="real", y="imaginary"), shape="D", size=4, color="#AE3030", stroke=1.2)
    + geom_text(
        crossing_label_df,
        aes(x="real", y="imaginary", label="label"),
        color="#AE3030",
        size=3.0,
        ha="left",
        nudge_x=0.4,
        nudge_y=0.3,
        fontweight="bold",
    )
    # Breakaway point annotation
    + annotate(
        "text",
        x=breakaway_s - 0.8,
        y=-0.7,
        label=f"Breakaway\nK={breakaway_K:.2f}",
        color=INK_SOFT,
        size=3.0,
        ha="center",
        fontweight="bold",
    )
    # Axes (real and imaginary)
    + geom_hline(yintercept=0, color=INK_SOFT, size=0.4)
    + geom_vline(xintercept=0, color=INK_SOFT, size=0.4)
    + scale_color_manual(values=branch_colors)
    + scale_x_continuous(labels=sigma_fmt, breaks=[-5, -4, -3, -2, -1, 0, 1, 2])
    + scale_y_continuous(
        labels=lambda vs: ["0" if int(round(v)) == 0 else f"{int(round(v))}j" for v in vs],
        breaks=[-4, -3, -2, -1, 0, 1, 2, 3, 4],
    )
    + coord_fixed(ratio=1, xlim=(-5.2, 2.2), ylim=(-4.8, 4.8))
    + labs(
        title="root-locus-basic · python · plotnine · anyplot.ai",
        x="Real Axis (σ)",
        y="Imaginary Axis (jω)",
        color="Branch",
    )
    + guides(
        shape=guide_legend(order=1, override_aes={"size": 4}), color=guide_legend(order=2, override_aes={"size": 2})
    )
    + theme_minimal()
    + theme(
        figure_size=(6, 6),
        plot_title=element_text(size=12, weight="bold", ha="center", color=INK),
        axis_title=element_text(size=10, color=INK),
        axis_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=10, weight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_position="right",
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT, size=0.5),
        legend_key_size=14,
        panel_grid_major=element_line(color=INK, size=0.2, alpha=0.12),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_rect(color=INK_SOFT, fill=None),
        axis_line=element_line(color=INK_SOFT, size=0.4),
    )
)

plot.save(f"plot-{THEME}.png", dpi=400, width=6, height=6, units="in", verbose=False)

""" pyplots.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    arrow,
    coord_fixed,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_ribbon,
    geom_segment,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_alpha_manual,
    scale_color_manual,
    scale_linetype_manual,
    scale_size_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Transfer function G(s) = 5 / [(s+1)(0.5s+1)(0.2s+1)]
# Poles at s = -1, -2, -5 (stable minimum-phase system)
omega = np.concatenate(
    [np.logspace(-2, -0.5, 150), np.logspace(-0.5, 0.5, 300), np.logspace(0.5, 1.5, 200), np.logspace(1.5, 3, 100)]
)

K = 5.0
jw = 1j * omega
G = K / ((jw + 1) * (0.5 * jw + 1) * (0.2 * jw + 1))

real_part = G.real
imag_part = G.imag

# Build unified DataFrame for both curves
df_pos = pd.DataFrame({"real": real_part, "imaginary": imag_part, "curve": "Positive freq (ω > 0)"})
df_neg = pd.DataFrame({"real": real_part[::-1], "imaginary": -imag_part[::-1], "curve": "Negative freq (ω < 0)"})
df_curves = pd.concat([df_pos, df_neg], ignore_index=True)

# Unit circle reference
theta = np.linspace(0, 2 * np.pi, 200)
unit_circle_df = pd.DataFrame({"real": np.cos(theta), "imaginary": np.sin(theta)})

# Stability region shading
theta_fill = np.linspace(0, 2 * np.pi, 100)
cos_vals = np.cos(theta_fill)
sin_vals = np.sin(np.arccos(np.clip(cos_vals, -1, 1)))
stability_df = pd.DataFrame({"x": cos_vals, "ymin": -sin_vals, "ymax": sin_vals})

# Critical point (-1, 0)
critical_df = pd.DataFrame({"real": [-1.0], "imaginary": [0.0]})

# Frequency annotations - positioned away from crossover markers near origin
# Use explicit offsets to guarantee no overlap with critical point / crossover labels
freq_annotations = [
    (0.1, 0.4, -0.5),  # upper right region - offset down-right
    (0.3, 0.6, -0.55),  # right side - offset down-right
    (0.7, 0.5, -0.55),  # bottom region - offset down
    (1.5, -0.7, 0.5),  # lower-left - offset up-left (away from gain crossover label)
    (3.0, 0.75, 0.8),  # near origin - offset up-right, well clear of phase crossover marker
]
annot_rows = []
for wf, ox, oy in freq_annotations:
    idx = np.argmin(np.abs(omega - wf))
    rx, ry = real_part[idx], imag_part[idx]
    annot_rows.append({"real": rx, "imaginary": ry, "label": f"ω = {wf:g}", "lx": rx + ox, "ly": ry + oy})

annot_df = pd.DataFrame(annot_rows)

# Direction arrows along positive frequency curve
arrow_data = []
for frac in [0.06, 0.3, 0.65]:
    idx = int(frac * len(df_pos))
    step = max(2, int(0.015 * len(df_pos)))
    if 0 < idx < len(df_pos) - step:
        arrow_data.append(
            {
                "x": df_pos.iloc[idx]["real"],
                "y": df_pos.iloc[idx]["imaginary"],
                "xend": df_pos.iloc[idx + step]["real"],
                "yend": df_pos.iloc[idx + step]["imaginary"],
            }
        )

# Direction arrows along negative frequency curve
for frac in [0.35, 0.75]:
    idx = int(frac * len(df_neg))
    step = max(2, int(0.015 * len(df_neg)))
    if 0 < idx < len(df_neg) - step:
        arrow_data.append(
            {
                "x": df_neg.iloc[idx]["real"],
                "y": df_neg.iloc[idx]["imaginary"],
                "xend": df_neg.iloc[idx + step]["real"],
                "yend": df_neg.iloc[idx + step]["imaginary"],
            }
        )

arrow_df = pd.DataFrame(arrow_data)

# Gain and phase margin calculations
mag = np.abs(G)
phase = np.degrees(np.angle(G))

gc_idx = np.argmin(np.abs(mag - 1.0))
gc_omega = omega[gc_idx]
phase_margin = 180 + phase[gc_idx]

pc_idx = np.argmin(np.abs(phase + 180))
pc_omega = omega[pc_idx]
gain_margin_db = -20 * np.log10(mag[pc_idx])

# Segment from origin to gain crossover point (shows phase margin angle)
gc_seg_df = pd.DataFrame({"x": [0.0], "y": [0.0], "xend": [G[gc_idx].real], "yend": [G[gc_idx].imag]})

# Plot
plot = (
    ggplot()
    # Stability region shading
    + geom_ribbon(stability_df, aes(x="x", ymin="ymin", ymax="ymax"), fill="#E8EDF2", alpha=0.3)
    # Unit circle
    + geom_path(unit_circle_df, aes(x="real", y="imaginary"), color="#BBBBBB", size=0.8, linetype="dashed")
    # Nyquist curves with unified legend via aes-mapped scales
    + geom_path(df_curves, aes(x="real", y="imaginary", color="curve", linetype="curve", size="curve", alpha="curve"))
    + scale_color_manual(
        values={"Positive freq (ω > 0)": "#306998", "Negative freq (ω < 0)": "#7BA4C7"}, name="Frequency Response"
    )
    + scale_linetype_manual(
        values={"Positive freq (ω > 0)": "solid", "Negative freq (ω < 0)": "dashed"}, name="Frequency Response"
    )
    + scale_size_manual(values={"Positive freq (ω > 0)": 1.5, "Negative freq (ω < 0)": 1.0}, name="Frequency Response")
    + scale_alpha_manual(
        values={"Positive freq (ω > 0)": 0.95, "Negative freq (ω < 0)": 0.55}, name="Frequency Response"
    )
    # Direction arrows
    + geom_segment(
        arrow_df, aes(x="x", y="y", xend="xend", yend="yend"), color="#333333", size=1.0, arrow=arrow(length=0.15)
    )
    # Phase margin line from origin to gain crossover
    + geom_segment(
        gc_seg_df, aes(x="x", y="y", xend="xend", yend="yend"), color="#9467BD", size=0.7, linetype="dotted", alpha=0.7
    )
    # Critical point marker
    + geom_point(critical_df, aes(x="real", y="imaginary"), color="#D62728", size=7, shape="x", stroke=2.5)
    + annotate(
        "text",
        x=-1.95,
        y=0.85,
        label="Critical point\n(−1, 0)",
        color="#D62728",
        size=12,
        fontweight="bold",
        ha="center",
    )
    + annotate("segment", x=-1.55, y=0.6, xend=-1.05, yend=0.1, color="#D62728", size=0.5, alpha=0.5)
    # Gain crossover marker
    + geom_point(
        pd.DataFrame({"real": [G[gc_idx].real], "imaginary": [G[gc_idx].imag]}),
        aes(x="real", y="imaginary"),
        color="#9467BD",
        size=5.5,
        shape="o",
        stroke=1.8,
    )
    # Phase crossover marker
    + geom_point(
        pd.DataFrame({"real": [G[pc_idx].real], "imaginary": [G[pc_idx].imag]}),
        aes(x="real", y="imaginary"),
        color="#E8833A",
        size=5.5,
        shape="s",
        stroke=1.8,
        fill="#E8833A",
    )
    # Gain crossover annotation - positioned in lower-left, well clear of origin and freq labels
    + annotate(
        "text",
        x=-3.2,
        y=-2.6,
        label=f"Gain crossover\nω = {gc_omega:.1f} rad/s · PM = {phase_margin:.0f}°",
        color="#9467BD",
        size=12,
        ha="left",
        fontweight="bold",
    )
    + annotate(
        "segment",
        x=-2.1,
        y=-2.1,
        xend=G[gc_idx].real - 0.1,
        yend=G[gc_idx].imag - 0.1,
        color="#9467BD",
        size=0.6,
        alpha=0.7,
    )
    # Phase crossover annotation - positioned in upper-left, well separated
    + annotate(
        "text",
        x=-2.8,
        y=2.6,
        label=f"Phase crossover\nω = {pc_omega:.1f} rad/s · GM = {gain_margin_db:.1f} dB",
        color="#E8833A",
        size=12,
        ha="left",
        fontweight="bold",
    )
    + annotate(
        "segment",
        x=-1.9,
        y=2.2,
        xend=G[pc_idx].real + 0.05,
        yend=G[pc_idx].imag + 0.05,
        color="#E8833A",
        size=0.6,
        alpha=0.7,
    )
    # Frequency annotation dots and labels
    + geom_point(annot_df, aes(x="real", y="imaginary"), color="#306998", size=3.5, shape="o", fill="#306998")
)

# Frequency labels
for _, row in annot_df.iterrows():
    plot = plot + annotate("text", x=row["lx"], y=row["ly"], label=row["label"], color="#444444", size=12)

# Axes, scales, and styling
plot = (
    plot
    + scale_x_continuous(breaks=[-3, -2, -1, 0, 1, 2, 3, 4, 5])
    + scale_y_continuous(breaks=[-3, -2, -1, 0, 1, 2, 3])
    + coord_fixed(ratio=1, xlim=(-3.8, 5.8), ylim=(-3.8, 3.8))
    + labs(
        title="nyquist-basic · plotnine · pyplots.ai", x="Real Axis [dimensionless]", y="Imaginary Axis [dimensionless]"
    )
    + guides(color=guide_legend(title="Frequency Response", override_aes={"size": 2}))
    + theme_minimal()
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, weight="bold", ha="center"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16, color="#555555"),
        panel_grid_major=element_line(color="#EFEFEF", size=0.3),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="#FAFBFC", color="white"),
        legend_position="bottom",
        legend_title=element_text(size=14, weight="bold"),
        legend_text=element_text(size=12),
        legend_background=element_rect(fill="white", alpha=0.9),
    )
)

plot.save("plot.png", dpi=300, verbose=False)

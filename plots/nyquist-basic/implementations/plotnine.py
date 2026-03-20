""" pyplots.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-20
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
    geom_segment,
    ggplot,
    labs,
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

# Positive frequency curve
df_pos = pd.DataFrame({"real": real_part, "imaginary": imag_part})

# Negative frequency curve (conjugate mirror)
df_neg = pd.DataFrame({"real": real_part[::-1], "imaginary": -imag_part[::-1]})

# Unit circle reference
theta = np.linspace(0, 2 * np.pi, 200)
unit_circle_df = pd.DataFrame({"real": np.cos(theta), "imaginary": np.sin(theta)})

# Critical point (-1, 0)
critical_df = pd.DataFrame({"real": [-1.0], "imaginary": [0.0]})

# Frequency annotations at well-spaced points
annotation_config = [(0.1, 0.25, 0.35), (0.3, 0.4, -0.35), (0.7, -0.2, -0.5), (1.5, -0.5, -0.3), (3.0, -0.3, 0.3)]
annot_data = []
for wf, nx, ny in annotation_config:
    idx = np.argmin(np.abs(omega - wf))
    annot_data.append({"real": real_part[idx], "imaginary": imag_part[idx], "label": f"ω={wf:g}", "nx": nx, "ny": ny})

annot_df = pd.DataFrame(annot_data)

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

# Gain and phase margin
mag = np.abs(G)
phase = np.degrees(np.angle(G))

# Gain crossover: |G(jw)| = 1
gc_idx = np.argmin(np.abs(mag - 1.0))
gc_omega = omega[gc_idx]
phase_margin = 180 + phase[gc_idx]

# Phase crossover: angle(G(jw)) = -180°
pc_idx = np.argmin(np.abs(phase + 180))
pc_omega = omega[pc_idx]
gain_margin_db = -20 * np.log10(mag[pc_idx])

gc_df = pd.DataFrame({"real": [G[gc_idx].real], "imaginary": [G[gc_idx].imag]})
pc_df = pd.DataFrame({"real": [G[pc_idx].real], "imaginary": [G[pc_idx].imag]})

# Segment from origin to gain crossover point (shows phase margin angle)
gc_seg_df = pd.DataFrame({"x": [0.0], "y": [0.0], "xend": [G[gc_idx].real], "yend": [G[gc_idx].imag]})

# Plot
plot = (
    ggplot()
    # Unit circle
    + geom_path(unit_circle_df, aes(x="real", y="imaginary"), color="#CCCCCC", size=0.8, linetype="dashed")
    # Nyquist curve - positive frequencies
    + geom_path(df_pos, aes(x="real", y="imaginary"), color="#306998", size=1.5, alpha=0.9)
    # Nyquist curve - negative frequencies
    + geom_path(df_neg, aes(x="real", y="imaginary"), color="#7BA4C7", size=1.2, alpha=0.6, linetype="dashed")
    # Direction arrows
    + geom_segment(
        arrow_df, aes(x="x", y="y", xend="xend", yend="yend"), color="#333333", size=1.0, arrow=arrow(length=0.15)
    )
    # Phase margin line from origin to gain crossover
    + geom_segment(
        gc_seg_df, aes(x="x", y="y", xend="xend", yend="yend"), color="#2CA02C", size=0.7, linetype="dotted", alpha=0.7
    )
    # Critical point (-1, 0)
    + geom_point(critical_df, aes(x="real", y="imaginary"), color="#D62728", size=6, shape="x", stroke=2.5)
    + annotate("text", x=-1.55, y=0.0, label="(−1, 0)", color="#D62728", size=10, fontweight="bold", ha="center")
    # Gain crossover point
    + geom_point(gc_df, aes(x="real", y="imaginary"), color="#2CA02C", size=5, shape="o", stroke=1.5)
    + annotate(
        "text",
        x=-2.2,
        y=-1.2,
        label=f"Gain crossover\nω={gc_omega:.1f} rad/s, PM={phase_margin:.0f}°",
        color="#2CA02C",
        size=8,
        ha="left",
    )
    # Leader line from gain crossover label to point
    + annotate(
        "segment", x=-1.5, y=-1.0, xend=G[gc_idx].real, yend=G[gc_idx].imag, color="#2CA02C", size=0.5, alpha=0.6
    )
    # Phase crossover point
    + geom_point(pc_df, aes(x="real", y="imaginary"), color="#E8833A", size=5, shape="s", stroke=1.5, fill="#E8833A")
    + annotate(
        "text",
        x=-2.2,
        y=1.6,
        label=f"Phase crossover\nω={pc_omega:.1f} rad/s, GM={gain_margin_db:.1f} dB",
        color="#E8833A",
        size=8,
        ha="left",
    )
    # Leader line from phase crossover label to point
    + annotate("segment", x=-1.5, y=1.3, xend=G[pc_idx].real, yend=G[pc_idx].imag, color="#E8833A", size=0.5, alpha=0.6)
    # Frequency annotation dots
    + geom_point(annot_df, aes(x="real", y="imaginary"), color="#306998", size=3, shape="o", fill="#306998")
)

# Frequency labels with per-point nudge
for _, row in annot_df.iterrows():
    plot = plot + annotate(
        "text", x=row["real"] + row["nx"], y=row["imaginary"] + row["ny"], label=row["label"], color="#555555", size=9
    )

# Axes and styling
plot = (
    plot
    + scale_x_continuous(breaks=[-3, -2, -1, 0, 1, 2, 3, 4, 5])
    + scale_y_continuous(breaks=[-3, -2, -1, 0, 1, 2, 3])
    + coord_fixed(ratio=1, xlim=(-3.5, 5.8), ylim=(-3.8, 3.8))
    + labs(title="nyquist-basic · plotnine · pyplots.ai", x="Real", y="Imaginary")
    + theme_minimal()
    + theme(
        figure_size=(12, 12),
        plot_title=element_text(size=24, weight="bold", ha="center"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(color="#F0F0F0", size=0.3),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="white", color="white"),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)

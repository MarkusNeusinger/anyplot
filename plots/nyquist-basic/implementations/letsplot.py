""" pyplots.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave
from scipy import signal


LetsPlot.setup_html()  # noqa: F405

# Curated color palette
COLOR_PRIMARY = "#1B4F72"
COLOR_MIRROR = "#5DADE2"
COLOR_CRITICAL = "#C0392B"
COLOR_STABILITY = "#E74C3C"
COLOR_UNIT_CIRCLE = "#AEB6BF"
COLOR_GAIN_MARGIN = "#E74C3C"
COLOR_ANNOTATION = "#2C3E50"
COLOR_ARROW = "#1A5276"

# Data - Third-order system: G(s) = 2 / ((s+1)(0.5s+1)(0.2s+1))
num = [2.0]
den = np.polymul(np.polymul([1, 1], [0.5, 1]), [0.2, 1])
system = signal.TransferFunction(num, den)

omega = np.logspace(-2, 2, 500)
_, H = signal.freqresp(system, omega)

real_part = H.real
imag_part = H.imag

df = pd.DataFrame({"real": real_part, "imaginary": imag_part, "frequency": omega})

# Mirror (negative frequencies) for complete Nyquist contour
df_mirror = pd.DataFrame({"real": real_part, "imaginary": -imag_part, "frequency": -omega})

# Unit circle
theta = np.linspace(0, 2 * np.pi, 200)
df_circle = pd.DataFrame({"real": np.cos(theta), "imaginary": np.sin(theta)})

# Critical point (-1, 0)
df_critical = pd.DataFrame({"real": [-1.0], "imaginary": [0.0]})

# Gain margin line: from critical point to nearest point on curve where it crosses negative real axis
real_cross_mask = (imag_part[1:] * imag_part[:-1] < 0) & (real_part[:-1] < 0)
cross_indices = np.where(real_cross_mask)[0]
cross_idx = cross_indices[0] if len(cross_indices) > 0 else np.argmin(np.abs(imag_part[200:])) + 200
df_gain_margin = pd.DataFrame({"x": [-1.0], "y": [0.0], "xend": [real_part[cross_idx]], "yend": [0.0]})

# Arrow indicators along the curve showing direction of increasing frequency
arrow_indices = [50, 150, 300]
df_arrows = df.iloc[arrow_indices].copy()
df_arrows_next = df.iloc[[i + 5 for i in arrow_indices]].copy()
df_segments = pd.DataFrame(
    {
        "x": df_arrows["real"].values,
        "y": df_arrows["imaginary"].values,
        "xend": df_arrows_next["real"].values,
        "yend": df_arrows_next["imaginary"].values,
    }
)

# Frequency labels at key points
label_indices = [0, 80, 200, 350]
df_labels = df.iloc[label_indices].copy()
df_labels["label"] = [f"ω={omega[i]:.2f}" if omega[i] < 10 else f"ω={omega[i]:.0f}" for i in label_indices]
df_labels["nudge_x"] = [0.12, -0.18, -0.12, 0.12]
df_labels["nudge_y"] = [0.10, -0.14, 0.12, 0.10]

# Stability region highlight - shaded area around critical point
stability_theta = np.linspace(0, 2 * np.pi, 100)
stability_r = 0.15
df_stability_zone = pd.DataFrame(
    {"real": -1.0 + stability_r * np.cos(stability_theta), "imaginary": stability_r * np.sin(stability_theta)}
)

# Gain margin annotation
gain_margin_db = 20 * np.log10(1.0 / abs(real_part[cross_idx]))
df_gm_label = pd.DataFrame(
    {"real": [(-1.0 + real_part[cross_idx]) / 2], "imaginary": [0.12], "label": [f"GM = {gain_margin_db:.1f} dB"]}
)

# Plot
plot = (
    ggplot()
    # Stability zone highlight around critical point
    + geom_polygon(aes(x="real", y="imaginary"), data=df_stability_zone, fill=COLOR_STABILITY, alpha=0.07)
    # Unit circle
    + geom_path(aes(x="real", y="imaginary"), data=df_circle, color=COLOR_UNIT_CIRCLE, size=0.6, linetype="dashed")
    # Gain margin indicator line
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=df_gain_margin,
        color=COLOR_GAIN_MARGIN,
        size=0.7,
        linetype="dotted",
    )
    # Gain margin label
    + geom_label(
        aes(x="real", y="imaginary", label="label"),
        data=df_gm_label,
        size=16,
        color=COLOR_CRITICAL,
        fill="#FDEDEC",
        alpha=0.9,
        label_padding=0.3,
        label_r=0.15,
        label_size=0.5,
        fontface="bold",
    )
    # Mirror curve (negative frequencies)
    + geom_path(
        aes(x="real", y="imaginary"), data=df_mirror, color=COLOR_MIRROR, size=1.0, alpha=0.45, linetype="dashed"
    )
    # Main Nyquist curve with tooltips
    + geom_path(
        aes(x="real", y="imaginary"),
        data=df,
        color=COLOR_PRIMARY,
        size=2.2,
        tooltips=layer_tooltips()
        .format("real", ".3f")
        .format("imaginary", ".3f")
        .format("frequency", ".3f")
        .line("Re: @real")
        .line("Im: @imaginary")
        .line("ω: @frequency rad/s"),
    )
    # Direction arrows
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"),
        data=df_segments,
        color=COLOR_ARROW,
        size=1.5,
        arrow=arrow(length=14, type="closed"),
    )
    # Critical point (-1, 0) - prominent marker
    + geom_point(aes(x="real", y="imaginary"), data=df_critical, color=COLOR_CRITICAL, size=11, shape=4, stroke=3.5)
    # Critical point label
    + geom_text(
        aes(x="real", y="imaginary"),
        data=pd.DataFrame({"real": [-0.72], "imaginary": [0.28]}),
        label="(-1, 0)",
        size=18,
        color=COLOR_CRITICAL,
        fontface="bold",
    )
    # Origin marker
    + geom_point(
        aes(x="real", y="imaginary"),
        data=pd.DataFrame({"real": [0.0], "imaginary": [0.0]}),
        color="#7F8C8D",
        size=4,
        shape=3,
        stroke=2.0,
    )
    # Frequency annotations along curve
    + geom_label(
        aes(x="real", y="imaginary", label="label"),
        data=pd.DataFrame(
            {
                "real": df_labels["real"].values + df_labels["nudge_x"].values,
                "imaginary": df_labels["imaginary"].values + df_labels["nudge_y"].values,
                "label": df_labels["label"].values,
            }
        ),
        size=17,
        color=COLOR_ANNOTATION,
        fill="#F8F9F9",
        alpha=0.9,
        label_padding=0.35,
        label_r=0.2,
        label_size=0.3,
    )
    # Styling
    + labs(
        x="Re{G(jω)}",
        y="Im{G(jω)}",
        title="nyquist-basic · letsplot · pyplots.ai",
        subtitle="G(s) = 2 / [(s+1)(0.5s+1)(0.2s+1)]  —  Stable: curve does not encircle (-1, 0)",
    )
    + coord_fixed(ratio=1)
    + ggsize(1200, 1200)
    + theme_minimal()
    + theme(
        axis_text=element_text(size=16, color="#566573"),
        axis_title=element_text(size=22, color="#2C3E50", face="bold"),
        plot_title=element_text(size=26, color="#1B2631", face="bold"),
        plot_subtitle=element_text(size=16, color="#5D6D7E", face="italic"),
        panel_grid_major=element_line(color="#EAECEE", size=0.2),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="#FDFEFE", color="#FDFEFE"),
        panel_background=element_rect(fill="#FFFFFF", color="#D5D8DC", size=0.3),
        axis_ticks=element_blank(),
        axis_ticks_length=0,
        plot_margin=[40, 40, 25, 25],
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")

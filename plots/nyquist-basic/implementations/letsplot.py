"""pyplots.ai
nyquist-basic: Nyquist Plot for Control Systems
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave
from scipy import signal


LetsPlot.setup_html()  # noqa: F405

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
df_labels["nudge_x"] = [0.08, -0.12, -0.08, 0.08]
df_labels["nudge_y"] = [0.06, -0.10, 0.08, 0.06]

# Plot
plot = (
    ggplot()
    # Unit circle
    + geom_path(aes(x="real", y="imaginary"), data=df_circle, color="#CCCCCC", size=0.8, linetype="dashed")
    # Mirror curve (negative frequencies)
    + geom_path(aes(x="real", y="imaginary"), data=df_mirror, color="#306998", size=1.2, alpha=0.35, linetype="dashed")
    # Main Nyquist curve with tooltips
    + geom_path(
        aes(x="real", y="imaginary"),
        data=df,
        color="#306998",
        size=1.8,
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
        color="#306998",
        size=1.2,
        arrow=arrow(length=10, type="closed"),
    )
    # Critical point (-1, 0)
    + geom_point(aes(x="real", y="imaginary"), data=df_critical, color="#D62728", size=8, shape=4, stroke=2.5)
    # Critical point label
    + geom_text(
        aes(x="real", y="imaginary"),
        data=pd.DataFrame({"real": [-1.0], "imaginary": [0.12]}),
        label="(-1, 0)",
        size=11,
        color="#D62728",
    )
    # Origin marker
    + geom_point(
        aes(x="real", y="imaginary"),
        data=pd.DataFrame({"real": [0.0], "imaginary": [0.0]}),
        color="#333333",
        size=3,
        shape=3,
        stroke=1.5,
    )
    # Frequency annotations along curve
    + geom_text(
        aes(x="real", y="imaginary", label="label"),
        data=pd.DataFrame(
            {
                "real": df_labels["real"].values + df_labels["nudge_x"].values,
                "imaginary": df_labels["imaginary"].values + df_labels["nudge_y"].values,
                "label": df_labels["label"].values,
            }
        ),
        size=9,
        color="#555555",
    )
    # Styling
    + labs(x="Real", y="Imaginary", title="nyquist-basic · letsplot · pyplots.ai")
    + coord_fixed(ratio=1)
    + ggsize(1200, 1200)
    + theme_minimal()
    + theme(
        axis_text=element_text(size=16, color="#555555"),
        axis_title=element_text(size=20, color="#333333"),
        plot_title=element_text(size=24, color="#222222", face="bold"),
        panel_grid_major=element_line(color="#E8E8E8", size=0.3),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),
        panel_background=element_rect(fill="transparent", color="transparent"),
        axis_ticks=element_blank(),
        axis_ticks_length=0,
        plot_margin=[30, 30, 20, 20],
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")

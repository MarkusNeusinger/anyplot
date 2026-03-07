""" pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 75/100 | Created: 2026-03-07
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    arrow,
    coord_fixed,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    theme,
    theme_void,
    xlim,
    ylim,
)


# Vertices for electron-positron annihilation: e- e+ -> gamma -> mu- mu+
vertices = {"v1": (2.0, 0.0), "v2": (6.0, 0.0)}

# Fermion lines (straight with arrows)
# e- incoming (upper left to v1)
# e+ incoming (lower left to v1) - antiparticle, arrow reversed
# mu- outgoing (v2 to upper right)
# mu+ outgoing (v2 to lower right) - antiparticle, arrow reversed

fermion_segments = pd.DataFrame(
    {"x": [0.0, 0.0, 6.0, 6.0], "y": [1.5, -1.5, 0.0, 0.0], "xend": [2.0, 2.0, 8.0, 8.0], "yend": [0.0, 0.0, 1.5, -1.5]}
)

# Fermion labels
fermion_labels = pd.DataFrame(
    {
        "x": [0.5, 0.5, 7.5, 7.5],
        "y": [1.15, -1.15, 1.15, -1.15],
        "label": ["e\u207b", "e\u207a", "\u03bc\u207b", "\u03bc\u207a"],
    }
)


# Wavy line for photon (gamma) between v1 and v2
def make_wavy_line(x_start, y_start, x_end, y_end, n_waves=6, amplitude=0.25):
    n_points = n_waves * 40
    t = np.linspace(0, 1, n_points)
    x_base = x_start + (x_end - x_start) * t
    y_base = y_start + (y_end - y_start) * t
    dx = x_end - x_start
    dy = y_end - y_start
    length = np.sqrt(dx**2 + dy**2)
    nx = -dy / length
    ny = dx / length
    wave = amplitude * np.sin(2 * np.pi * n_waves * t)
    x_wave = x_base + wave * nx
    y_wave = y_base + wave * ny
    return pd.DataFrame({"x": x_wave, "y": y_wave})


photon_df = make_wavy_line(2.0, 0.0, 6.0, 0.0)

# Photon label
photon_label = pd.DataFrame({"x": [4.0], "y": [0.55], "label": ["\u03b3"]})

# Vertex points
vertex_df = pd.DataFrame({"x": [2.0, 6.0], "y": [0.0, 0.0]})

# Plot
plot = (
    ggplot()
    + geom_segment(
        data=fermion_segments,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        size=1.2,
        color="#306998",
        arrow=arrow(length=0.12, type="closed"),
    )
    + geom_path(data=photon_df, mapping=aes(x="x", y="y"), size=1.2, color="#E0672A")
    + geom_point(data=vertex_df, mapping=aes(x="x", y="y"), size=5, color="#1a1a1a")
    + geom_text(
        data=fermion_labels, mapping=aes(x="x", y="y", label="label"), size=18, color="#306998", fontweight="bold"
    )
    + geom_text(
        data=photon_label, mapping=aes(x="x", y="y", label="label"), size=18, color="#E0672A", fontweight="bold"
    )
    + coord_fixed(ratio=1)
    + xlim(-0.5, 8.5)
    + ylim(-2.0, 2.0)
    + labs(title="feynman-basic \u00b7 plotnine \u00b7 pyplots.ai")
    + theme_void()
    + theme(figure_size=(16, 9), plot_title=element_text(size=24, ha="center", fontweight="medium"), plot_margin=0.05)
)

# Save
plot.save("plot.png", dpi=300, verbose=False)

"""pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-07
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    arrow,
    coord_fixed,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_void,
)


# --- Main diagram: e- e+ -> gamma -> mu- mu+ ---
# Vertex positions (spread wider for better canvas utilization)
v1x, v1y = 3.0, 3.5
v2x, v2y = 7.0, 3.5

# Fermion segments with correct Feynman arrow conventions:
# Particles (e-, mu-): arrows forward in time (left to right)
# Antiparticles (e+, mu+): arrows backward in time (right to left)
fermion_particles = pd.DataFrame({"x": [0.5, v2x], "y": [5.8, v2y], "xend": [v1x, 9.5], "yend": [v1y, 5.8]})
fermion_antiparticles = pd.DataFrame({"x": [v1x, 9.5], "y": [v1y, 1.2], "xend": [0.5, v2x], "yend": [1.2, v2y]})

# Fermion labels positioned near line endpoints
fermion_labels = pd.DataFrame(
    {
        "x": [0.3, 0.3, 9.7, 9.7],
        "y": [6.25, 0.75, 6.25, 0.75],
        "label": ["e\u207b", "e\u207a", "\u03bc\u207b", "\u03bc\u207a"],
    }
)

# Wavy photon line between vertices (inline, no function definition)
n_waves, amp = 7, 0.35
n_pts = n_waves * 40
t_ph = np.linspace(0, 1, n_pts)
photon_df = pd.DataFrame({"x": v1x + (v2x - v1x) * t_ph, "y": v1y + amp * np.sin(2 * np.pi * n_waves * t_ph)})

# Photon label
photon_label = pd.DataFrame({"x": [(v1x + v2x) / 2], "y": [v1y + 0.75], "label": ["\u03b3"]})

# Vertex dots
vertex_df = pd.DataFrame({"x": [v1x, v2x], "y": [v1y, v2y], "ptype": ["vertex", "vertex"]})

# --- Particle type legend showing all 4 line styles ---
leg_y = -0.5
leg_len = 1.5

# Fermion (solid + arrow)
leg_fermion = pd.DataFrame({"x": [0.3], "y": [leg_y], "xend": [0.3 + leg_len], "yend": [leg_y]})

# Photon (wavy)
t_lp = np.linspace(0, 1, 120)
leg_photon_df = pd.DataFrame({"x": 2.8 + leg_len * t_lp, "y": leg_y + 0.2 * np.sin(2 * np.pi * 4 * t_lp)})

# Gluon (curly looped line — tighter loops with larger amplitude for distinction)
t_gl = np.linspace(0, 1, 400)
n_loops = 7
gluon_base_x = 5.5 + leg_len * t_gl
gluon_loop_x = 0.12 * np.sin(2 * np.pi * n_loops * t_gl)
gluon_loop_y = 0.35 * np.abs(np.sin(np.pi * n_loops * t_gl))
leg_gluon_df = pd.DataFrame({"x": gluon_base_x + gluon_loop_x, "y": leg_y - 0.05 + gluon_loop_y})

# Scalar boson (dashed)
leg_boson = pd.DataFrame({"x": [8.0], "y": [leg_y], "xend": [8.0 + leg_len], "yend": [leg_y]})

# Legend text labels
legend_labels = pd.DataFrame(
    {
        "x": [0.3 + leg_len / 2, 2.8 + leg_len / 2, 5.5 + leg_len / 2, 8.0 + leg_len / 2],
        "y": [leg_y - 0.65] * 4,
        "label": ["Fermion", "Photon", "Gluon", "Scalar Boson"],
    }
)

# Time axis indicator
time_arrow_df = pd.DataFrame({"x": [1.5], "y": [0.3], "xend": [8.5], "yend": [0.3]})
time_label_df = pd.DataFrame({"x": [5.0], "y": [0.7], "label": ["time"]})

# --- Build the plot using plotnine grammar of graphics ---
plot = (
    ggplot()
    # Particle fermion lines (arrows forward in time)
    + geom_segment(
        data=fermion_particles,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        size=2.0,
        color="#306998",
        arrow=arrow(length=0.18, type="closed"),
    )
    # Antiparticle fermion lines (arrows backward in time)
    + geom_segment(
        data=fermion_antiparticles,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        size=2.0,
        color="#306998",
        arrow=arrow(length=0.18, type="closed"),
    )
    # Photon wavy propagator
    + geom_path(data=photon_df, mapping=aes(x="x", y="y"), size=2.0, color="#E0672A")
    # Vertex interaction points using color aesthetic with scale_color_manual
    + geom_point(data=vertex_df, mapping=aes(x="x", y="y", color="ptype"), size=8, show_legend=False)
    + scale_color_manual(values={"vertex": "#1a1a1a"})
    # Particle labels
    + geom_text(
        data=fermion_labels, mapping=aes(x="x", y="y", label="label"), size=22, color="#306998", fontweight="bold"
    )
    + geom_text(
        data=photon_label, mapping=aes(x="x", y="y", label="label"), size=22, color="#E0672A", fontweight="bold"
    )
    # Time axis arrow
    + geom_segment(
        data=time_arrow_df,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        size=0.8,
        color="#999999",
        arrow=arrow(length=0.1, type="open"),
    )
    + geom_text(
        data=time_label_df, mapping=aes(x="x", y="y", label="label"), size=16, color="#888888", fontstyle="italic"
    )
    # Legend: fermion (solid + arrow)
    + geom_segment(
        data=leg_fermion,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        size=1.5,
        color="#306998",
        arrow=arrow(length=0.1, type="closed"),
    )
    # Legend: photon (wavy)
    + geom_path(data=leg_photon_df, mapping=aes(x="x", y="y"), size=1.5, color="#E0672A")
    # Legend: gluon (curly)
    + geom_path(data=leg_gluon_df, mapping=aes(x="x", y="y"), size=1.5, color="#2ca02c")
    # Legend: scalar boson (dashed)
    + geom_segment(
        data=leg_boson,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        size=1.5,
        color="#9467bd",
        linetype="dashed",
    )
    # Legend labels (increased to 16 for legibility)
    + geom_text(data=legend_labels, mapping=aes(x="x", y="y", label="label"), size=16, color="#333333")
    # Subtitle annotation for the process
    + annotate(
        "text",
        x=5.0,
        y=6.8,
        label="e\u207be\u207a \u2192 \u03b3 \u2192 \u03bc\u207b\u03bc\u207a",
        size=18,
        color="#333333",
        fontstyle="italic",
    )
    # Layout using scale_x/y_continuous for finer axis control
    + scale_x_continuous(limits=(-0.5, 10.5), expand=(0, 0.2))
    + scale_y_continuous(limits=(-1.5, 7.5), expand=(0, 0.1))
    + coord_fixed(ratio=1)
    + labs(title="feynman-basic \u00b7 plotnine \u00b7 pyplots.ai")
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=26, ha="center", fontweight="bold", margin={"b": 8}),
        plot_background=element_rect(fill="white", color="white"),
        plot_margin=0.02,
    )
)

plot.save("plot.png", dpi=300, verbose=False)

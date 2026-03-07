""" pyplots.ai
feynman-basic: Feynman Diagram for Particle Interactions
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-07
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_path,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    ggsize,
    labs,
    theme,
    xlim,
    ylim,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Electron-positron annihilation into muon pair: e⁻e⁺ → γ → μ⁻μ⁺
# Vertex positions
v1x, v1y = 0.25, 0.50
v2x, v2y = 0.58, 0.50

# Fermion line endpoints
ext = 0.20

# Fermion segments with arrowhead direction
# Each row: line start → line end, with arrow pointing in direction of particle flow
segments = [
    (v1x - ext, v1y + ext, v1x, v1y),  # e⁻ incoming → v1
    (v1x, v1y, v1x - ext, v1y - ext),  # e⁺ (antiparticle arrow away)
    (v2x, v2y, v2x + ext, v2y + ext),  # μ⁻ outgoing from v2
    (v2x + ext, v2y - ext, v2x, v2y),  # μ⁺ (antiparticle arrow toward v2)
]

fermion_df = pd.DataFrame(segments, columns=["x", "y", "xend", "yend"])

# Arrowheads - simplified with vectorized computation
hl, hw = 0.022, 0.010
dx = fermion_df["xend"] - fermion_df["x"]
dy = fermion_df["yend"] - fermion_df["y"]
lens = np.sqrt(dx**2 + dy**2)
ux, uy = dx / lens, dy / lens
px, py = -uy, ux
mid_frac = 0.55
mx = fermion_df["x"] + mid_frac * dx
my = fermion_df["y"] + mid_frac * dy

arrow_df = pd.DataFrame(
    {
        "x_l": mx - hl * ux - hw * px,
        "y_l": my - hl * uy - hw * py,
        "x_r": mx - hl * ux + hw * px,
        "y_r": my - hl * uy + hw * py,
        "x_t": mx,
        "y_t": my,
    }
)

# Photon wavy line (v1 → v2)
t = np.linspace(0, 1, 400)
photon_df = pd.DataFrame({"x": v1x + t * (v2x - v1x), "y": v1y + 0.028 * np.sin(t * 7 * 2 * np.pi), "grp": 1})

# Legend line demonstrations (right side, vertically centered)
leg_x0 = 0.82
leg_len = 0.12
# Legend y positions: fermion=0.55, photon=0.47, gluon=0.39, boson=0.31
leg_ys = [0.55, 0.47, 0.39, 0.31]

# Gluon curly line for legend
t_g = np.linspace(0, 1, 500)
gluon_df = pd.DataFrame(
    {
        "x": leg_x0 + t_g * leg_len + 0.008 * np.sin(t_g * 9 * 2 * np.pi),
        "y": leg_ys[2] + 0.018 * np.sin(t_g * 9 * 2 * np.pi + np.pi / 2),
        "grp": 1,
    }
)

# Boson dashed line for legend
boson_leg_df = pd.DataFrame({"x": [leg_x0], "xend": [leg_x0 + leg_len], "y": [leg_ys[3]], "yend": [leg_ys[3]]})

# Photon wavy line for legend
t_pw = np.linspace(0, 1, 200)
photon_leg_df = pd.DataFrame(
    {"x": leg_x0 + t_pw * leg_len, "y": leg_ys[1] + 0.012 * np.sin(t_pw * 5 * 2 * np.pi), "grp": 1}
)

# Vertices
vertex_df = pd.DataFrame({"x": [v1x, v2x], "y": [v1y, v2y]})

# Particle labels - positioned to avoid legend area
labels_df = pd.DataFrame(
    {
        "x": [v1x - ext - 0.03, v1x - ext - 0.03, v2x + ext + 0.02, v2x + ext + 0.02, (v1x + v2x) / 2],
        "y": [v1y + ext + 0.02, v1y - ext - 0.02, v2y + ext + 0.03, v2y - ext - 0.03, v1y + 0.045],
        "label": ["e\u207b", "e\u207a", "\u03bc\u207b", "\u03bc\u207a", "\u03b3"],
    }
)

# Time arrow
time_y = 0.18
time_df = pd.DataFrame({"x": [0.25], "xend": [0.58], "y": [time_y], "yend": [time_y]})
time_head_df = pd.DataFrame(
    {"x": [0.57, 0.57], "y": [time_y + 0.01, time_y - 0.01], "xend": [0.58, 0.58], "yend": [time_y, time_y]}
)
time_lbl_df = pd.DataFrame({"x": [0.415], "y": [time_y - 0.04], "label": ["time"]})

# Legend: all 4 particle types (right side, vertically centered)
leg_labels_df = pd.DataFrame(
    {"x": [0.96, 0.96, 0.96, 0.96], "y": leg_ys, "label": ["Fermion", "Photon", "Gluon", "Boson"]}
)
leg_title_df = pd.DataFrame({"x": [0.88], "y": [0.63], "label": ["Particle Types"]})

# Fermion legend line
fermion_leg_df = pd.DataFrame({"x": [leg_x0], "xend": [leg_x0 + leg_len], "y": [leg_ys[0]], "yend": [leg_ys[0]]})

# Fermion legend arrowhead
fla_mx, fla_my = 0.89, leg_ys[0]
fla_hl, fla_hw = 0.015, 0.007
fermion_leg_arrow = pd.DataFrame(
    {
        "x_l": [fla_mx - fla_hl - fla_hw * 0],
        "y_l": [fla_my - fla_hw],
        "x_r": [fla_mx - fla_hl + fla_hw * 0],
        "y_r": [fla_my + fla_hw],
        "x_t": [fla_mx],
        "y_t": [fla_my],
    }
)

# Plot assembly
BLUE = "#306998"
GOLD = "#D4973B"
TEAL = "#2A9D8F"
PURPLE = "#7B2D8E"
DARK = "#1A1A1A"
GRAY = "#AAAAAA"

plot = (
    ggplot()
    # --- Main diagram ---
    # Fermion lines
    + geom_segment(data=fermion_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), size=2.0, color=BLUE)
    # Arrowheads (two sides of V)
    + geom_segment(data=arrow_df, mapping=aes(x="x_l", y="y_l", xend="x_t", yend="y_t"), size=2.0, color=BLUE)
    + geom_segment(data=arrow_df, mapping=aes(x="x_r", y="y_r", xend="x_t", yend="y_t"), size=2.0, color=BLUE)
    # Photon wavy line
    + geom_path(data=photon_df, mapping=aes(x="x", y="y", group="grp"), size=2.0, color=GOLD)
    # Vertices
    + geom_point(data=vertex_df, mapping=aes(x="x", y="y"), size=10, color=DARK, shape=16)
    # Particle labels
    + geom_text(data=labels_df, mapping=aes(x="x", y="y", label="label"), size=22, color=DARK, fontface="italic")
    # Time arrow
    + geom_segment(data=time_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), size=1.0, color=GRAY)
    + geom_segment(data=time_head_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), size=1.0, color=GRAY)
    + geom_text(data=time_lbl_df, mapping=aes(x="x", y="y", label="label"), size=16, color=GRAY, fontface="italic")
    # --- Legend: all 4 particle types ---
    + geom_text(
        data=leg_title_df, mapping=aes(x="x", y="y", label="label"), size=18, color=DARK, fontface="bold", hjust=0.5
    )
    # Fermion legend line + arrow
    + geom_segment(data=fermion_leg_df, mapping=aes(x="x", y="y", xend="xend", yend="yend"), size=2.0, color=BLUE)
    + geom_segment(data=fermion_leg_arrow, mapping=aes(x="x_l", y="y_l", xend="x_t", yend="y_t"), size=2.0, color=BLUE)
    + geom_segment(data=fermion_leg_arrow, mapping=aes(x="x_r", y="y_r", xend="x_t", yend="y_t"), size=2.0, color=BLUE)
    # Photon legend wavy line
    + geom_path(data=photon_leg_df, mapping=aes(x="x", y="y", group="grp"), size=2.0, color=GOLD)
    # Gluon legend curly line
    + geom_path(data=gluon_df, mapping=aes(x="x", y="y", group="grp"), size=2.0, color=TEAL)
    # Boson legend dashed line
    + geom_segment(
        data=boson_leg_df,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),
        size=2.0,
        color=PURPLE,
        linetype="dashed",
    )
    # Legend labels
    + geom_text(data=leg_labels_df, mapping=aes(x="x", y="y", label="label"), size=16, color=DARK, hjust=0)
    # Styling
    + xlim(-0.02, 1.12)
    + ylim(0.08, 0.88)
    + labs(
        title="feynman-basic \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="Electron\u2013Positron Annihilation: e\u207be\u207a \u2192 \u03b3 \u2192 \u03bc\u207b\u03bc\u207a",
    )
    + theme(
        axis_title=element_blank(),
        axis_text=element_blank(),
        axis_ticks=element_blank(),
        axis_line=element_blank(),
        panel_grid=element_blank(),
        panel_background=element_rect(fill="white", color="white"),
        plot_background=element_rect(fill="white", color="white"),
        plot_title=element_text(size=24, face="bold", color="#1A3A5C"),
        plot_subtitle=element_text(size=18, color="#4A6B82"),
        legend_position="none",
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, filename="plot.png", path=".", scale=3)
ggsave(plot, filename="plot.html", path=".")

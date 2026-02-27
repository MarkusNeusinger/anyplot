""" pyplots.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 87/100 | Created: 2026-02-27
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    arrow,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_rect,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_identity,
    scale_fill_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Nonlinear transformation: signed sqrt spreads crowded upper levels
# and compresses the large n=1-to-n=2 gap (spec: "consider nonlinear scale")
def vis(energy):
    """Transform energy to visual position: sign(E)*sqrt(|E|)."""
    e = np.asarray(energy, dtype=float)
    result = np.sign(e) * np.sqrt(np.abs(e))
    return float(result) if result.ndim == 0 else result


# Data — Hydrogen atom energy levels (En = -13.6/n² eV)
n_values = np.arange(1, 7)
energies = -13.6 / n_values**2
vis_e = vis(energies)

# Energy level lines (partial-width, as spec requires)
levels = pd.DataFrame({"y": vis_e, "x_start": 0.15, "x_end": 0.78})

# Endpoint dots at each end of level lines
endpoints = pd.DataFrame({"x": [0.15] * 6 + [0.78] * 6, "y": list(vis_e) * 2})

# Right-side labels — slight vertical nudge for n=5,6 to prevent overlap
label_y = list(vis_e[:4]) + [vis_e[4] + 0.05, vis_e[5] + 0.12]
labels_df = pd.DataFrame(
    {"y": label_y, "label": [f"n = {n}  ({e:.2f} eV)" for n, e in zip(n_values, energies, strict=True)], "x": 0.91}
)

# Thin connector lines from level endpoints to spread labels
connectors = pd.DataFrame({"x1": [0.79] * 6, "x2": [0.89] * 6, "y1": list(vis_e), "y2": label_y})

# Ionization limit at 0 eV (transformed)
ion_y = vis(0.0)
ion_label_y = 0.16

# Transitions — colorblind-safe palette (no similar blues)
# Lyman (UV) → cool tones: purple, deep indigo, magenta
# Balmer (visible) → warm + distinct: red, emerald, amber
energy_lookup = dict(zip(n_values, vis_e, strict=True))
transitions = pd.DataFrame(
    {
        "from_n": [2, 3, 4, 3, 4, 5],
        "to_n": [1, 1, 1, 2, 2, 2],
        "x_pos": [0.28, 0.36, 0.44, 0.54, 0.62, 0.70],
        "color": [
            "#7B2FBE",  # Ly-α  purple
            "#4338CA",  # Ly-β  deep indigo (distinct from emerald Hβ)
            "#DB2777",  # Ly-γ  magenta
            "#DC2626",  # Hα   red
            "#059669",  # Hβ   emerald (was sky-blue → now maximally distinct)
            "#D97706",  # Hγ   amber
        ],
        "label": ["Ly-α\n122 nm", "Ly-β\n103 nm", "Ly-γ\n97 nm", "Hα\n656 nm", "Hβ\n486 nm", "Hγ\n434 nm"],
    }
)
transitions["y_start"] = transitions["from_n"].map(energy_lookup) - 0.04
transitions["y_end"] = transitions["to_n"].map(energy_lookup) + 0.08
transitions["label_y"] = (transitions["y_start"] + transitions["y_end"]) / 2

# Series group labels above the diagram
series_labels = pd.DataFrame(
    {
        "x": [0.36, 0.62],
        "y": [0.30, 0.30],
        "label": ["Lyman Series (UV)", "Balmer Series (Visible)"],
        "color": ["#7B2FBE", "#DC2626"],
    }
)

# Subtle shaded bands behind each series (visual grouping / storytelling)
series_bands = pd.DataFrame(
    {
        "xmin": [0.23, 0.49],
        "xmax": [0.49, 0.75],
        "ymin": [vis_e[0] - 0.12, vis_e[1] - 0.12],
        "ymax": [vis_e[3] + 0.08, vis_e[4] + 0.08],
        "fill": ["#EDE9FE", "#FEE2E2"],
    }
)

# Y-axis: show real eV values at transformed tick positions
y_breaks = [vis(-13.6), vis(-3.4), vis(-1.5), vis(-0.85), 0.0]
y_labels = ["-13.6", "-3.4", "-1.5", "-0.85", "0"]

# Build plot — layered grammar: bands → levels → ionization → connectors → labels → arrows
plot = (
    ggplot()
    # Background bands for series grouping
    + geom_rect(
        data=series_bands, mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="fill"), alpha=0.35
    )
    + scale_fill_identity()
    # Energy level lines
    + geom_segment(data=levels, mapping=aes(x="x_start", xend="x_end", y="y", yend="y"), color="#306998", size=2.0)
    + geom_point(data=endpoints, mapping=aes(x="x", y="y"), color="#306998", size=3)
    # Ionization limit (dashed reference line + label)
    + annotate("segment", x=0.15, xend=0.78, y=ion_y, yend=ion_y, color="#9CA3AF", size=1.2, linetype="dashed")
    + annotate("text", x=0.91, y=ion_label_y, label="Ionization\nlimit (0 eV)", size=10, ha="left", color="#6B7280")
    # Connector lines from level endpoints to spread labels
    + geom_segment(data=connectors, mapping=aes(x="x1", xend="x2", y="y1", yend="y2"), color="#D1D5DB", size=0.4)
    # Ionization limit connector
    + annotate("segment", x=0.79, xend=0.89, y=ion_y, yend=ion_label_y, color="#D1D5DB", size=0.4)
    # Level labels (right side)
    + geom_text(data=labels_df, mapping=aes(x="x", y="y", label="label"), size=10, ha="left", color="#1F2937")
    # Transition arrows (emission = downward)
    + geom_segment(
        data=transitions,
        mapping=aes(x="x_pos", xend="x_pos", y="y_start", yend="y_end", color="color"),
        size=1.2,
        arrow=arrow(length=0.08, type="closed"),
    )
    # Transition wavelength labels
    + geom_text(
        data=transitions, mapping=aes(x="x_pos", y="label_y", label="label", color="color"), size=10, nudge_x=-0.045
    )
    # Series group labels at top
    + geom_text(data=series_labels, mapping=aes(x="x", y="y", label="label", color="color"), size=11)
    + scale_color_identity()
    + scale_x_continuous(limits=(0.0, 1.18), expand=(0, 0))
    + scale_y_continuous(name="Energy (eV)", breaks=y_breaks, labels=y_labels)
    + coord_cartesian(ylim=(vis(-13.6) - 0.25, 0.52))
    + labs(
        title="energy-level-atomic · plotnine · pyplots.ai",
        subtitle="Hydrogen Atom Emission Spectrum  —  Lyman (UV) & Balmer (Visible) Series",
        x="",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color="#1a1a2e"),
        plot_subtitle=element_text(size=15, color="#6B7280", margin={"b": 14}),
        axis_title_y=element_text(size=20, color="#374151"),
        axis_title_x=element_blank(),
        axis_text_y=element_text(size=16),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_minor_y=element_blank(),
        panel_grid_major_y=element_line(alpha=0.12, color="#CBD5E1"),
        plot_background=element_rect(fill="#FAFBFC", color="none"),
        panel_background=element_rect(fill="#FAFBFC", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300)

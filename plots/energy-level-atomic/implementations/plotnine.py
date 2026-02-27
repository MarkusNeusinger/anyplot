"""pyplots.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 84/100 | Created: 2026-02-27
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
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Hydrogen atom energy levels (En = -13.6/n² eV)
n_values = np.arange(1, 7)
energies = -13.6 / n_values**2

# Level lines
levels = pd.DataFrame({"energy": energies, "x_start": 0.18, "x_end": 0.76})

# Endpoint markers for level lines (dots at each end to distinguish crowded upper levels)
endpoints = pd.DataFrame({"x": [0.18] * 6 + [0.76] * 6, "energy": list(energies) * 2})

# Right-side labels with spread y-positions to avoid overlap for upper levels
display_y = [-13.6, -3.4, -1.51, -0.85, -0.10, 0.55]
labels_df = pd.DataFrame(
    {
        "energy": energies,
        "display_y": display_y,
        "label": [f"n = {n}  ({e:.2f} eV)" for n, e in zip(n_values, energies, strict=True)],
        "label_x": 0.90,
    }
)

# Thin connecting lines from level endpoints to label positions
connectors = pd.DataFrame({"x_start": [0.77] * 6, "x_end": [0.88] * 6, "y_start": list(energies), "y_end": display_y})

# Ionization limit connector (line and label use annotate below)
ion_connector = pd.DataFrame({"x_start": [0.77], "x_end": [0.88], "y_start": [0.0], "y_end": [1.25]})

# Transitions - Lyman series (UV, to n=1) and Balmer series (visible, to n=2)
energy_map = dict(zip(n_values, energies, strict=True))
transitions = pd.DataFrame(
    {
        "from_n": [2, 3, 4, 3, 4, 5],
        "to_n": [1, 1, 1, 2, 2, 2],
        "x_pos": [0.30, 0.37, 0.44, 0.54, 0.61, 0.68],
        "color": ["#7B2FBE", "#2563EB", "#DB2777", "#DC2626", "#0EA5E9", "#D97706"],
        "label": [
            "Ly-\u03b1\n122 nm",
            "Ly-\u03b2\n103 nm",
            "Ly-\u03b3\n97 nm",
            "H\u03b1\n656 nm",
            "H\u03b2\n486 nm",
            "H\u03b3\n434 nm",
        ],
    }
)
transitions["y_start"] = transitions["from_n"].map(energy_map) - 0.1
transitions["y_end"] = transitions["to_n"].map(energy_map) + 0.2
transitions["label_y"] = (transitions["y_start"] + transitions["y_end"]) / 2

# Series group labels
series_labels = pd.DataFrame(
    {
        "x": [0.37, 0.61],
        "y": [1.6, 1.6],
        "label": ["Lyman Series (UV)", "Balmer Series (Visible)"],
        "color": ["#7B2FBE", "#DC2626"],
    }
)

# Plot — uses annotate() for fixed reference elements (plotnine-idiomatic)
plot = (
    ggplot()
    + geom_segment(
        data=levels, mapping=aes(x="x_start", xend="x_end", y="energy", yend="energy"), color="#306998", size=1.8
    )
    + geom_point(data=endpoints, mapping=aes(x="x", y="energy"), color="#306998", size=2.5)
    # Ionization limit via annotate (no DataFrame needed for fixed references)
    + annotate("segment", x=0.18, xend=0.76, y=0, yend=0, color="#9CA3AF", size=1, linetype="dashed")
    + annotate("text", x=0.90, y=1.25, label="Ionization\nlimit (0 eV)", size=9, ha="left", color="#9CA3AF")
    + geom_segment(
        data=connectors, mapping=aes(x="x_start", xend="x_end", y="y_start", yend="y_end"), color="#CCCCCC", size=0.3
    )
    + geom_segment(
        data=ion_connector, mapping=aes(x="x_start", xend="x_end", y="y_start", yend="y_end"), color="#CCCCCC", size=0.3
    )
    + geom_text(
        data=labels_df, mapping=aes(x="label_x", y="display_y", label="label"), size=9, ha="left", color="#333333"
    )
    + geom_segment(
        data=transitions,
        mapping=aes(x="x_pos", xend="x_pos", y="y_start", yend="y_end", color="color"),
        size=1.1,
        arrow=arrow(length=0.08, type="closed"),
    )
    + geom_text(
        data=transitions, mapping=aes(x="x_pos", y="label_y", label="label", color="color"), size=9, nudge_x=-0.04
    )
    + geom_text(data=series_labels, mapping=aes(x="x", y="y", label="label", color="color"), size=9)
    + scale_color_identity()
    + scale_x_continuous(limits=(0.0, 1.18), expand=(0, 0))
    + scale_y_continuous(
        name="Energy (eV)", breaks=[-13.6, -3.4, -1.5, -0.85, 0], labels=["-13.6", "-3.4", "-1.5", "-0.85", "0"]
    )
    + coord_cartesian(ylim=(-14.2, 2.3))
    + labs(
        title="energy-level-atomic \u00b7 plotnine \u00b7 pyplots.ai",
        subtitle="Hydrogen Atom Emission Spectrum  \u2014  Lyman (UV) & Balmer (Visible) Series",
        x="",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", color="#1a1a2e"),
        plot_subtitle=element_text(size=14, color="#6B7280", margin={"b": 12}),
        axis_title_y=element_text(size=20),
        axis_title_x=element_blank(),
        axis_text_y=element_text(size=16),
        axis_text_x=element_blank(),
        axis_ticks_major_x=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_minor_x=element_blank(),
        panel_grid_minor_y=element_blank(),
        panel_grid_major_y=element_line(alpha=0.15),
        plot_background=element_rect(fill="#FAFBFC", color="none"),
    )
)

# Save
plot.save("plot.png", dpi=300)

""" pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-06
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    guides,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_size_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - transcription factor binding site motif (10 positions, DNA)
position_freqs = {
    1: {"A": 0.05, "C": 0.80, "G": 0.05, "T": 0.10},
    2: {"A": 0.70, "C": 0.05, "G": 0.20, "T": 0.05},
    3: {"A": 0.05, "C": 0.05, "G": 0.85, "T": 0.05},
    4: {"A": 0.10, "C": 0.10, "G": 0.10, "T": 0.70},
    5: {"A": 0.25, "C": 0.25, "G": 0.25, "T": 0.25},
    6: {"A": 0.60, "C": 0.10, "G": 0.20, "T": 0.10},
    7: {"A": 0.05, "C": 0.05, "G": 0.05, "T": 0.85},
    8: {"A": 0.90, "C": 0.02, "G": 0.05, "T": 0.03},
    9: {"A": 0.05, "C": 0.10, "G": 0.75, "T": 0.10},
    10: {"A": 0.15, "C": 0.55, "G": 0.15, "T": 0.15},
}

# Calculate information content and build stacked letter segments
records = []
for pos, freqs in position_freqs.items():
    ic = 2.0
    for f in freqs.values():
        if f > 0:
            ic += f * np.log2(f)

    sorted_letters = sorted(freqs.items(), key=lambda x: x[1])

    y_bottom = 0.0
    for letter, freq in sorted_letters:
        height = freq * ic
        if height > 0.001:
            records.append(
                {
                    "position": pos,
                    "letter": letter,
                    "ymin": y_bottom,
                    "ymax": y_bottom + height,
                    "y_mid": y_bottom + height / 2,
                    "height": height,
                }
            )
            y_bottom += height

df = pd.DataFrame(records)
bar_half_width = 0.44
df["xmin"] = df["position"] - bar_half_width
df["xmax"] = df["position"] + bar_half_width

# Scale font size so letters visually fill their segments as glyphs
# The letter IS the primary visual element (sequence logo convention)
max_height = df["height"].max()
df["fontsize"] = df["height"] * (64 / max_height)
df["fontsize"] = df["fontsize"].clip(lower=5)

# Only show letters on segments tall enough to be readable
df_visible = df[df["height"] > 0.02].copy()

# Colorblind-safe DNA color scheme
dna_colors = {"A": "#009E73", "C": "#0072B2", "G": "#E69F00", "T": "#CC79A7"}

# Highlight most conserved position for data storytelling
highlight_pos = 8
highlight_ymax = df[df["position"] == highlight_pos]["ymax"].max()
df_highlight = pd.DataFrame(
    {"xmin": [highlight_pos - 0.48], "xmax": [highlight_pos + 0.48], "ymin": [-0.02], "ymax": [highlight_ymax + 0.04]}
)

# Plot - colored letters as primary visual elements (sequence logo style)
plot = (
    ggplot(df)
    # Storytelling: highlight most conserved position
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        data=df_highlight,
        fill="#FFF9C4",
        color=None,
        alpha=0.5,
    )
    # Very subtle background rectangles to define segment boundaries
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="letter"), alpha=0.08, color="#FFFFFF", size=0.2
    )
    # Colored bold letters: the primary visual element (scaled glyphs)
    + geom_text(
        aes(x="position", y="y_mid", label="letter", color="letter", size="fontsize"),
        data=df_visible,
        fontweight="bold",
        show_legend=False,
    )
    + scale_fill_manual(values=dna_colors)
    + scale_color_manual(values=dna_colors, name="Nucleotide")
    + scale_size_identity()
    + guides(fill="none")
    + scale_x_continuous(breaks=range(1, 11), minor_breaks=[])
    + scale_y_continuous(expand=(0, 0, 0.05, 0))
    + coord_cartesian(ylim=(0, None))
    + annotate(
        "text",
        x=highlight_pos,
        y=highlight_ymax + 0.09,
        label="most conserved",
        size=10,
        color="#555555",
        fontstyle="italic",
    )
    + labs(
        x="Position",
        y="Information content (bits)",
        title="sequence-logo-basic \u00b7 plotnine \u00b7 pyplots.ai",
        color="Nucleotide",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=16, weight="bold"),
        legend_text=element_text(size=14),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.3),
        axis_line_x=element_line(color="#333333", size=0.8),
        axis_line_y=element_line(color="#333333", size=0.8),
        plot_background=element_rect(fill="#FAFAFA", color=None),
        panel_background=element_rect(fill="#FAFAFA", color=None),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)

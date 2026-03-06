""" pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 77/100 | Created: 2026-03-06
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    labs,
    scale_fill_manual,
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

# Calculate information content and build stacked rectangles
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
bar_half_width = 0.42
df["xmin"] = df["position"] - bar_half_width
df["xmax"] = df["position"] + bar_half_width

# Separate large and small segments for different text sizes
df_large = df[df["height"] > 0.15].copy()
df_medium = df[(df["height"] > 0.05) & (df["height"] <= 0.15)].copy()

# DNA color scheme
dna_colors = {"A": "#2ca02c", "C": "#1f77b4", "G": "#ff7f0e", "T": "#d62728"}

# Plot
plot = (
    ggplot(df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="letter"))
    + geom_text(
        aes(x="position", y="y_mid", label="letter"),
        data=df_large,
        fontweight="bold",
        color="white",
        size=18,
        show_legend=False,
    )
    + geom_text(
        aes(x="position", y="y_mid", label="letter"),
        data=df_medium,
        fontweight="bold",
        color="white",
        size=10,
        show_legend=False,
    )
    + scale_fill_manual(values=dna_colors)
    + scale_x_continuous(breaks=range(1, 11), minor_breaks=[])
    + scale_y_continuous(expand=(0, 0, 0.05, 0))
    + labs(
        x="Position",
        y="Information content (bits)",
        title="sequence-logo-basic \u00b7 plotnine \u00b7 pyplots.ai",
        fill="Nucleotide",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color="#333333", size=0.8),
        axis_line_y=element_line(color="#333333", size=0.8),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)

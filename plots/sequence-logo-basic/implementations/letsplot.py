""" pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-06
"""

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data — 10-position DNA transcription factor binding site motif
positions = list(range(1, 11))

# Realistic motif frequencies (resembling a TATA-box-like binding site)
frequencies = {
    1: {"A": 0.25, "C": 0.25, "G": 0.25, "T": 0.25},
    2: {"A": 0.10, "C": 0.05, "G": 0.05, "T": 0.80},
    3: {"A": 0.85, "C": 0.05, "G": 0.05, "T": 0.05},
    4: {"A": 0.05, "C": 0.05, "G": 0.05, "T": 0.85},
    5: {"A": 0.90, "C": 0.02, "G": 0.02, "T": 0.06},
    6: {"A": 0.60, "C": 0.05, "G": 0.05, "T": 0.30},
    7: {"A": 0.15, "C": 0.05, "G": 0.70, "T": 0.10},
    8: {"A": 0.05, "C": 0.80, "G": 0.10, "T": 0.05},
    9: {"A": 0.30, "C": 0.30, "G": 0.20, "T": 0.20},
    10: {"A": 0.25, "C": 0.25, "G": 0.25, "T": 0.25},
}

# Color scheme: A=green, C=blue, G=orange, T=red
color_map = {"A": "#2CA02C", "C": "#1F77B4", "G": "#FF7F0E", "T": "#D62728"}

# Calculate information content and build letter data
rows = []
max_info = 0.0
for pos in positions:
    freqs = frequencies[pos]
    entropy = -sum(f * np.log2(f) for f in freqs.values() if f > 0)
    info_content = 2.0 - entropy

    # Sort by frequency (least frequent at bottom, most frequent on top)
    sorted_letters = sorted(freqs.items(), key=lambda x: x[1])

    y_bottom = 0.0
    for letter, freq in sorted_letters:
        height = freq * info_content
        if height < 0.04:
            y_bottom += height
            continue
        rows.append(
            {
                "position": pos,
                "xmin": pos - 0.45,
                "xmax": pos + 0.45,
                "ymin": y_bottom,
                "ymax": y_bottom + height,
                "ymid": y_bottom + height / 2,
                "height": height,
                "letter": letter,
                "frequency": freq,
                "info_bits": round(info_content, 3),
            }
        )
        y_bottom += height
    if info_content > max_info:
        max_info = info_content

df = pd.DataFrame(rows)

# Legend data — invisible points to create a proper legend with square symbols
legend_df = pd.DataFrame({"x": [0] * 4, "y": [0] * 4, "letter": ["A", "C", "G", "T"]})

# Y-axis upper limit: round up to nearest 0.2 with small padding
y_max = np.ceil(max_info * 5) / 5 + 0.05

# Build plot with colored letters as the primary visual element
plot = (
    ggplot()
    # Subtle background rectangles for structure
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="letter"),
        data=df,
        alpha=0.15,
        color="rgba(0,0,0,0)",
        size=0,
        show_legend=False,
    )
    # Colored letter glyphs — the primary visual element
    + geom_text(
        aes(x="position", y="ymid", label="letter", color="letter", size="height"),
        data=df,
        fontface="bold",
        show_legend=False,
        tooltips=layer_tooltips()
        .format("@frequency", ".0%")
        .format("@info_bits", ".3f")
        .line("@letter")
        .line("Frequency: @frequency")
        .line("Info content: @info_bits bits"),
    )
    # Invisible points for proper legend (square shape shows color blocks)
    + geom_point(
        aes(x="x", y="y", fill="letter"),
        data=legend_df,
        size=6,
        shape=22,
        color="rgba(0,0,0,0)",
        alpha=0,
        tooltips="none",
    )
    # Manual color scales
    + scale_fill_manual(values=color_map, name="Nucleotide", breaks=["A", "C", "G", "T"])
    + scale_color_manual(values=color_map)
    + scale_size(range=[6, 36], guide="none")
    + scale_x_continuous(breaks=positions, limits=[0.3, 10.7])
    + scale_y_continuous(limits=[0, y_max], breaks=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4])
    + guides(fill=guide_legend(override_aes={"size": 12, "alpha": 1.0}))
    + labs(x="Position", y="Information content (bits)", title="sequence-logo-basic \u00b7 letsplot \u00b7 pyplots.ai")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        axis_title=element_text(size=22),
        axis_text=element_text(size=18),
        legend_title=element_text(size=20, face="bold"),
        legend_text=element_text(size=18),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.5),
        plot_background=element_rect(color="white", fill="white"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", scale=3, path=".")
ggsave(plot, "plot.html", path=".")

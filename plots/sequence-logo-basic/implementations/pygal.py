""" pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: pygal 3.1.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-06
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — ETS transcription factor binding site motif (10 positions)
frequencies = {
    1: {"A": 0.40, "C": 0.20, "G": 0.25, "T": 0.15},
    2: {"A": 0.10, "C": 0.05, "G": 0.80, "T": 0.05},
    3: {"A": 0.05, "C": 0.05, "G": 0.85, "T": 0.05},
    4: {"A": 0.90, "C": 0.03, "G": 0.04, "T": 0.03},
    5: {"A": 0.85, "C": 0.05, "G": 0.05, "T": 0.05},
    6: {"A": 0.05, "C": 0.05, "G": 0.05, "T": 0.85},
    7: {"A": 0.05, "C": 0.05, "G": 0.05, "T": 0.85},
    8: {"A": 0.25, "C": 0.30, "G": 0.20, "T": 0.25},
    9: {"A": 0.15, "C": 0.35, "G": 0.35, "T": 0.15},
    10: {"A": 0.30, "C": 0.20, "G": 0.30, "T": 0.20},
}

nucleotides = ["A", "C", "G", "T"]
max_entropy = 2.0  # bits for DNA

# Calculate information content at each position
info_content = {}
for pos, freqs in frequencies.items():
    entropy = 0
    for nt in nucleotides:
        f = freqs[nt]
        if f > 0:
            entropy -= f * np.log2(f)
    info_content[pos] = max_entropy - entropy

# Scale each nucleotide height by frequency * information content
# Build per-nucleotide series with letter labels inside bars
stacked_data = {nt: [] for nt in nucleotides}
for pos in sorted(frequencies.keys()):
    ic = info_content[pos]
    for nt in nucleotides:
        height = round(frequencies[pos][nt] * ic, 4)
        # Show nucleotide letter inside bar for significant segments
        show_letter = height >= 0.12
        stacked_data[nt].append(
            {
                "value": height,
                "label": f"Pos {pos}: {nt} = {frequencies[pos][nt]:.0%} × {ic:.2f} bits",
                "formatter": lambda x, letter=nt, show=show_letter: letter if show else "",
            }
        )

# Style — refined DNA colors with strong contrast
# Conserved core emphasis through color saturation; softer grid
custom_style = Style(
    background="white",
    plot_background="#fafafa",
    foreground="#2d2d2d",
    foreground_strong="#1a1a1a",
    foreground_subtle="#eeeeee",
    colors=("#0d7a22", "#1d4ed8", "#d97706", "#b91c1c"),
    opacity=0.95,
    opacity_hover=1.0,
    title_font_size=34,
    label_font_size=22,
    major_label_font_size=20,
    legend_font_size=22,
    value_font_size=22,
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    major_label_font_family="sans-serif",
    legend_font_family="sans-serif",
    value_font_family="monospace",
    tooltip_font_size=18,
    tooltip_font_family="monospace",
)

# Plot
chart = pygal.StackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="sequence-logo-basic · pygal · pyplots.ai",
    x_title="Position",
    y_title="Information content (bits)",
    show_x_guides=False,
    show_y_guides=True,
    show_minor_y_labels=False,
    margin=60,
    margin_bottom=100,
    spacing=8,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=28,
    print_values=True,
    print_values_position="center",
    rounded_bars=2,
    y_labels_major_count=5,
    truncate_legend=-1,
    tooltip_border_radius=8,
    tooltip_fancy_mode=True,
    min_scale=0,
    range=(0, 1.5),
    x_label_rotation=0,
    js=[],
)

# Custom x-labels with motif annotation
chart.x_labels = [str(pos) for pos in sorted(frequencies.keys())]

for nt in nucleotides:
    chart.add(nt, stacked_data[nt])

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")

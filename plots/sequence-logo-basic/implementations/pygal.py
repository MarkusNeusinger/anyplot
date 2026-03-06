""" pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: pygal 3.1.0 | Python 3.14.3
Quality: 74/100 | Created: 2026-03-06
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — ETS transcription factor binding site motif (10 positions)
np.random.seed(42)

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
# Sort by frequency at each position (smallest first for stacking)
stacked_data = {nt: [] for nt in nucleotides}
for pos in sorted(frequencies.keys()):
    ic = info_content[pos]
    sorted_nts = sorted(nucleotides, key=lambda n: frequencies[pos][n])
    for nt in nucleotides:
        stacked_data[nt].append(round(frequencies[pos][nt] * ic, 4))

# Style — standard DNA colors: A=green, C=blue, G=orange, T=red
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#cccccc",
    colors=("#2ca02c", "#1f77b4", "#ff7f0e", "#d62728"),
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=18,
    value_font_size=14,
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
    margin=50,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    print_values=False,
    rounded_bars=2,
)

chart.x_labels = [str(pos) for pos in sorted(frequencies.keys())]

for nt in nucleotides:
    chart.add(nt, stacked_data[nt])

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")

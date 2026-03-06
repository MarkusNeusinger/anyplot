"""pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: pygal 3.1.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-06
"""

import numpy as np
import pygal
from pygal.style import Style


# Data — ETS transcription factor binding site motif (10 positions)
# Positions 2-7 form the conserved GGAATT core
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

# Identify conserved core (IC > 0.5 bits) for visual emphasis
core_positions = {pos for pos, ic in info_content.items() if ic > 0.5}

# Scale each nucleotide height by frequency * information content
# Build per-nucleotide series with letter labels inside bars
stacked_data = {nt: [] for nt in nucleotides}
for pos in sorted(frequencies.keys()):
    ic = info_content[pos]
    for nt in nucleotides:
        height = round(frequencies[pos][nt] * ic, 4)
        show_letter = height >= 0.10
        is_core = pos in core_positions
        stacked_data[nt].append(
            {
                "value": height,
                "label": (
                    f"{'[core] ' if is_core else ''}Pos {pos}: {nt} = {frequencies[pos][nt]:.0%} x {ic:.2f} bits"
                ),
                "formatter": (lambda x, letter=nt, show=show_letter: letter if show else ""),
            }
        )

# Colorblind-safe DNA palette: teal A, blue C, amber G, purple T
# Avoids red-green confusion while maintaining visual distinctiveness
custom_style = Style(
    background="white",
    plot_background="#f8f9fa",
    foreground="#2d2d2d",
    foreground_strong="#111111",
    foreground_subtle="#e0e0e0",
    colors=("#0f766e", "#1d4ed8", "#d97706", "#7c3aed"),
    opacity=0.92,
    opacity_hover=1.0,
    title_font_size=36,
    label_font_size=22,
    major_label_font_size=20,
    legend_font_size=22,
    value_font_size=24,
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    major_label_font_family="sans-serif",
    legend_font_family="sans-serif",
    value_font_family="monospace",
    tooltip_font_size=18,
    tooltip_font_family="monospace",
)

# X-labels: mark conserved core positions for emphasis
x_labels = []
for pos in sorted(frequencies.keys()):
    if pos in core_positions:
        label = f"*{pos}*"
    else:
        label = str(pos)
    x_labels.append(label)

# Plot
chart = pygal.StackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="sequence-logo-basic · pygal · pyplots.ai",
    x_title="Position (* = conserved core, IC > 0.5 bits)",
    y_title="Information content (bits)",
    show_x_guides=False,
    show_y_guides=True,
    show_minor_y_labels=False,
    margin=60,
    margin_bottom=120,
    spacing=6,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=28,
    print_values=True,
    print_values_position="center",
    rounded_bars=3,
    y_labels_major_count=6,
    truncate_legend=-1,
    tooltip_border_radius=10,
    tooltip_fancy_mode=True,
    min_scale=0,
    range=(0, 1.6),
    x_label_rotation=0,
    secondary_style=custom_style,
    inner_radius=0,
    js=[],
)

chart.x_labels = x_labels

for nt in nucleotides:
    chart.add(nt, stacked_data[nt])

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")

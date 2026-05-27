""" anyplot.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: pygal 3.1.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pygal
from pygal.style import Style


np.random.seed(42)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Chromosome lengths (simplified, in Mb)
chrom_lengths = {
    "1": 249,
    "2": 243,
    "3": 198,
    "4": 191,
    "5": 182,
    "6": 171,
    "7": 159,
    "8": 146,
    "9": 141,
    "10": 136,
    "11": 135,
    "12": 134,
    "13": 115,
    "14": 107,
    "15": 102,
    "16": 90,
    "17": 83,
    "18": 80,
    "19": 59,
    "20": 64,
    "21": 47,
    "22": 51,
}

chromosomes = list(chrom_lengths.keys())
n_snps_per_chrom = 500

# Storage for data
all_chroms = []
all_cumulative_pos = []
all_pvalues = []

# Track chromosome boundaries for x-axis labels
chrom_midpoints = []
cumulative_offset = 0

for chrom in chromosomes:
    length = chrom_lengths[chrom]
    positions = np.sort(np.random.uniform(0, length, n_snps_per_chrom))

    # Store chromosome midpoint for x-axis label
    chrom_midpoints.append(cumulative_offset + length / 2)

    # Generate p-values: mostly uniform with some significant hits
    pvalues = np.random.uniform(0, 1, n_snps_per_chrom)

    # Add significant peaks on selected chromosomes
    if chrom in ["6", "11", "16"]:
        n_sig = np.random.randint(3, 8)
        sig_indices = np.random.choice(n_snps_per_chrom, n_sig, replace=False)
        pvalues[sig_indices] = 10 ** (-np.random.uniform(8, 15, n_sig))

    # Add suggestive signals
    n_sugg = np.random.randint(5, 15)
    sugg_indices = np.random.choice(n_snps_per_chrom, n_sugg, replace=False)
    pvalues[sugg_indices] = 10 ** (-np.random.uniform(5, 8, n_sugg))

    cumulative_positions = positions + cumulative_offset
    all_chroms.extend([chrom] * n_snps_per_chrom)
    all_cumulative_pos.extend(cumulative_positions)
    all_pvalues.extend(pvalues)

    cumulative_offset += length

# Convert to -log10 p-values
neg_log_pvalues = -np.log10(np.array(all_pvalues))

# Thresholds
genome_wide_sig = -np.log10(5e-8)  # ~7.3
suggestive_sig = 5.0  # -log10(1e-5)

# Custom style with theme-adaptive colors
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
)

# Create XY scatter chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="manhattan-gwas · pygal · anyplot.ai",
    x_title="Chromosome",
    y_title="-log₁₀(p-value)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=16,
    stroke=False,
    dots_size=4,
    show_x_guides=False,
    show_y_guides=True,
    truncate_label=-1,
    print_values=False,
    x_label_rotation=0,
    range=(0, 16),
    xrange=(0, cumulative_offset),
    tooltip_border_radius=5,
    explicit_size=True,
    spacing=20,
    margin=50,
    margin_bottom=150,
    margin_top=80,
)

# Set x-axis labels at chromosome midpoints
chart.x_labels = chrom_midpoints


def format_x_label(x_val):
    """Find closest chromosome midpoint and return chromosome number."""
    if not chrom_midpoints:
        return ""
    min_dist = float("inf")
    closest_idx = 0
    for i, pos in enumerate(chrom_midpoints):
        dist = abs(x_val - pos)
        if dist < min_dist:
            min_dist = dist
            closest_idx = i
    # Only return label if close to midpoint
    if min_dist < 50:
        return str(closest_idx + 1)
    return ""


chart.x_value_formatter = lambda x: format_x_label(x)

# Prepare data by chromosome with alternating colors
odd_chrom_points = []
even_chrom_points = []
significant_points = []

for idx, chrom in enumerate(chromosomes):
    chrom_mask = [c == chrom for c in all_chroms]
    chrom_x = [all_cumulative_pos[j] for j in range(len(all_chroms)) if chrom_mask[j]]
    chrom_y = [neg_log_pvalues[j] for j in range(len(all_chroms)) if chrom_mask[j]]

    for x, y in zip(chrom_x, chrom_y, strict=True):
        point = {"value": (x, y), "label": f"Chr {chrom}: {x:.1f} Mb, -log₁₀(p)={y:.2f}"}
        if y >= genome_wide_sig:
            significant_points.append(point)
        elif idx % 2 == 0:
            odd_chrom_points.append(point)
        else:
            even_chrom_points.append(point)

# Add data series
chart.add("Odd chromosomes", odd_chrom_points, stroke=False, show_dots=True)
chart.add("Even chromosomes", even_chrom_points, stroke=False, show_dots=True)
chart.add("Significant (p<5×10⁻⁸)", significant_points, stroke=False, show_dots=True)

# Add threshold lines
n_line_points = 200
threshold_x = np.linspace(10, cumulative_offset - 10, n_line_points)

gw_line_points = [
    {"value": (x, genome_wide_sig), "label": f"Genome-wide threshold: -log₁₀(5×10⁻⁸) = {genome_wide_sig:.1f}"}
    for x in threshold_x
]
chart.add("p = 5×10⁻⁸ threshold", gw_line_points, stroke=True, show_dots=True, dots_size=2)

sugg_line_points = [
    {"value": (x, suggestive_sig), "label": f"Suggestive threshold: -log₁₀(1×10⁻⁵) = {suggestive_sig:.1f}"}
    for x in threshold_x
]
chart.add("p = 1×10⁻⁵ threshold", sugg_line_points, stroke=True, show_dots=True, dots_size=2)

# Save outputs
chart.render_to_file(f"plot-{THEME}.html")
chart.render_to_png(f"plot-{THEME}.png")

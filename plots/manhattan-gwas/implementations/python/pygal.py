""" pyplots.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: pygal 3.1.0 | Python 3.13.11
Quality: 82/100 | Created: 2025-12-31
"""

import numpy as np
import pygal
from pygal.style import Style


# Seed for reproducibility
np.random.seed(42)

# Chromosome lengths (simplified, in Mb scale)
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

# Custom style with explicit colors for threshold lines
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=(
        "#306998",  # Blue - odd chromosomes
        "#888888",  # Gray - even chromosomes
        "#D62728",  # Red - significant points above threshold
        "#D62728",  # Red - genome-wide threshold line
        "#FF7F0E",  # Orange - suggestive threshold line
    ),
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=32,
    value_font_size=20,
    font_family="sans-serif",
)

# Create XY scatter chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="manhattan-gwas · pygal · pyplots.ai",
    x_title="Chromosome",
    y_title="-log₁₀(p-value)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=24,
    stroke=False,
    dots_size=5,
    show_x_guides=False,
    show_y_guides=True,
    truncate_label=-1,
    print_values=False,
    x_label_rotation=0,
    range=(0, 16),
    xrange=(0, cumulative_offset),
    tooltip_border_radius=10,
    explicit_size=True,
    spacing=30,
    margin=60,
    margin_bottom=200,
    margin_top=100,
)

# Create x_labels with chromosome numbers at midpoints
# Use string labels for chromosomes 1-22
chart.x_labels = [str(i + 1) for i in range(len(chromosomes))]
chart.x_labels_major_count = len(chromosomes)

# Map positions to display label indices
# We need to normalize x values to show chromosome labels
# Pygal XY chart needs numeric x_labels for scatter, so we'll use custom formatter
label_positions = chrom_midpoints.copy()


def format_x_label(x_val):
    """Find closest chromosome midpoint and return chromosome number."""
    if not label_positions:
        return ""
    min_dist = float("inf")
    closest_idx = 0
    for i, pos in enumerate(label_positions):
        dist = abs(x_val - pos)
        if dist < min_dist:
            min_dist = dist
            closest_idx = i
    # Only return label if close to midpoint (within half chromosome width)
    if min_dist < 50:
        return str(closest_idx + 1)
    return ""


# Set numeric x_labels at chromosome midpoints
chart.x_labels = chrom_midpoints
chart.x_value_formatter = lambda x: format_x_label(x) if x in chrom_midpoints else ""

# Prepare data by chromosome with alternating colors
odd_chrom_points = []
even_chrom_points = []
significant_points = []  # Points above genome-wide significance

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

# Add chromosome data series (blue for odd, gray for even)
chart.add("Odd chromosomes", odd_chrom_points, stroke=False, show_dots=True)
chart.add("Even chromosomes", even_chrom_points, stroke=False, show_dots=True)

# Add significant points as separate series (highlighted)
chart.add("Significant (p<5×10⁻⁸)", significant_points, stroke=False, show_dots=True)

# Add threshold lines as dense scatter points (works better in PNG than stroke)
# Using many small dots to create visible line effect
n_line_points = 200
threshold_x = np.linspace(10, cumulative_offset - 10, n_line_points)

# Genome-wide significance threshold line (y ≈ 7.3)
gw_line_points = [
    {"value": (x, genome_wide_sig), "label": f"Genome-wide threshold: -log₁₀(5×10⁻⁸) = {genome_wide_sig:.1f}"}
    for x in threshold_x
]
chart.add("p = 5×10⁻⁸ threshold", gw_line_points, stroke=True, show_dots=True, dots_size=2)

# Suggestive threshold line (y = 5)
sugg_line_points = [
    {"value": (x, suggestive_sig), "label": f"Suggestive threshold: -log₁₀(1×10⁻⁵) = {suggestive_sig:.1f}"}
    for x in threshold_x
]
chart.add("p = 1×10⁻⁵ threshold", sugg_line_points, stroke=True, show_dots=True, dots_size=2)

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")

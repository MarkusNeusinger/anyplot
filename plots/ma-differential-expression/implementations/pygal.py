"""pyplots.ai
ma-differential-expression: MA Plot for Differential Expression
Library: pygal 3.1.0 | Python 3.14.3
Quality: 76/100 | Created: 2026-03-20
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Simulated RNA-seq differential expression results
np.random.seed(42)
n_genes = 15000

# Mean expression (A values) - log2 scale, typical RNA-seq range
mean_expression = np.random.exponential(scale=3, size=n_genes) + 1

# Log fold change (M values) - most genes near zero, some truly differentially expressed
log_fold_change = np.random.normal(0, 0.3, n_genes)

# Add truly differentially expressed genes (~8% upregulated, ~7% downregulated)
n_up = 1200
n_down = 1050
up_idx = np.random.choice(n_genes, n_up, replace=False)
remaining = np.setdiff1d(np.arange(n_genes), up_idx)
down_idx = np.random.choice(remaining, n_down, replace=False)

log_fold_change[up_idx] = np.random.normal(2.5, 0.8, n_up)
log_fold_change[down_idx] = np.random.normal(-2.2, 0.7, n_down)

# Simulate p-values (significant for DE genes, noise for others)
p_values = np.ones(n_genes)
p_values[up_idx] = 10 ** (-np.random.uniform(2, 10, n_up))
p_values[down_idx] = 10 ** (-np.random.uniform(2, 10, n_down))
noise_idx = np.setdiff1d(np.arange(n_genes), np.concatenate([up_idx, down_idx]))
p_values[noise_idx] = np.random.uniform(0.01, 1.0, len(noise_idx))

# Significance threshold
significant = p_values < 0.05

# Gene names for top DE genes
gene_names = [f"Gene{i}" for i in range(n_genes)]
top_genes = ["BRCA1", "TP53", "MYC", "EGFR", "KRAS", "PTEN", "CDK2", "RB1", "AKT1", "VEGFA"]
top_idx = np.argsort(p_values)[: len(top_genes)]
for i, name in zip(top_idx, top_genes, strict=False):
    gene_names[i] = name

# LOESS-like smoothing curve (binned moving average with additional smoothing)
sort_order = np.argsort(mean_expression)
sorted_a = mean_expression[sort_order]
sorted_m = log_fold_change[sort_order]

n_bins = 30
bin_edges = np.percentile(sorted_a, np.linspace(0, 100, n_bins + 1))
raw_x = []
raw_y = []
for b in range(n_bins):
    mask = (sorted_a >= bin_edges[b]) & (sorted_a < bin_edges[b + 1])
    if mask.sum() > 20:
        raw_x.append(float(np.median(sorted_a[mask])))
        raw_y.append(float(np.mean(sorted_m[mask])))

# Apply moving average smoothing
smooth_y = np.array(raw_y)
for _ in range(4):
    smoothed = np.copy(smooth_y)
    for j in range(1, len(smoothed) - 1):
        smoothed[j] = (smooth_y[j - 1] + smooth_y[j] + smooth_y[j + 1]) / 3
    smooth_y = smoothed
smooth_x = raw_x

# Style - white background for maximum contrast
custom_style = Style(
    background="#FAFAFA",
    plot_background="#FFFFFF",
    foreground="#2C3E50",
    foreground_strong="#1A252F",
    foreground_subtle="#E8E8E8",
    colors=(
        "#6B8DAA",  # non-significant: steel blue (visible on white)
        "#C0392B",  # significant: deep red
        "#2471A3",  # M=0 line: strong blue
        "#5D6D7E",  # +1 threshold: dark slate
        "#5D6D7E",  # -1 threshold: dark slate (same)
        "#E67E22",  # LOESS curve: bold orange
        "#1A252F",  # gene labels: dark
    ),
    title_font_size=48,
    label_font_size=38,
    major_label_font_size=36,
    legend_font_size=30,
    value_font_size=22,
    tooltip_font_size=24,
    stroke_width=3,
    opacity=0.85,
    opacity_hover=0.95,
)

# Subsample for performance (pygal renders each point as SVG element)
np.random.seed(42)
n_display = 3000
sig_mask = significant
nonsig_mask = ~significant

# Keep all significant genes, subsample non-significant
sig_indices = np.where(sig_mask)[0]
nonsig_indices = np.where(nonsig_mask)[0]
nonsig_sample = np.random.choice(nonsig_indices, min(n_display - len(sig_indices), len(nonsig_indices)), replace=False)
display_indices = np.concatenate([sig_indices, nonsig_sample])

# Prepare data points with rich tooltips using pygal's node dict format
nonsig_points = []
sig_points = []

for i in display_indices:
    point = {
        "value": (round(float(mean_expression[i]), 2), round(float(log_fold_change[i]), 2)),
        "label": f"{gene_names[i]} | A={mean_expression[i]:.1f}, M={log_fold_change[i]:.2f}, p={p_values[i]:.2e}",
    }
    if significant[i]:
        sig_points.append(point)
    else:
        nonsig_points.append(point)

# Prepare labeled gene points (top 10 most significant genes)
labeled_points = []
for i in top_idx:
    labeled_points.append(
        {
            "value": (round(float(mean_expression[i]), 2), round(float(log_fold_change[i]), 2)),
            "label": f"{gene_names[i]} (p={p_values[i]:.2e})",
        }
    )

# Create XY chart with pygal SVG features
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="ma-differential-expression \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Mean Expression (A)",
    y_title="Log\u2082 Fold Change (M)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=7,
    legend_box_size=24,
    dots_size=10,
    stroke=False,
    show_x_guides=False,
    show_y_guides=True,
    truncate_legend=-1,
    print_values=False,
    dynamic_print_values=True,
    js=[],
    x_label_rotation=0,
)

# Non-significant genes (visible on white background, larger dots)
chart.add("Not Significant", nonsig_points, dots_size=12)

# Significant genes (deep red, on top)
chart.add("Significant (p < 0.05)", sig_points, dots_size=9)

# Reference lines
x_min = 0
x_max = float(np.max(mean_expression[display_indices])) + 1

# M = 0 line (no change)
chart.add("M = 0 (no change)", [(x_min, 0), (x_max, 0)], stroke=True, show_dots=False, stroke_style={"width": 5})

# M = +1 threshold (2-fold up)
chart.add(
    "+2-fold threshold",
    [(x_min, 1), (x_max, 1)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 4, "dasharray": "12, 6"},
)

# M = -1 threshold (2-fold down)
chart.add(
    "\u22122-fold threshold",
    [(x_min, -1), (x_max, -1)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 4, "dasharray": "12, 6"},
)

# LOESS smoothing curve - bold orange with dots for high visibility
chart.add(
    "LOESS trend",
    [(round(x, 2), round(y, 3)) for x, y in zip(smooth_x, smooth_y, strict=False)],
    stroke=True,
    show_dots=True,
    dots_size=6,
    stroke_style={"width": 8},
)

# Top DE gene labels as a separate series with visible dots
chart.add("Top DE genes", labeled_points, dots_size=14, stroke=False)

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")

"""pyplots.ai
ma-differential-expression: MA Plot for Differential Expression
Library: pygal 3.1.0 | Python 3.14.3
Quality: 71/100 | Created: 2026-03-20
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

n_bins = 25
# Use percentile-based bins for even point distribution
bin_edges = np.percentile(sorted_a, np.linspace(0, 100, n_bins + 1))
raw_x = []
raw_y = []
for b in range(n_bins):
    mask = (sorted_a >= bin_edges[b]) & (sorted_a < bin_edges[b + 1])
    if mask.sum() > 20:
        raw_x.append(float(np.median(sorted_a[mask])))
        raw_y.append(float(np.mean(sorted_m[mask])))

# Apply triple moving average for smooth curve
smooth_y = np.array(raw_y)
for _ in range(4):
    smoothed = np.copy(smooth_y)
    for j in range(1, len(smoothed) - 1):
        smoothed[j] = (smooth_y[j - 1] + smooth_y[j] + smooth_y[j + 1]) / 3
    smooth_y = smoothed
smooth_x = raw_x

# Style - warm background with visible non-significant points
custom_style = Style(
    background="#FAFAF7",
    plot_background="#F4F1EB",
    foreground="#2C3E50",
    foreground_strong="#1A252F",
    foreground_subtle="#D0CEC8",
    colors=(
        "#5B7B94",  # non-significant: dark steel blue (strong contrast on cream)
        "#C0392B",  # significant: deep red
        "#2471A3",  # M=0 line: strong blue
        "#5D6D7E",  # threshold lines: dark slate
        "#1E8449",  # LOESS curve: forest green
    ),
    title_font_size=48,
    label_font_size=38,
    major_label_font_size=36,
    legend_font_size=30,
    value_font_size=22,
    tooltip_font_size=24,
    stroke_width=3,
    opacity=0.75,
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

# Prepare data points with rich tooltips
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

# Create XY chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="ma-differential-expression \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Mean Expression (A)",
    y_title="Log\u2082 Fold Change (M)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=24,
    dots_size=6,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
    truncate_legend=-1,
    print_values=False,
    dynamic_print_values=True,
    js=[],
)

# Non-significant genes (steel gray, visible on cream background)
chart.add("Not Significant", nonsig_points)

# Significant genes (deep red, on top)
chart.add("Significant (p < 0.05)", sig_points)

# Reference lines
x_min = 0
x_max = float(np.max(mean_expression[display_indices])) + 1

# M = 0 line (no change)
chart.add("M = 0 (no change)", [(x_min, 0), (x_max, 0)], stroke=True, show_dots=False, stroke_style={"width": 4})

# M = ±1 threshold (2-fold change) - combined into single legend entry
chart.add(
    "\u00b12-fold threshold",
    [(x_min, 1), (x_max, 1), (None, None), (x_min, -1), (x_max, -1)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 3, "dasharray": "10, 6"},
)

# LOESS smoothing curve
chart.add(
    "LOESS trend",
    [(round(x, 2), round(y, 3)) for x, y in zip(smooth_x, smooth_y, strict=False)],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 5},
)

# Save
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")

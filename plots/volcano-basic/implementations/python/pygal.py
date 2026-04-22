"""pyplots.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: pygal 3.1.0 | Python 3.13.11
Quality: 75/100 | Created: 2025-12-31
"""

import numpy as np
import pygal
from pygal.style import Style


# Data - Simulated differential gene expression results
np.random.seed(42)
n_genes = 500

# Gene names for annotations
gene_names = [f"GENE{i:03d}" for i in range(n_genes)]

# Generate fold changes (mostly near zero, some with larger effects)
log2_fc = np.concatenate(
    [
        np.random.normal(0, 0.5, 400),  # Non-significant genes
        np.random.normal(2.5, 0.5, 50),  # Up-regulated
        np.random.normal(-2.5, 0.5, 50),  # Down-regulated
    ]
)

# Generate p-values (correlated with effect size)
base_pval = np.random.uniform(0.001, 0.9, n_genes)
# Significant genes have lower p-values
base_pval[400:] = np.random.uniform(0.0001, 0.01, 100)
neg_log10_pval = -np.log10(base_pval)

# Classification thresholds
fc_threshold = 1.0  # log2 fold change threshold (2-fold)
pval_threshold = 1.3  # -log10(0.05) ≈ 1.3

# Classify genes
up_regulated = (log2_fc > fc_threshold) & (neg_log10_pval > pval_threshold)
down_regulated = (log2_fc < -fc_threshold) & (neg_log10_pval > pval_threshold)
not_significant = ~(up_regulated | down_regulated)

# Colorblind-safe palette: gray, orange, blue, dark gray for threshold lines
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#888888", "#E69F00", "#0072B2", "#555555", "#555555", "#555555"),  # Gray, Orange, Blue, Dark gray x3
    title_font_size=56,
    label_font_size=36,
    major_label_font_size=32,
    legend_font_size=40,
    value_font_size=24,
    stroke_width=2,
    opacity=0.7,
    opacity_hover=1.0,
    font_family="DejaVu Sans",
)

# Calculate axis ranges - tight fitting to data (y starts at 0)
y_max = float(np.ceil(max(neg_log10_pval) + 0.3))
x_min = float(np.floor(min(log2_fc) - 0.3))
x_max = float(np.ceil(max(log2_fc) + 0.3))

# Generate y-axis labels from 0 to max (positive only)
y_labels = [i * 0.5 for i in range(int(y_max / 0.5) + 2)]

# Create XY chart (scatter plot)
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="volcano-basic · pygal · pyplots.ai",
    x_title="Log₂ Fold Change",
    y_title="-Log₁₀(p-value)",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=32,
    dots_size=10,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
    x_label_rotation=0,
    range=(x_min, x_max),
    include_x_axis=True,
    explicit_size=True,
    truncate_legend=-1,
    spacing=40,
    margin=30,
    margin_bottom=120,
)

# Set y-axis labels to start from 0 (all data is positive)
chart.y_labels = y_labels

# Prepare data points for each category with gene labels for tooltips
not_sig_points = [
    {"value": (float(log2_fc[i]), float(neg_log10_pval[i])), "label": gene_names[i]}
    for i in range(n_genes)
    if not_significant[i]
]
up_points = [
    {"value": (float(log2_fc[i]), float(neg_log10_pval[i])), "label": gene_names[i]}
    for i in range(n_genes)
    if up_regulated[i]
]
down_points = [
    {"value": (float(log2_fc[i]), float(neg_log10_pval[i])), "label": gene_names[i]}
    for i in range(n_genes)
    if down_regulated[i]
]

# Add data series
chart.add("Not Significant", not_sig_points)
chart.add("Up-regulated", up_points)
chart.add("Down-regulated", down_points)

# Add threshold lines as line series (dashed lines for significance cutoffs)
# Horizontal line at p-value threshold (y = 1.3)
h_line_points = [(x_min, pval_threshold), (x_max, pval_threshold)]
chart.add("p=0.05", h_line_points, stroke=True, show_dots=False, stroke_style={"width": 4, "dasharray": "12, 6"})

# Vertical lines at fold change thresholds (x = ±1, representing 2-fold change)
# Each vertical line as separate series to avoid diagonal connections
v_line_neg = [(float(-fc_threshold), 0.0), (float(-fc_threshold), float(y_max))]
v_line_pos = [(float(fc_threshold), 0.0), (float(fc_threshold), float(y_max))]
chart.add("FC=-2", v_line_neg, stroke=True, show_dots=False, stroke_style={"width": 4, "dasharray": "12, 6"})
chart.add("FC=+2", v_line_pos, stroke=True, show_dots=False, stroke_style={"width": 4, "dasharray": "12, 6"})

# Save as PNG and HTML
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")

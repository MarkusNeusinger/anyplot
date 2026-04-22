""" pyplots.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, Span
from bokeh.plotting import figure


# Data - Simulated differential expression results
np.random.seed(42)
n_genes = 2000

# Generate log2 fold changes (effect sizes)
log2_fc = np.random.normal(0, 1.5, n_genes)

# Generate p-values: most genes non-significant, some highly significant
# Use inverse relationship with fold change magnitude for realism
base_pvals = np.random.uniform(0.001, 1, n_genes)
# Genes with larger fold changes tend to have lower p-values
fold_effect = np.abs(log2_fc) / np.max(np.abs(log2_fc))
pvals = base_pvals * (1 - 0.7 * fold_effect) + 0.01 * np.random.random(n_genes)
pvals = np.clip(pvals, 1e-50, 1)

neg_log10_pval = -np.log10(pvals)

# Significance thresholds
pval_threshold = -np.log10(0.05)  # ~1.3
fc_threshold = 1.0  # log2(2) = 1

# Classify points by significance
significant_up = (neg_log10_pval > pval_threshold) & (log2_fc > fc_threshold)
significant_down = (neg_log10_pval > pval_threshold) & (log2_fc < -fc_threshold)

# Create separate data sources for each category (enables proper legend)
source_up = ColumnDataSource(data={"x": log2_fc[significant_up], "y": neg_log10_pval[significant_up]})

source_down = ColumnDataSource(data={"x": log2_fc[significant_down], "y": neg_log10_pval[significant_down]})

source_ns = ColumnDataSource(
    data={"x": log2_fc[~(significant_up | significant_down)], "y": neg_log10_pval[~(significant_up | significant_down)]}
)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="volcano-basic · bokeh · pyplots.ai",
    x_axis_label="Log₂ Fold Change",
    y_axis_label="-Log₁₀ (P-value)",
)

# Plot points by category (non-significant first, then significant on top)
p.scatter(x="x", y="y", source=source_ns, color="#AAAAAA", size=18, alpha=0.5, legend_label="Not significant")

p.scatter(x="x", y="y", source=source_down, color="#306998", size=25, alpha=0.7, legend_label="Down-regulated")

p.scatter(x="x", y="y", source=source_up, color="#D62728", size=25, alpha=0.7, legend_label="Up-regulated")

# Add threshold lines
# Horizontal line for p-value threshold
hline = Span(
    location=pval_threshold, dimension="width", line_color="#333333", line_dash="dashed", line_width=3, line_alpha=0.7
)
p.add_layout(hline)

# Vertical lines for fold change thresholds
vline_pos = Span(
    location=fc_threshold, dimension="height", line_color="#333333", line_dash="dashed", line_width=3, line_alpha=0.7
)
p.add_layout(vline_pos)

vline_neg = Span(
    location=-fc_threshold, dimension="height", line_color="#333333", line_dash="dashed", line_width=3, line_alpha=0.7
)
p.add_layout(vline_neg)

# Styling - scaled for 4800x2700 canvas
p.title.text_font_size = "36pt"
p.title.align = "center"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = "dotted"

# Background
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "#FFFFFF"

# Legend styling
p.legend.location = "top_right"
p.legend.label_text_font_size = "22pt"
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.spacing = 15
p.legend.padding = 20
p.legend.background_fill_alpha = 0.8
p.legend.border_line_width = 2
p.legend.border_line_color = "#CCCCCC"

# Save
export_png(p, filename="plot.png")

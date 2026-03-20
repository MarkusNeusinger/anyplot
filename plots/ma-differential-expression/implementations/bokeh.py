""" pyplots.ai
ma-differential-expression: MA Plot for Differential Expression
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Label, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data: Simulated RNA-seq differential expression results
np.random.seed(42)
n_genes = 15000

# Mean expression (A values) - log2 scale, typical range 0-16
mean_expression = np.random.gamma(shape=2.5, scale=2.5, size=n_genes)

# Log fold change (M values) - most genes near zero
log_fold_change = np.random.normal(0, 0.4, n_genes)

# Add truly differentially expressed genes (~8% of total)
n_de = int(n_genes * 0.08)
de_indices = np.random.choice(n_genes, n_de, replace=False)
log_fold_change[de_indices] = np.random.choice([-1, 1], n_de) * np.random.uniform(1.0, 4.0, n_de)

# Generate p-values: small for DE genes, random for others
p_values = np.ones(n_genes)
p_values[de_indices] = 10 ** (-np.random.uniform(2, 10, n_de))
p_values[~np.isin(np.arange(n_genes), de_indices)] = np.random.uniform(0.01, 1.0, n_genes - n_de)

# Significance threshold
significant = p_values < 0.05

# Separate sources for legend
sig_mask = significant
nonsig_mask = ~significant

source_nonsig = ColumnDataSource(data={"x": mean_expression[nonsig_mask], "y": log_fold_change[nonsig_mask]})

source_sig = ColumnDataSource(data={"x": mean_expression[sig_mask], "y": log_fold_change[sig_mask]})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="ma-differential-expression · bokeh · pyplots.ai",
    x_axis_label="Mean Expression (log₂)",
    y_axis_label="Log₂ Fold Change (M)",
    toolbar_location=None,
)

# Non-significant genes (gray, behind)
p.scatter(x="x", y="y", source=source_nonsig, size=8, color="#B0B0B0", alpha=0.2, legend_label="Not Significant")

# Significant genes (red, on top)
p.scatter(
    x="x",
    y="y",
    source=source_sig,
    size=12,
    color="#E63946",
    alpha=0.6,
    legend_label=f"Significant (n={sig_mask.sum():,})",
)

# Reference lines
zero_line = Span(location=0, dimension="width", line_color="#306998", line_width=2.5)
p.add_layout(zero_line)

upper_fc = Span(location=1, dimension="width", line_color="#306998", line_width=2, line_dash="dashed")
p.add_layout(upper_fc)

lower_fc = Span(location=-1, dimension="width", line_color="#306998", line_width=2, line_dash="dashed")
p.add_layout(lower_fc)

# Smoothing curve via binned moving average
sort_idx = np.argsort(mean_expression)
x_sorted = mean_expression[sort_idx]
y_sorted = log_fold_change[sort_idx]

n_bins = 100
bin_edges = np.linspace(x_sorted.min(), x_sorted.max(), n_bins + 1)
bin_centers = []
bin_means = []
for i in range(n_bins):
    mask = (x_sorted >= bin_edges[i]) & (x_sorted < bin_edges[i + 1])
    if mask.sum() > 5:
        bin_centers.append((bin_edges[i] + bin_edges[i + 1]) / 2)
        bin_means.append(np.mean(y_sorted[mask]))

bin_centers = np.array(bin_centers)
bin_means = np.array(bin_means)

# Smooth with moving average (window=11)
window = 11
pad = window // 2
padded = np.pad(bin_means, pad, mode="edge")
y_smooth = np.convolve(padded, np.ones(window) / window, mode="valid")

smooth_source = ColumnDataSource(data={"x": bin_centers, "y": y_smooth})
p.line(x="x", y="y", source=smooth_source, line_width=4, color="#FFD43B", legend_label="LOESS Trend")

# Fold-change threshold labels
x_max = mean_expression.max()
label_x = x_max * 0.85

upper_label = Label(
    x=label_x, y=1, text="FC = 2", text_font_size="18pt", text_color="#306998", text_baseline="bottom", y_offset=5
)
p.add_layout(upper_label)

lower_label = Label(
    x=label_x, y=-1, text="FC = −2", text_font_size="18pt", text_color="#306998", text_baseline="top", y_offset=-5
)
p.add_layout(lower_label)

# Styling
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

p.xgrid.grid_line_alpha = 0.2
p.ygrid.grid_line_alpha = 0.2

p.legend.label_text_font_size = "18pt"
p.legend.location = "top_left"
p.legend.background_fill_alpha = 0.8

p.background_fill_color = "white"
p.border_fill_color = "white"

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="MA Plot for Differential Expression")

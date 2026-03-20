"""pyplots.ai
ma-differential-expression: MA Plot for Differential Expression
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, HoverTool, Label, LinearColorMapper, Range1d, Span
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.transform import transform


# Data: Simulated RNA-seq differential expression results
np.random.seed(42)
n_genes = 15000

# Gene names
gene_prefixes = [
    "BRCA",
    "TP",
    "MYC",
    "EGFR",
    "KRAS",
    "PTEN",
    "AKT",
    "MAPK",
    "STAT",
    "JAK",
    "CDK",
    "RB",
    "VEGF",
    "HIF",
    "TNF",
    "IL",
    "NOTCH",
    "WNT",
    "SHH",
    "FGF",
    "SOX",
    "PAX",
    "HOX",
    "GATA",
    "FOXP",
    "RUNX",
    "ETS",
    "MMP",
    "COL",
    "FN",
]
gene_names = [f"{gene_prefixes[i % len(gene_prefixes)]}{i}" for i in range(n_genes)]

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
neg_log10_p = -np.log10(np.clip(p_values, 1e-15, 1.0))

# Separate sources for legend
sig_mask = significant
nonsig_mask = ~significant

source_nonsig = ColumnDataSource(
    data={
        "x": mean_expression[nonsig_mask],
        "y": log_fold_change[nonsig_mask],
        "gene": [gene_names[i] for i in np.where(nonsig_mask)[0]],
        "pval": p_values[nonsig_mask],
        "neg_log10_p": neg_log10_p[nonsig_mask],
    }
)

source_sig = ColumnDataSource(
    data={
        "x": mean_expression[sig_mask],
        "y": log_fold_change[sig_mask],
        "gene": [gene_names[i] for i in np.where(sig_mask)[0]],
        "pval": p_values[sig_mask],
        "neg_log10_p": neg_log10_p[sig_mask],
    }
)

# Clamp x-axis to remove sparse right tail
x_limit = np.percentile(mean_expression, 99)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="ma-differential-expression · bokeh · pyplots.ai",
    x_axis_label="Mean Expression (log\u2082)",
    y_axis_label="Log\u2082 Fold Change (M)",
    toolbar_location=None,
    x_range=Range1d(-0.5, x_limit + 0.5),
)

# Color mapper for significant genes by -log10(p) using Inferno-inspired palette
inferno_palette = [
    "#FCFFA4",
    "#F7D03C",
    "#FB9906",
    "#ED6925",
    "#CF4446",
    "#A52C60",
    "#781C6D",
    "#4B0C6B",
    "#1B0C41",
    "#000004",
]
color_mapper = LinearColorMapper(
    palette=inferno_palette,
    low=neg_log10_p[sig_mask].min() if sig_mask.sum() > 0 else 0,
    high=neg_log10_p[sig_mask].max() if sig_mask.sum() > 0 else 10,
)

# Non-significant genes (gray, behind)
r_nonsig = p.scatter(
    x="x", y="y", source=source_nonsig, size=7, color="#C0C0C0", alpha=0.15, legend_label="Not Significant"
)

# Significant genes with color mapped by significance strength
r_sig = p.scatter(
    x="x",
    y="y",
    source=source_sig,
    size=11,
    color=transform("neg_log10_p", color_mapper),
    alpha=0.65,
    legend_label=f"Significant (n={sig_mask.sum():,})",
)

# HoverTool for significant genes only
hover = HoverTool(
    renderers=[r_sig],
    tooltips=[("Gene", "@gene"), ("Mean Expr", "@x{0.2f}"), ("Log\u2082 FC", "@y{0.2f}"), ("p-value", "@pval{0.2e}")],
)
p.add_tools(hover)

# Reference lines
zero_line = Span(location=0, dimension="width", line_color="#306998", line_width=2.5, line_alpha=0.8)
p.add_layout(zero_line)

upper_fc = Span(location=1, dimension="width", line_color="#306998", line_width=1.8, line_dash="dashed", line_alpha=0.6)
p.add_layout(upper_fc)

lower_fc = Span(
    location=-1, dimension="width", line_color="#306998", line_width=1.8, line_dash="dashed", line_alpha=0.6
)
p.add_layout(lower_fc)

# Smoothing curve via binned moving average
sort_idx = np.argsort(mean_expression)
x_sorted = mean_expression[sort_idx]
y_sorted = log_fold_change[sort_idx]

# Only use data within visible range
vis_mask = x_sorted <= x_limit
x_vis = x_sorted[vis_mask]
y_vis = y_sorted[vis_mask]

n_bins = 80
bin_edges = np.linspace(x_vis.min(), x_vis.max(), n_bins + 1)
bin_centers = []
bin_means = []
for i in range(n_bins):
    mask = (x_vis >= bin_edges[i]) & (x_vis < bin_edges[i + 1])
    if mask.sum() > 5:
        bin_centers.append((bin_edges[i] + bin_edges[i + 1]) / 2)
        bin_means.append(np.mean(y_vis[mask]))

bin_centers = np.array(bin_centers)
bin_means = np.array(bin_means)

# Smooth with moving average (window=11)
window = 11
pad = window // 2
padded = np.pad(bin_means, pad, mode="edge")
y_smooth = np.convolve(padded, np.ones(window) / window, mode="valid")

smooth_source = ColumnDataSource(data={"x": bin_centers, "y": y_smooth})
p.line(x="x", y="y", source=smooth_source, line_width=4, color="#2D6A4F", alpha=0.85, legend_label="LOESS Trend")

# Fold-change threshold labels
label_x = x_limit * 0.88

upper_label = Label(
    x=label_x,
    y=1,
    text="FC = 2",
    text_font_size="20pt",
    text_color="#306998",
    text_baseline="bottom",
    y_offset=5,
    text_font_style="italic",
)
p.add_layout(upper_label)

lower_label = Label(
    x=label_x,
    y=-1,
    text="FC = \u22122",
    text_font_size="20pt",
    text_color="#306998",
    text_baseline="top",
    y_offset=-5,
    text_font_style="italic",
)
p.add_layout(lower_label)

# Annotate top DE genes by |fold change| * -log10(p)
sig_indices = np.where(sig_mask)[0]
if len(sig_indices) > 0:
    de_score = np.abs(log_fold_change[sig_indices]) * neg_log10_p[sig_indices]
    top_n = 8
    top_local = np.argsort(de_score)[-top_n:]
    top_global = sig_indices[top_local]

    for idx in top_global:
        gx = mean_expression[idx]
        gy = log_fold_change[idx]
        if gx <= x_limit:
            label = Label(
                x=gx,
                y=gy,
                text=f" {gene_names[idx]}",
                text_font_size="17pt",
                text_color="#1a1a2e",
                text_font_style="bold",
                x_offset=8,
                y_offset=6,
            )
            p.add_layout(label)

# Summary annotation: upregulated vs downregulated counts
n_up = int(np.sum((significant) & (log_fold_change > 1)))
n_down = int(np.sum((significant) & (log_fold_change < -1)))
summary_label = Label(
    x=70,
    y=70,
    x_units="screen",
    y_units="screen",
    text=f"▲ {n_up} upregulated  ·  ▼ {n_down} downregulated  (|FC| > 2, p < 0.05)",
    text_font_size="18pt",
    text_color="#444444",
    text_font_style="italic",
)
p.add_layout(summary_label)

# ColorBar for significance gradient
color_bar = ColorBar(
    color_mapper=color_mapper,
    ticker=BasicTicker(desired_num_ticks=6),
    label_standoff=14,
    major_label_text_font_size="16pt",
    title="-log₁₀(p-value)",
    title_text_font_size="17pt",
    title_text_font_style="italic",
    title_standoff=12,
    width=28,
    location=(0, 0),
    padding=20,
)
p.add_layout(color_bar, "right")

# Styling
p.title.text_font_size = "28pt"
p.title.text_color = "#2C3E50"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_label_text_color = "#333333"
p.yaxis.axis_label_text_color = "#333333"

# Refined grid - y-axis only for cleaner appearance
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.2
p.ygrid.grid_line_dash = [4, 4]

# Remove spines for cleaner look
p.outline_line_color = None
p.xaxis.axis_line_color = "#666666"
p.yaxis.axis_line_color = "#666666"
p.xaxis.axis_line_width = 1.5
p.yaxis.axis_line_width = 1.5
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = "#666666"
p.yaxis.major_tick_line_color = "#666666"

# Legend styling
p.legend.label_text_font_size = "18pt"
p.legend.location = "top_left"
p.legend.background_fill_alpha = 0.85
p.legend.border_line_color = "#CCCCCC"
p.legend.border_line_width = 1
p.legend.padding = 12
p.legend.spacing = 8
p.legend.margin = 15

p.background_fill_color = "#FAFAFA"
p.border_fill_color = "white"

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="MA Plot for Differential Expression")

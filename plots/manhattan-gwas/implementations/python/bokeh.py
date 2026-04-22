""" pyplots.ai
manhattan-gwas: Manhattan Plot for GWAS
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label, Span
from bokeh.plotting import figure


# Data - Simulated GWAS data with significant peaks
np.random.seed(42)

# Chromosome sizes (simplified, in millions of base pairs)
chrom_sizes = {
    "1": 248,
    "2": 242,
    "3": 198,
    "4": 190,
    "5": 181,
    "6": 170,
    "7": 159,
    "8": 145,
    "9": 138,
    "10": 133,
    "11": 135,
    "12": 133,
    "13": 114,
    "14": 107,
    "15": 101,
    "16": 90,
    "17": 83,
    "18": 80,
    "19": 58,
    "20": 64,
    "21": 46,
    "22": 50,
}

# Generate SNP data
n_snps_per_chrom = 2000
data = []
cumulative_pos = 0
chrom_centers = {}

for chrom, size in chrom_sizes.items():
    # Random positions within chromosome
    positions = np.sort(np.random.randint(1, size * 1_000_000, n_snps_per_chrom))

    # Base p-values (mostly non-significant)
    p_values = np.random.uniform(0.001, 1.0, n_snps_per_chrom)

    # Add some significant peaks for certain chromosomes
    if chrom in ["2", "6", "11", "17"]:
        # Add 5-15 significant SNPs per peak chromosome
        n_significant = np.random.randint(5, 15)
        peak_indices = np.random.choice(n_snps_per_chrom, n_significant, replace=False)
        p_values[peak_indices] = 10 ** np.random.uniform(-12, -8, n_significant)

    # Calculate cumulative position
    cumulative_positions = positions + cumulative_pos
    chrom_centers[chrom] = cumulative_pos + (size * 1_000_000) / 2

    for i in range(n_snps_per_chrom):
        data.append(
            {
                "chromosome": chrom,
                "position": positions[i],
                "cumulative_pos": cumulative_positions[i],
                "p_value": p_values[i],
                "neg_log_p": -np.log10(p_values[i]),
            }
        )

    cumulative_pos += size * 1_000_000

df = pd.DataFrame(data)

# Assign colors based on chromosome (alternating)
colors = ["#306998", "#7BA3C9"]  # Python Blue and lighter shade
df["color"] = df["chromosome"].apply(lambda x: colors[int(x) % 2])

# Highlight significant SNPs (above genome-wide threshold)
significance_threshold = -np.log10(5e-8)  # ~7.3
significant_mask = df["neg_log_p"] >= significance_threshold
df.loc[significant_mask, "color"] = "#FFD43B"  # Python Yellow for significant

# Adjust point sizes - smaller for non-significant, larger for significant
df["size"] = 6
df.loc[significant_mask, "size"] = 12

# Create plot
source = ColumnDataSource(df)

p = figure(
    width=4800,
    height=2700,
    title="manhattan-gwas · bokeh · pyplots.ai",
    x_axis_label="Genomic Position",
    y_axis_label="-log₁₀(p-value)",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Scatter plot
p.scatter(x="cumulative_pos", y="neg_log_p", source=source, size="size", color="color", alpha=0.7, line_color=None)

# Genome-wide significance threshold line (p < 5e-8)
significance_line = Span(
    location=significance_threshold, dimension="width", line_color="#E63946", line_dash="dashed", line_width=3
)
p.add_layout(significance_line)

# Suggestive threshold line (p < 1e-5)
suggestive_threshold = -np.log10(1e-5)  # = 5
suggestive_line = Span(
    location=suggestive_threshold, dimension="width", line_color="#2A9D8F", line_dash="dotted", line_width=2
)
p.add_layout(suggestive_line)

# Add threshold labels
sig_label = Label(
    x=cumulative_pos * 0.98,
    y=significance_threshold + 0.3,
    text="p = 5×10⁻⁸",
    text_font_size="16pt",
    text_color="#E63946",
)
p.add_layout(sig_label)

sug_label = Label(
    x=cumulative_pos * 0.98,
    y=suggestive_threshold + 0.3,
    text="p = 1×10⁻⁵",
    text_font_size="16pt",
    text_color="#2A9D8F",
)
p.add_layout(sug_label)

# Style the plot
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "16pt"
p.yaxis.major_label_text_font_size = "18pt"

# Hide x-axis tick labels (we'll add chromosome labels instead)
p.xaxis.major_label_text_font_size = "0pt"
p.xaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None

# Add chromosome labels below the plot
for chrom, center in chrom_centers.items():
    chrom_label = Label(x=center, y=-0.8, text=chrom, text_font_size="14pt", text_align="center", text_color="#333333")
    p.add_layout(chrom_label)

# Grid styling
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3

# Background
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "#FFFFFF"

# Axis styling
p.yaxis.axis_line_width = 2
p.xaxis.axis_line_width = 2

# Set y-axis range to show chromosome labels
p.y_range.start = -1.5
p.y_range.end = df["neg_log_p"].max() + 1

# Save PNG
export_png(p, filename="plot.png")

# Save HTML for interactivity
output_file("plot.html")
save(p)

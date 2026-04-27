"""anyplot.ai
qq-basic: Basic Q-Q Plot
Library: bokeh | Python 3.13
Quality: pending | Updated: 2026-04-27
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data - adult heights (cm) with a few outliers to showcase Q-Q interpretation
np.random.seed(42)
core = np.random.normal(loc=170, scale=8, size=88)
outliers = np.array([145.0, 147.0, 149.0, 196.0, 199.0, 202.0, 148.0, 198.0, 200.0, 203.0, 145.5, 201.5])
sample = np.concatenate([core, outliers])

# Theoretical and sample quantiles (standardised to z-scores)
sample_sorted = np.sort(sample)
n = len(sample_sorted)
probabilities = (np.arange(1, n + 1) - 0.5) / n
theoretical_quantiles = stats.norm.ppf(probabilities)

sample_mean = np.mean(sample)
sample_std = np.std(sample, ddof=1)
sample_quantiles = (sample_sorted - sample_mean) / sample_std

source = ColumnDataSource(
    data={"theoretical": theoretical_quantiles, "sample": sample_quantiles, "value": sample_sorted}
)

# Reference line (y=x, bounded to data range)
pad = 0.3
x_min = theoretical_quantiles.min() - pad
x_max = theoretical_quantiles.max() + pad

# Figure
p = figure(
    width=4800,
    height=2700,
    title="qq-basic · bokeh · anyplot.ai",
    x_axis_label="Theoretical Quantiles",
    y_axis_label="Sample Quantiles",
    toolbar_location=None,
)

# Reference line drawn as a line glyph so it can carry a legend label
p.line(
    [x_min, x_max],
    [x_min, x_max],
    line_color=INK_SOFT,
    line_width=4,
    line_dash="dashed",
    legend_label="Normal reference",
)

# Q-Q scatter points
p.scatter(
    x="theoretical",
    y="sample",
    source=source,
    size=20,
    color=BRAND,
    alpha=0.75,
    line_color=PAGE_BG,
    line_width=1,
    legend_label="Sample quantiles",
)

# Hover tooltips
hover = HoverTool(
    tooltips=[("Theoretical Q", "@theoretical{0.00}"), ("Sample Q", "@sample{0.00}"), ("Height", "@value{0.0} cm")]
)
p.add_tools(hover)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.title.text_font_size = "36pt"

p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

if p.legend:
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.border_line_color = INK_SOFT
    p.legend.label_text_color = INK_SOFT
    p.legend.label_text_font_size = "20pt"
    p.legend.location = "top_left"

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)

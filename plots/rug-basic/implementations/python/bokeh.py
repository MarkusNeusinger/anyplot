"""anyplot.ai
rug-basic: Basic Rug Plot
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-04-30
"""

import os
import sys


# Prevent this file from shadowing the installed bokeh package
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _this_dir]

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Range1d
from bokeh.plotting import figure
from scipy import stats


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - bimodal API response times (ms) showing clustering patterns
np.random.seed(42)
cluster1 = np.random.normal(85, 12, 60)  # Fast responses
cluster2 = np.random.normal(180, 20, 40)  # Slower responses
values = np.concatenate([cluster1, cluster2])

# KDE curve
kde = stats.gaussian_kde(values, bw_method=0.3)
x_smooth = np.linspace(values.min() - 20, values.max() + 20, 500)
kde_y = kde(x_smooth)

# Rug ticks sit just below y=0
rug_top = 0.0
rug_bottom = -kde_y.max() * 0.05

# Sources
kde_source = ColumnDataSource(data={"x": x_smooth, "y": kde_y})
rug_source = ColumnDataSource(
    data={"x": values, "y0": np.full(len(values), rug_bottom), "y1": np.full(len(values), rug_top)}
)

# Figure
p = figure(
    width=4800,
    height=2700,
    title="rug-basic · bokeh · anyplot.ai",
    x_axis_label="Response Time (ms)",
    y_axis_label="Density",
    toolbar_location=None,
)

# KDE density curve
p.line("x", "y", source=kde_source, line_color=BRAND, line_width=5)

# Rug ticks
p.segment(x0="x", y0="y0", x1="x", y1="y1", source=rug_source, line_color=BRAND, line_width=4, line_alpha=0.5)

# Axis ranges
p.x_range = Range1d(values.min() - 20, values.max() + 20)
p.y_range = Range1d(rug_bottom * 2.0, kde_y.max() * 1.15)

# Chrome — theme-adaptive
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.title.text_font_size = "28pt"

p.xaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_font_size = "22pt"

p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_font_size = "18pt"

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)

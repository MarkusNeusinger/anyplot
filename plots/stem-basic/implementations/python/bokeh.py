""" anyplot.ai
stem-basic: Basic Stem Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-04-30
"""

import os
import sys


sys.path = [p for p in sys.path if not p.endswith("/python")]

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Discrete signal samples (damped oscillation)
np.random.seed(42)
n_points = 30
x = np.arange(n_points)
y = np.exp(-0.1 * x) * np.sin(0.5 * x) * 2 + np.random.randn(n_points) * 0.1

baseline = 0

# Create data sources
source = ColumnDataSource(data={"x": x, "y": y})
stem_source = ColumnDataSource(data={"x0": x, "y0": np.full_like(x, baseline, dtype=float), "x1": x, "y1": y})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="stem-basic · bokeh · anyplot.ai",
    x_axis_label="Sample Index",
    y_axis_label="Amplitude",
)

# Draw stems (vertical lines from baseline to data points)
p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=stem_source, line_width=4, color=BRAND, alpha=0.85)

# Draw markers at data points
p.scatter(x="x", y="y", source=source, size=25, color=BRAND, alpha=1.0)

# Draw baseline
p.line(x=[x.min() - 0.5, x.max() + 0.5], y=[baseline, baseline], line_width=3, color=INK_SOFT, alpha=0.6)

# Sizing
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Save outputs
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)

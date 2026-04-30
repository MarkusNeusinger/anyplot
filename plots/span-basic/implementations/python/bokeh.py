""" anyplot.ai
span-basic: Basic Span Plot (Highlighted Region)
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-04-30
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import BoxAnnotation, ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1 — always first series

# Data - Monthly revenue over 2 years with spans highlighting key periods
np.random.seed(42)
months = np.arange(1, 25)
base_revenue = 100 + np.linspace(0, 50, 24) + 15 * np.sin(np.linspace(0, 4 * np.pi, 24))
noise = np.random.randn(24) * 8
revenue = base_revenue + noise

# Create ColumnDataSource
source = ColumnDataSource(data={"x": months, "y": revenue})

# Create figure (4800 × 2700 px)
p = figure(
    width=4800,
    height=2700,
    title="span-basic · bokeh · anyplot.ai",
    x_axis_label="Month",
    y_axis_label="Revenue (thousands $)",
)

# Add vertical span - highlight Q4 of Year 1 (months 10-12)
vertical_span = BoxAnnotation(
    left=10, right=12, fill_alpha=0.25, fill_color="#0072B2", line_color="#0072B2", line_width=2, line_alpha=0.5
)
p.add_layout(vertical_span)

# Add horizontal span - highlight target revenue range (120-140)
horizontal_span = BoxAnnotation(
    bottom=120, top=140, fill_alpha=0.2, fill_color="#E69F00", line_color="#E69F00", line_width=2, line_alpha=0.5
)
p.add_layout(horizontal_span)

# Plot line with markers (Okabe-Ito position 1)
p.line(x="x", y="y", source=source, line_width=4, line_color=BRAND, legend_label="Monthly Revenue")
p.scatter(x="x", y="y", source=source, size=20, fill_color=BRAND, line_color=PAGE_BG, line_width=2)

# HoverTool — showcases Bokeh's interactive HTML output
hover = HoverTool(tooltips=[("Month", "@x"), ("Revenue", "@y{0.1} K$")])
p.add_tools(hover)

# Add labels for spans — positioned prominently at top of each span
vertical_label = Label(
    x=10.2, y=143, text="Q4 Peak Season", text_font_size="28pt", text_color="#0072B2", text_font_style="bold"
)
p.add_layout(vertical_label)

horizontal_label = Label(
    x=17,
    y=124,
    text="Target Range",
    text_font_size="28pt",
    text_color="#B8720B" if THEME == "light" else "#E69F00",
    text_font_style="bold",
)
p.add_layout(horizontal_label)

# Apply theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None  # remove box border; L-shaped spines via xaxis/yaxis lines only

p.title.text_color = INK
p.title.text_font_size = "48pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "36pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "28pt"
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = None  # y-only grid preferred for line charts
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Legend — top-left for better visual balance
p.legend.label_text_font_size = "28pt"
p.legend.location = "top_left"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)

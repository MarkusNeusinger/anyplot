""" pyplots.ai
subplot-mosaic: Mosaic Subplot Layout with Varying Sizes
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-31
"""

import numpy as np
from bokeh.io import export_png
from bokeh.layouts import Spacer, column, row
from bokeh.models import ColumnDataSource, Legend, LegendItem
from bokeh.plotting import figure
from bokeh.themes import Theme


np.random.seed(42)

# Color palette (Python Blue and Yellow)
PYTHON_BLUE = "#306998"
PYTHON_YELLOW = "#FFD43B"
ACCENT_GREEN = "#4CAF50"

# Define a theme for consistent grid styling
theme = Theme(json={"attrs": {"Grid": {"grid_line_alpha": 0.3, "grid_line_dash": "dashed"}}})


# Helper to apply theme styling to a figure
def apply_theme(fig):
    fig.grid.grid_line_alpha = 0.3
    fig.grid.grid_line_dash = "dashed"


# Data for various subplots - Dashboard with business metrics

# A: Large overview time series (top left, spans 2 rows)
days = np.arange(1, 91)
revenue = 50000 + np.cumsum(np.random.randn(90) * 2000) + days * 300
source_a = ColumnDataSource(data={"day": days, "revenue": revenue})

# B: Scatter plot (top right) - two product lines
products_a = np.random.rand(25) * 100
profit_margin_a = products_a * 0.35 + np.random.randn(25) * 4 + 12
products_b = np.random.rand(25) * 100
profit_margin_b = products_b * 0.25 + np.random.randn(25) * 5 + 8
source_b1 = ColumnDataSource(data={"products": products_a, "profit_margin": profit_margin_a})
source_b2 = ColumnDataSource(data={"products": products_b, "profit_margin": profit_margin_b})

# C: Bar chart - Categories (middle left)
categories = ["Electronics", "Clothing", "Food", "Books"]
sales = [45000, 32000, 28000, 18000]
source_c = ColumnDataSource(data={"category": categories, "sales": sales})

# D: Line chart - Monthly trend (bottom, spans full width) - two years
months = np.arange(1, 13)
orders_2023 = [1200, 1400, 1100, 1600, 1800, 2100, 1900, 2200, 2400, 2100, 2300, 2800]
orders_2024 = [1400, 1600, 1350, 1850, 2100, 2400, 2200, 2500, 2700, 2350, 2600, 3100]
source_d1 = ColumnDataSource(data={"month": months, "orders": orders_2023})
source_d2 = ColumnDataSource(data={"month": months, "orders": orders_2024})

# E: Small metric - Conversion rate trend (two channels)
weeks = np.arange(1, 13)
conversion_web = 3.2 + np.cumsum(np.random.randn(12) * 0.15)
conversion_mobile = 2.8 + np.cumsum(np.random.randn(12) * 0.18)
source_e1 = ColumnDataSource(data={"week": weeks, "conversion": conversion_web})
source_e2 = ColumnDataSource(data={"week": weeks, "conversion": conversion_mobile})

# F: Customer satisfaction
quarters = ["Q1", "Q2", "Q3", "Q4"]
satisfaction = [78, 82, 85, 88]
source_f = ColumnDataSource(data={"quarter": quarters, "satisfaction": satisfaction})

# A: Large Revenue Overview (spans 2 columns, taller)
p_a = figure(
    width=3200,
    height=1100,
    title="Quarterly Revenue Overview",
    x_axis_label="Day",
    y_axis_label="Revenue ($)",
    toolbar_location=None,
)
line_a = p_a.line("day", "revenue", source=source_a, line_width=4, color=PYTHON_BLUE)
scatter_a = p_a.scatter("day", "revenue", source=source_a, size=8, color=PYTHON_BLUE, alpha=0.6)
legend_a = Legend(items=[LegendItem(label="Daily Revenue", renderers=[line_a, scatter_a])], location="top_left")
p_a.add_layout(legend_a)
p_a.legend.label_text_font_size = "16pt"
p_a.legend.background_fill_alpha = 0.7
p_a.title.text_font_size = "28pt"
p_a.xaxis.axis_label_text_font_size = "20pt"
p_a.yaxis.axis_label_text_font_size = "20pt"
p_a.xaxis.major_label_text_font_size = "16pt"
p_a.yaxis.major_label_text_font_size = "16pt"
apply_theme(p_a)

# B: Product Profitability Scatter with two product lines
p_b = figure(
    width=1600,
    height=1100,
    title="Product Profitability",
    x_axis_label="Units Sold",
    y_axis_label="Profit Margin (%)",
    toolbar_location=None,
)
scatter_b1 = p_b.scatter(
    "products", "profit_margin", source=source_b1, size=18, color=PYTHON_BLUE, alpha=0.7, legend_label="Premium Line"
)
scatter_b2 = p_b.scatter(
    "products",
    "profit_margin",
    source=source_b2,
    size=18,
    color=PYTHON_YELLOW,
    alpha=0.7,
    line_color=PYTHON_BLUE,
    line_width=2,
    legend_label="Standard Line",
)
p_b.legend.location = "top_left"
p_b.legend.label_text_font_size = "14pt"
p_b.legend.background_fill_alpha = 0.7
p_b.title.text_font_size = "24pt"
p_b.xaxis.axis_label_text_font_size = "18pt"
p_b.yaxis.axis_label_text_font_size = "18pt"
p_b.xaxis.major_label_text_font_size = "14pt"
p_b.yaxis.major_label_text_font_size = "14pt"
apply_theme(p_b)

# C: Category Sales Bar Chart
p_c = figure(
    width=2400,
    height=900,
    x_range=categories,
    title="Sales by Category",
    x_axis_label="Category",
    y_axis_label="Sales ($)",
    toolbar_location=None,
)
bars_c = p_c.vbar(
    x="category",
    top="sales",
    source=source_c,
    width=0.7,
    color=PYTHON_BLUE,
    alpha=0.85,
    line_color="white",
    line_width=2,
    legend_label="Q4 2024 Sales",
)
p_c.legend.location = "top_right"
p_c.legend.label_text_font_size = "14pt"
p_c.legend.background_fill_alpha = 0.7
p_c.title.text_font_size = "24pt"
p_c.xaxis.axis_label_text_font_size = "18pt"
p_c.yaxis.axis_label_text_font_size = "18pt"
p_c.xaxis.major_label_text_font_size = "14pt"
p_c.yaxis.major_label_text_font_size = "14pt"
p_c.xaxis.major_label_orientation = 0.3
apply_theme(p_c)

# Empty cell spacer to demonstrate gap functionality (like "." in mosaic pattern)
# This represents an intentional gap in the mosaic layout
empty_spacer = Spacer(width=2400, height=450, background="#F5F5F5")

# F: Customer Satisfaction Bar
p_f = figure(
    width=2400,
    height=450,
    x_range=quarters,
    title="Customer Satisfaction",
    x_axis_label="Quarter",
    y_axis_label="Score",
    toolbar_location=None,
)
p_f.vbar(
    x="quarter",
    top="satisfaction",
    source=source_f,
    width=0.6,
    color=PYTHON_YELLOW,
    alpha=0.9,
    line_color=PYTHON_BLUE,
    line_width=2,
    legend_label="Satisfaction Score",
)
p_f.legend.location = "top_left"
p_f.legend.label_text_font_size = "12pt"
p_f.legend.background_fill_alpha = 0.7
p_f.title.text_font_size = "22pt"
p_f.xaxis.axis_label_text_font_size = "16pt"
p_f.yaxis.axis_label_text_font_size = "16pt"
p_f.xaxis.major_label_text_font_size = "14pt"
p_f.yaxis.major_label_text_font_size = "14pt"
apply_theme(p_f)

# D: Monthly Orders Trend with main title (full width bottom) - comparing two years
p_d = figure(
    width=4800,
    height=700,
    title="subplot-mosaic · bokeh · pyplots.ai",
    x_axis_label="Month",
    y_axis_label="Orders",
    toolbar_location=None,
)
line_d1 = p_d.line("month", "orders", source=source_d1, line_width=5, color=PYTHON_BLUE, legend_label="2023")
scatter_d1 = p_d.scatter("month", "orders", source=source_d1, size=18, color=PYTHON_BLUE)
line_d2 = p_d.line("month", "orders", source=source_d2, line_width=5, color=ACCENT_GREEN, legend_label="2024")
scatter_d2 = p_d.scatter("month", "orders", source=source_d2, size=18, color=ACCENT_GREEN)
p_d.legend.location = "top_left"
p_d.legend.label_text_font_size = "18pt"
p_d.legend.background_fill_alpha = 0.7
p_d.legend.orientation = "horizontal"
p_d.title.text_font_size = "32pt"
p_d.xaxis.axis_label_text_font_size = "22pt"
p_d.yaxis.axis_label_text_font_size = "22pt"
p_d.xaxis.major_label_text_font_size = "18pt"
p_d.yaxis.major_label_text_font_size = "18pt"
apply_theme(p_d)

# Create mosaic layout: AAB / C.F / DDD pattern
# Row 1: A (large, spans 2 cols) + B on right
# Row 2: C left, empty spacer (gap), F on right
# Row 3: D spans full width
# The "." in the pattern is represented by empty_spacer

# Row 1: Large A + B
row1 = row(p_a, p_b)

# Row 2: C + empty cell (gap) + F - demonstrates empty cell with "."
row2 = row(p_c, column(empty_spacer, p_f))

# Full layout
layout = column(row1, row2, p_d)

export_png(layout, filename="plot.png")

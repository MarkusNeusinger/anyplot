""" pyplots.ai
line-yield-curve: Yield Curve (Interest Rate Term Structure)
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-14
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, Label, Legend, LegendItem, NumeralTickFormatter
from bokeh.plotting import figure


# Data - U.S. Treasury yield curves on three dates
maturity_labels = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
maturity_years = np.array([1 / 12, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30])

# Normal upward-sloping curve (Jan 2024)
yields_normal = np.array([5.53, 5.46, 5.36, 4.95, 4.42, 4.15, 3.98, 4.03, 4.10, 4.38, 4.27])

# Flat curve (Jun 2024)
yields_flat = np.array([5.47, 5.49, 5.40, 5.12, 4.75, 4.55, 4.32, 4.30, 4.28, 4.52, 4.40])

# Inverted curve (Jul 2023)
yields_inverted = np.array([5.47, 5.52, 5.56, 5.40, 4.87, 4.56, 4.18, 4.09, 3.96, 4.22, 4.03])

# Create ColumnDataSources
source_normal = ColumnDataSource(data={"maturity": maturity_years, "yield_pct": yields_normal})
source_flat = ColumnDataSource(data={"maturity": maturity_years, "yield_pct": yields_flat})
source_inverted = ColumnDataSource(data={"maturity": maturity_years, "yield_pct": yields_inverted})

# Inversion zone: where inverted curve short-term yields exceed its own 30Y yield
inv_30y = yields_inverted[-1]  # 4.03%

# Create figure with log x-axis for better spacing of short-term maturities
p = figure(
    width=4800,
    height=2700,
    title="line-yield-curve · bokeh · pyplots.ai",
    x_axis_label="Maturity",
    y_axis_label="Yield (%)",
    x_axis_type="log",
    x_range=(0.06, 42),
    y_range=(3.75, 5.8),
)

# Inversion shading - only the short-term maturities (1M to 7Y) where yields > 30Y
inv_mask = yields_inverted > inv_30y
inv_idx = np.where(inv_mask)[0]
inv_x = maturity_years[inv_idx]
inv_upper = yields_inverted[inv_idx]
source_inv_shade = ColumnDataSource(data={"x": inv_x, "y1": np.full_like(inv_x, inv_30y), "y2": inv_upper})
p.varea(x="x", y1="y1", y2="y2", source=source_inv_shade, fill_color="#7B2D8E", fill_alpha=0.08)

# Colorblind-safe palette: Python Blue, teal, purple
color_normal = "#306998"
color_flat = "#2A9D8F"
color_inverted = "#7B2D8E"

# Normal curve - solid, primary emphasis
line_normal = p.line(x="maturity", y="yield_pct", source=source_normal, line_width=4.5, line_color=color_normal)
scatter_normal = p.scatter(
    x="maturity",
    y="yield_pct",
    source=source_normal,
    size=16,
    fill_color=color_normal,
    line_color="white",
    line_width=2.5,
)

# Flat curve - solid, secondary
line_flat = p.line(x="maturity", y="yield_pct", source=source_flat, line_width=4.5, line_color=color_flat)
scatter_flat = p.scatter(
    x="maturity", y="yield_pct", source=source_flat, size=16, fill_color=color_flat, line_color="white", line_width=2.5
)

# Inverted curve - dashed to emphasize anomaly
line_inverted = p.line(
    x="maturity", y="yield_pct", source=source_inverted, line_width=4.5, line_color=color_inverted, line_dash=[12, 6]
)
scatter_inverted = p.scatter(
    x="maturity",
    y="yield_pct",
    source=source_inverted,
    size=16,
    fill_color=color_inverted,
    line_color="white",
    line_width=2.5,
)

# Inversion annotation - positioned in clear space above the shading
inversion_label = Label(
    x=0.55,
    y=3.85,
    text="Inversion zone: short-term yields exceed long-term",
    text_font_size="20pt",
    text_color=color_inverted,
    text_font_style="italic",
    text_alpha=0.85,
)
p.add_layout(inversion_label)

# Subtitle annotation
subtitle = Label(
    x=0.07,
    y=5.70,
    text="U.S. Treasury Yield Curves — normal, flat, and inverted term structures",
    text_font_size="19pt",
    text_color="#777777",
)
p.add_layout(subtitle)

# Legend - positioned in lower right with proper sizing
legend = Legend(
    items=[
        LegendItem(label="Jan 2024 — Normal", renderers=[line_normal, scatter_normal]),
        LegendItem(label="Jun 2024 — Flat", renderers=[line_flat, scatter_flat]),
        LegendItem(label="Jul 2023 — Inverted", renderers=[line_inverted, scatter_inverted]),
    ],
    location="bottom_right",
)
legend.label_text_font_size = "22pt"
legend.glyph_width = 55
legend.glyph_height = 32
legend.spacing = 14
legend.padding = 24
legend.margin = 30
legend.background_fill_color = "white"
legend.background_fill_alpha = 0.9
legend.border_line_color = "#dddddd"
legend.border_line_width = 1
legend.border_line_alpha = 0.6
p.add_layout(legend)

# Custom x-axis tick labels - log scale provides natural spacing
p.xaxis.ticker = list(maturity_years)
p.xaxis.major_label_overrides = {maturity_years[i]: maturity_labels[i] for i in range(len(maturity_labels))}

# Title styling
p.title.text_font_size = "36pt"
p.title.text_color = "#333333"
p.title.text_font_style = "bold"

# Axis label and tick styling
p.xaxis.axis_label_text_font_size = "26pt"
p.yaxis.axis_label_text_font_size = "26pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

# Grid styling - subtle y-axis only, solid thin lines
p.xgrid.grid_line_alpha = 0
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_color = "#999999"
p.ygrid.grid_line_width = 1

# Background
p.background_fill_color = "#FFFFFF"
p.border_fill_color = "white"
p.outline_line_color = None

# Axis styling - clean, minimal
p.xaxis.axis_line_width = 2
p.xaxis.axis_line_color = "#444444"
p.yaxis.axis_line_width = 2
p.yaxis.axis_line_color = "#444444"
p.xaxis.major_tick_line_width = 0
p.yaxis.major_tick_line_width = 0
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Remove toolbar
p.toolbar_location = None

# Format y-axis
p.yaxis.formatter = NumeralTickFormatter(format="0.0")

# Save
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)

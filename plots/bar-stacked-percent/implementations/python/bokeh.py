""" pyplots.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 98/100 | Created: 2025-12-25
"""

import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data: Market share of smartphone brands over quarters
categories = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025"]
components = ["Apple", "Samsung", "Xiaomi", "Others"]

raw_data = {
    "Apple": [28, 25, 22, 31, 27],
    "Samsung": [23, 24, 26, 22, 24],
    "Xiaomi": [14, 16, 18, 15, 17],
    "Others": [35, 35, 34, 32, 32],
}

# Calculate percentages (already sum to 100, but normalize for safety)
df = pd.DataFrame(raw_data, index=categories)
totals = df.sum(axis=1)
df_percent = df.div(totals, axis=0) * 100

# Calculate bottom positions for stacking
bottoms = {}
cumulative = [0.0] * len(categories)
for comp in components:
    bottoms[comp] = cumulative.copy()
    cumulative = [c + v for c, v in zip(cumulative, df_percent[comp], strict=True)]

# Colors - Python Blue first, then harmonious palette
colors = ["#306998", "#FFD43B", "#4ECDC4", "#95A5A6"]

# Create figure with categorical x-axis
p = figure(
    x_range=categories,
    width=4800,
    height=2700,
    title="bar-stacked-percent · bokeh · pyplots.ai",
    y_range=(0, 100),
    toolbar_location=None,
)

# Draw stacked bars
renderers = []
for i, comp in enumerate(components):
    source = ColumnDataSource(
        data={
            "x": categories,
            "top": [b + v for b, v in zip(bottoms[comp], df_percent[comp], strict=True)],
            "bottom": bottoms[comp],
            "value": df_percent[comp].tolist(),
        }
    )
    r = p.vbar(
        x="x",
        top="top",
        bottom="bottom",
        source=source,
        width=0.7,
        color=colors[i],
        legend_label=comp,
        line_color="white",
        line_width=2,
    )
    renderers.append(r)

# Add percentage labels inside each segment
for i, comp in enumerate(components):
    values = df_percent[comp].tolist()
    mids = [(b + b + v) / 2 for b, v in zip(bottoms[comp], values, strict=True)]

    # Only show labels for segments >= 10%
    labels = [f"{v:.0f}%" if v >= 10 else "" for v in values]

    label_source = ColumnDataSource(data={"x": categories, "y": mids, "text": labels})

    # Use dark text on light colors (Samsung yellow, Xiaomi cyan), white on dark (Apple blue, Others gray)
    text_color = "#333333" if i in [1, 2] else "white"

    label_set = LabelSet(
        x="x",
        y="y",
        text="text",
        source=label_source,
        text_align="center",
        text_baseline="middle",
        text_font_size="24pt",
        text_color=text_color,
        text_font_style="bold",
    )
    p.add_layout(label_set)

# Styling for large canvas
p.title.text_font_size = "36pt"
p.title.text_font_style = "bold"
p.xaxis.axis_label = "Quarter"
p.yaxis.axis_label = "Market Share (%)"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.3
p.ygrid.grid_line_dash = "dashed"

# Legend styling
p.legend.location = "top_right"
p.legend.label_text_font_size = "22pt"
p.legend.glyph_width = 50
p.legend.glyph_height = 50
p.legend.spacing = 15
p.legend.padding = 20
p.legend.background_fill_alpha = 0.8

# Remove outline
p.outline_line_color = None

# Save PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="bar-stacked-percent · bokeh · pyplots.ai")

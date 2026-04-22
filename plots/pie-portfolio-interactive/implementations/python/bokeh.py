""" pyplots.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, CustomJS, HoverTool, LabelSet, Legend, LegendItem, TapTool
from bokeh.plotting import figure, output_file


# Data - Portfolio allocation with categories
np.random.seed(42)

# Main portfolio data with asset classes
data = {
    "asset": [
        "Apple Inc.",
        "Microsoft",
        "Google",
        "US Treasury 10Y",
        "Corporate Bonds",
        "Gold ETF",
        "Real Estate Fund",
        "Int'l Equities",
        "Cash",
        "Commodities",
    ],
    "weight": [18, 15, 12, 15, 10, 5, 8, 10, 4, 3],
    "category": [
        "Equities",
        "Equities",
        "Equities",
        "Fixed Income",
        "Fixed Income",
        "Alternatives",
        "Alternatives",
        "Equities",
        "Cash",
        "Alternatives",
    ],
    "value": [180000, 150000, 120000, 150000, 100000, 50000, 80000, 100000, 40000, 30000],
}

df = pd.DataFrame(data)

# Calculate angles for pie chart
df["angle"] = df["weight"] / df["weight"].sum() * 2 * np.pi

# Calculate cumulative angles for positioning (start from top: -pi/2 offset)
df["end_angle"] = df["angle"].cumsum() - np.pi / 2
df["start_angle"] = df["end_angle"] - df["angle"]

# Mid-angle for label positioning
df["mid_angle"] = (df["start_angle"] + df["end_angle"]) / 2

# Color mapping by category
category_colors = {
    "Equities": "#306998",  # Python Blue
    "Fixed Income": "#FFD43B",  # Python Yellow
    "Alternatives": "#48A9A6",  # Teal
    "Cash": "#8B8B8B",  # Gray
}
df["color"] = df["category"].map(category_colors)

# Calculate positions for labels (outer ring)
outer_radius = 0.72
label_radius = 0.88
df["label_x"] = label_radius * np.cos(df["mid_angle"])
df["label_y"] = label_radius * np.sin(df["mid_angle"])

# Format weight for display
df["weight_str"] = df["weight"].apply(lambda x: f"{x}%")

# Create source
source = ColumnDataSource(df)

# Set output file for HTML
output_file("plot.html", title="Interactive Portfolio Allocation Chart")

# Create figure - using square aspect for pie chart
p = figure(
    width=3600,
    height=3600,
    title="pie-portfolio-interactive · bokeh · pyplots.ai",
    x_range=(-1.25, 1.25),
    y_range=(-1.25, 1.25),
    tools="hover,tap,reset,save",
    toolbar_location="above",
)

# Remove grid and axes for clean pie look
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None

# Draw donut wedges
wedges = p.annular_wedge(
    x=0,
    y=0,
    inner_radius=0.38,
    outer_radius=outer_radius,
    start_angle="start_angle",
    end_angle="end_angle",
    color="color",
    alpha=0.9,
    source=source,
    line_color="white",
    line_width=4,
    hover_fill_alpha=1.0,
    hover_line_color="#222222",
    hover_line_width=6,
)

# Add labels for assets
labels = LabelSet(
    x="label_x",
    y="label_y",
    text="asset",
    source=source,
    text_font_size="18pt",
    text_align="center",
    text_baseline="middle",
    text_color="#333333",
)
p.add_layout(labels)

# Configure hover tool
hover = p.select(type=HoverTool)
hover.tooltips = [
    ("Asset", "@asset"),
    ("Category", "@category"),
    ("Weight", "@weight{0.0}%"),
    ("Value", "$@value{0,0}"),
]
hover.mode = "mouse"

# Create legend manually with category colors using scatter (not circle)
legend_items = []
for category, color in category_colors.items():
    # Create a dummy glyph for legend using scatter
    dummy_source = ColumnDataSource(data={"x": [999], "y": [999]})
    r = p.scatter(x="x", y="y", size=20, color=color, source=dummy_source, marker="square")
    legend_items.append(LegendItem(label=category, renderers=[r]))

legend = Legend(items=legend_items, location="center")
legend.label_text_font_size = "22pt"
legend.glyph_width = 35
legend.glyph_height = 35
legend.spacing = 15
legend.padding = 25
legend.background_fill_alpha = 0.85
legend.border_line_color = "#cccccc"
legend.border_line_width = 2
p.add_layout(legend, "right")

# Style title
p.title.text_font_size = "36pt"
p.title.align = "center"

# Add center text showing total portfolio value
total_value = df["value"].sum()
center_source = ColumnDataSource(data={"x": [0], "y": [0.02], "text": [f"Total\n${total_value:,.0f}"]})
center_label = LabelSet(
    x="x",
    y="y",
    text="text",
    source=center_source,
    text_font_size="26pt",
    text_align="center",
    text_baseline="middle",
    text_color="#333333",
    text_font_style="bold",
)
p.add_layout(center_label)

# Add JavaScript callback for drill-down interactivity
callback = CustomJS(
    args={"source": source},
    code="""
    const indices = source.selected.indices;
    if (indices.length > 0) {
        const idx = indices[0];
        const asset = source.data['asset'][idx];
        const weight = source.data['weight'][idx];
        const category = source.data['category'][idx];
        const value = source.data['value'][idx];
        console.log('Selected: ' + asset + ' (' + category + ')');
        console.log('Weight: ' + weight + '%, Value: $' + value.toLocaleString());
    }
""",
)

tap_tool = p.select(type=TapTool)
source.selected.js_on_change("indices", callback)

# Save outputs
export_png(p, filename="plot.png")
save(p)

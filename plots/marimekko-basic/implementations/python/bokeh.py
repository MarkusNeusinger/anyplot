""" anyplot.ai
marimekko-basic: Basic Marimekko Chart
Library: bokeh 3.9.0 | Python 3.14.4
Quality: 88/100 | Updated: 2026-04-27
"""

import os

from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (positions 1-4)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]

# Data: Market share across regions with varying market sizes
regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
products = ["Electronics", "Apparel", "Home & Garden", "Food & Beverage"]

market_data = {
    "North America": {"Electronics": 120, "Apparel": 80, "Home & Garden": 60, "Food & Beverage": 140},
    "Europe": {"Electronics": 90, "Apparel": 110, "Home & Garden": 50, "Food & Beverage": 100},
    "Asia Pacific": {"Electronics": 200, "Apparel": 150, "Home & Garden": 80, "Food & Beverage": 170},
    "Latin America": {"Electronics": 40, "Apparel": 35, "Home & Garden": 25, "Food & Beverage": 50},
}

# Calculate totals for each region (determines bar width)
region_totals = {region: sum(market_data[region].values()) for region in regions}
total_all = sum(region_totals.values())

# Calculate normalized widths (proportional to region total)
bar_gap = 0.02
total_width = 1.0 - (len(regions) - 1) * bar_gap
widths = {region: (region_totals[region] / total_all) * total_width for region in regions}

# Build rectangle data for each segment
rect_x, rect_y, rect_widths, rect_heights = [], [], [], []
rect_colors, rect_products, rect_regions, rect_values, rect_percentages = [], [], [], [], []

current_x = 0
for region in regions:
    bar_width = widths[region]
    bar_center_x = current_x + bar_width / 2
    current_y = 0
    region_total = region_totals[region]

    for i, product in enumerate(products):
        value = market_data[region][product]
        height = value / region_total

        rect_x.append(bar_center_x)
        rect_y.append(current_y + height / 2)
        rect_widths.append(bar_width * 0.98)
        rect_heights.append(height)
        rect_colors.append(OKABE_ITO[i])
        rect_products.append(product)
        rect_regions.append(region)
        rect_values.append(value)
        rect_percentages.append(f"{height * 100:.1f}%")

        current_y += height

    current_x += bar_width + bar_gap

source = ColumnDataSource(
    data={
        "x": rect_x,
        "y": rect_y,
        "width": rect_widths,
        "height": rect_heights,
        "color": rect_colors,
        "product": rect_products,
        "region": rect_regions,
        "value": rect_values,
        "percentage": rect_percentages,
    }
)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="marimekko-basic · bokeh · anyplot.ai",
    x_range=(-0.02, 1.02),
    y_range=(-0.18, 1.05),
    tools="",
    toolbar_location=None,
)

p.rect(x="x", y="y", width="width", height="height", color="color", source=source, line_color=PAGE_BG, line_width=3)

hover = HoverTool(
    tooltips=[("Region", "@region"), ("Product", "@product"), ("Value", "$@value B"), ("Share", "@percentage")]
)
p.add_tools(hover)

# Value labels on larger segments
label_x, label_y, label_text = [], [], []
for i in range(len(rect_x)):
    if rect_heights[i] > 0.12 and rect_widths[i] > 0.08:
        label_x.append(rect_x[i])
        label_y.append(rect_y[i])
        label_text.append(f"${rect_values[i]}B")

label_source = ColumnDataSource(data={"x": label_x, "y": label_y, "text": label_text})
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=label_source,
        text_align="center",
        text_baseline="middle",
        text_color="white",
        text_font_size="22pt",
        text_font_style="bold",
    )
)

# Region labels at bottom
region_label_x, region_label_text = [], []
current_x = 0
for region in regions:
    bar_width = widths[region]
    region_label_x.append(current_x + bar_width / 2)
    region_label_text.append(f"{region}\n(${region_totals[region]}B)")
    current_x += bar_width + bar_gap

region_source = ColumnDataSource(data={"x": region_label_x, "y": [-0.04] * len(regions), "text": region_label_text})
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=region_source,
        text_align="center",
        text_baseline="top",
        text_color=INK,
        text_font_size="24pt",
    )
)

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "32pt"
p.title.align = "center"
p.title.text_color = INK

p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Manual legend
legend_y_start = 0.92
legend_x = 0.83
legend_spacing = 0.07
box_size = 0.035

for i, product in enumerate(products):
    legend_y_pos = legend_y_start - i * legend_spacing
    p.quad(
        left=legend_x - box_size / 2,
        right=legend_x + box_size / 2,
        top=legend_y_pos + box_size / 2,
        bottom=legend_y_pos - box_size / 2,
        color=OKABE_ITO[i],
        line_color=PAGE_BG,
        line_width=2,
    )
    p.text(
        x=[legend_x + 0.03],
        y=[legend_y_pos],
        text=[product],
        text_font_size="22pt",
        text_baseline="middle",
        text_color=INK_SOFT,
    )

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)

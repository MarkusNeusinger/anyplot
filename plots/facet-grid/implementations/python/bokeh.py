""" pyplots.ai
facet-grid: Faceted Grid Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-30
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png
from bokeh.layouts import column, gridplot
from bokeh.models import ColumnDataSource, Div
from bokeh.plotting import figure


# Data - Product performance across regions and seasons
np.random.seed(42)

regions = ["North", "South", "East"]
seasons = ["Spring", "Summer", "Fall", "Winter"]

data = []
for region in regions:
    for season in seasons:
        n_points = 25
        # Base values vary by region
        base_x = {"North": 20, "South": 30, "East": 25}[region]
        base_y = {"North": 50, "South": 70, "East": 60}[region]

        # Seasonal adjustments
        season_adj = {"Spring": 1.0, "Summer": 1.3, "Fall": 0.9, "Winter": 0.7}[season]

        x = np.random.normal(base_x, 5, n_points)
        y = base_y * season_adj + x * 0.8 + np.random.normal(0, 8, n_points)

        for xi, yi in zip(x, y, strict=True):
            data.append({"marketing_spend": xi, "sales": yi, "region": region, "season": season})

df = pd.DataFrame(data)

# Colors for each region - darker orange instead of yellow for better visibility
colors = {"North": "#306998", "South": "#E69F00", "East": "#4ECDC4"}

# Create grid of plots (rows=seasons, cols=regions)
# Target: 4800x2700 total. With 3 cols, 4 rows + title/legend:
# - Subplot width: 4800 / 3 = 1600
# - Subplot height: (2700 - 120 title - 100 legend) / 4 = 620
plots = []

for season in seasons:
    row_plots = []
    for region in regions:
        subset = df[(df["region"] == region) & (df["season"] == season)]
        source = ColumnDataSource(data={"x": subset["marketing_spend"], "y": subset["sales"]})

        # Create figure for each cell
        p = figure(width=1600, height=620, x_range=(5, 50), y_range=(20, 130), tools="")

        # Add scatter points
        p.scatter(
            x="x", y="y", source=source, size=18, color=colors[region], alpha=0.7, line_color="#333333", line_width=1
        )

        # Add facet label in top-left corner
        p.text(
            x=[8],
            y=[122],
            text=[f"{region} · {season}"],
            text_font_size="18pt",
            text_color="#333333",
            text_font_style="bold",
        )

        # Style axes
        p.xaxis.axis_label = "Marketing Spend ($K)" if season == seasons[-1] else ""
        p.yaxis.axis_label = "Sales ($K)" if region == regions[0] else ""
        p.xaxis.axis_label_text_font_size = "20pt"
        p.yaxis.axis_label_text_font_size = "20pt"
        p.xaxis.major_label_text_font_size = "16pt"
        p.yaxis.major_label_text_font_size = "16pt"

        # Grid styling
        p.xgrid.grid_line_alpha = 0.3
        p.ygrid.grid_line_alpha = 0.3
        p.xgrid.grid_line_dash = "dashed"
        p.ygrid.grid_line_dash = "dashed"

        # Background
        p.background_fill_color = "#fafafa"

        row_plots.append(p)
    plots.append(row_plots)

# Create gridplot layout
grid = gridplot(plots, toolbar_location=None, merge_tools=False)

# Add overall title using Div for cleaner implementation
title_div = Div(
    text="<h1 style='text-align: center; color: #333333; font-size: 32pt; margin: 20px 0;'>"
    "facet-grid · bokeh · pyplots.ai</h1>",
    width=4800,
    height=120,
)

# Create legend using Div for region-color mapping
legend_html = (
    "<div style='text-align: center; font-size: 18pt; padding: 20px 0;'>"
    "<span style='font-weight: bold; margin-right: 30px;'>Region:</span>"
)
for region, color in colors.items():
    legend_html += (
        f"<span style='margin-right: 40px;'>"
        f"<span style='display: inline-block; width: 20px; height: 20px; "
        f"background-color: {color}; border: 1px solid #333; border-radius: 50%; "
        f"vertical-align: middle; margin-right: 8px;'></span>"
        f"{region}</span>"
    )
legend_html += "</div>"

legend_div = Div(text=legend_html, width=4800, height=80)

# Combine title, grid, and legend using column layout
final_layout = column(title_div, grid, legend_div)

# Save
export_png(final_layout, filename="plot.png")

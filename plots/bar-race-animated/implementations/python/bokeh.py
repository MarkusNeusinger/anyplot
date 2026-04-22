""" pyplots.ai
bar-race-animated: Animated Bar Chart Race
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-11
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.layouts import column, gridplot
from bokeh.models import ColumnDataSource, Range1d, Title
from bokeh.plotting import figure


# Data: Simulated streaming platform subscriber counts (millions) over 8 years
np.random.seed(42)

platforms = ["StreamMax", "ViewHub", "FlixNet", "WatchNow", "CineCloud", "MediaFlow"]
years = list(range(2016, 2024))
colors = ["#306998", "#FFD43B", "#DC2626", "#059669", "#7C3AED", "#EA580C"]
platform_colors = dict(zip(platforms, colors, strict=True))

# Generate realistic growth patterns for each platform
data_rows = []
base_values = [50, 80, 120, 30, 20, 40]  # Starting subscribers in millions
growth_rates = [1.35, 1.15, 1.08, 1.45, 1.55, 1.25]  # Annual growth multipliers

for i, platform in enumerate(platforms):
    value = base_values[i]
    for year in years:
        noise = np.random.uniform(0.9, 1.1)
        value = value * growth_rates[i] * noise
        data_rows.append({"platform": platform, "year": year, "subscribers": round(value, 1)})

df = pd.DataFrame(data_rows)

# Select 4 key time snapshots for the small multiples grid
snapshot_years = [2016, 2018, 2021, 2023]

# Find global max for consistent x-axis across all plots
max_subscribers = df["subscribers"].max() * 1.15

# Build individual plots for each snapshot year
plots = []
for idx, year in enumerate(snapshot_years):
    year_data = df[df["year"] == year].copy()
    year_data = year_data.sort_values("subscribers", ascending=True)

    # Prepare data for horizontal bar chart
    y_positions = list(range(len(platforms)))
    bar_colors = [platform_colors[p] for p in year_data["platform"]]

    source = ColumnDataSource(
        data={
            "y": y_positions,
            "right": year_data["subscribers"].tolist(),
            "platform": year_data["platform"].tolist(),
            "color": bar_colors,
            "label": [f"{v:.0f}M" for v in year_data["subscribers"]],
        }
    )

    # Create figure - each subplot is 2400x1275 (half of full canvas minus title)
    p = figure(
        width=2400,
        height=1275,
        x_range=Range1d(0, max_subscribers),
        y_range=(-0.5, len(platforms) - 0.5),
        x_axis_label="Subscribers (millions)" if idx >= 2 else None,
        tools="",
        toolbar_location=None,
    )

    # Add year title
    p.add_layout(Title(text=str(year), text_font_size="36pt", text_font_style="bold"), "above")

    # Create horizontal bars
    p.hbar(y="y", right="right", height=0.65, source=source, color="color", alpha=0.9, line_color="white", line_width=2)

    # Add platform labels on bars
    for _i, row in year_data.iterrows():
        y_pos = year_data["platform"].tolist().index(row["platform"])
        p.text(
            x=[row["subscribers"] * 0.03],
            y=[y_pos],
            text=[row["platform"]],
            text_font_size="18pt",
            text_font_style="bold",
            text_color="white",
            text_baseline="middle",
        )
        # Add value labels at end of bars
        p.text(
            x=[row["subscribers"] + max_subscribers * 0.01],
            y=[y_pos],
            text=[f"{row['subscribers']:.0f}M"],
            text_font_size="16pt",
            text_font_style="bold",
            text_color="#333333",
            text_baseline="middle",
        )

    # Styling
    p.yaxis.visible = False
    p.xaxis.axis_label_text_font_size = "22pt"
    p.xaxis.major_label_text_font_size = "18pt"
    p.xgrid.grid_line_alpha = 0.3
    p.xgrid.grid_line_dash = [6, 4]
    p.ygrid.grid_line_color = None
    p.outline_line_color = None
    p.min_border_right = 50  # Add right margin to prevent tick overlap

    plots.append(p)

# Create 2x2 grid layout
grid = gridplot([[plots[0], plots[1]], [plots[2], plots[3]]], merge_tools=False)

# Add overall title using column layout
overall_title = figure(width=4800, height=150, tools="", toolbar_location=None, x_range=(0, 1), y_range=(0, 1))
overall_title.outline_line_color = None
overall_title.xaxis.visible = False
overall_title.yaxis.visible = False
overall_title.xgrid.grid_line_color = None
overall_title.ygrid.grid_line_color = None
overall_title.text(
    x=[0.5],
    y=[0.5],
    text=["bar-race-animated · bokeh · pyplots.ai"],
    text_font_size="32pt",
    text_font_style="bold",
    text_align="center",
    text_baseline="middle",
    text_color="#333333",
)

# Combine title and grid
layout = column(overall_title, grid)

# Save as PNG
export_png(layout, filename="plot.png")

# Save as HTML for interactive version
output_file("plot.html")
save(layout)

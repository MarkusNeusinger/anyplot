""" pyplots.ai
bubble-basic: Basic Bubble Chart
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 93/100 | Created: 2026-02-16
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import BoxAnnotation, ColumnDataSource, HoverTool, Label, LinearColorMapper, Range1d
from bokeh.palettes import Viridis256
from bokeh.plotting import figure, output_file, save
from bokeh.transform import transform


# Data — City metrics: population density vs median income, bubble = green space per capita
np.random.seed(42)
n_cities = 40

population_density = np.random.uniform(500, 12000, n_cities)  # people per km²
median_income = 30 + population_density / 400 + np.random.normal(0, 4, n_cities)  # thousands USD
green_space = np.random.uniform(5, 60, n_cities)  # m² per capita

# Scale bubble sizes by area for accurate perception (spec requirement)
size_min, size_max = 25, 110
green_normalized = (green_space - green_space.min()) / (green_space.max() - green_space.min())
bubble_size = size_min + (size_max - size_min) * green_normalized

# Color by green space — tells the story: denser cities tend to have less green space
color_mapper = LinearColorMapper(palette=Viridis256, low=green_space.min(), high=green_space.max())

source = ColumnDataSource(
    data={
        "density": population_density,
        "income": median_income,
        "size": bubble_size,
        "green_space": green_space,
        "density_display": np.round(population_density).astype(int),
        "income_display": np.round(median_income, 1),
        "green_display": np.round(green_space, 1),
    }
)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="bubble-basic · bokeh · pyplots.ai",
    x_axis_label="Population Density (people/km²)",
    y_axis_label="Median Income (thousands USD)",
    toolbar_location=None,
)

p.scatter(
    x="density",
    y="income",
    size="size",
    source=source,
    fill_color=transform("green_space", color_mapper),
    fill_alpha=0.7,
    line_color="white",
    line_width=2,
)

# Interactive hover tool — Bokeh-distinctive feature
hover = HoverTool(
    tooltips=[
        ("Density", "@density_display{,} people/km²"),
        ("Income", "$@income_display{0.0}k"),
        ("Green Space", "@green_display m²/capita"),
    ],
    mode="mouse",
)
p.add_tools(hover)

# Typography (scaled for 4800x2700 px canvas)
p.title.text_font_size = "30pt"
p.title.text_color = "#222222"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"

# Clean frame — remove spines, outline, and tick marks
p.outline_line_color = None
p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None

# Subtle grid
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15
p.xgrid.grid_line_color = "#aaaaaa"
p.ygrid.grid_line_color = "#aaaaaa"
p.xgrid.grid_line_dash = [4, 4]
p.ygrid.grid_line_dash = [4, 4]

# Ranges — fit data tightly
x_pad = (population_density.max() - population_density.min()) * 0.06
y_pad = (median_income.max() - median_income.min()) * 0.08
x_start = population_density.min() - x_pad * 2
x_end = population_density.max() + x_pad * 4  # room for legend on right side
y_start = median_income.min() - y_pad * 2
y_end = median_income.max() + y_pad * 1.5
p.x_range = Range1d(start=x_start, end=x_end)
p.y_range = Range1d(start=y_start, end=y_end)

# Size legend — placed in lower-right with semi-transparent background
legend_x = population_density.max() * 0.85
legend_y_top = y_start + (y_end - y_start) * 0.32

ref_green = [green_space.min(), (green_space.min() + green_space.max()) / 2, green_space.max()]
ref_sizes = [size_min, (size_min + size_max) / 2, size_max]
ref_labels = [f"{v:.0f} m²/capita" for v in ref_green]

# Semi-transparent box behind legend for clarity
legend_box = BoxAnnotation(
    left=legend_x - 800,
    right=x_end - 100,
    top=legend_y_top + 4.5,
    bottom=legend_y_top - 2.5 * 3.2 - 1,
    fill_color="white",
    fill_alpha=0.75,
    line_color="#cccccc",
    line_alpha=0.5,
)
p.add_layout(legend_box)

p.add_layout(
    Label(
        x=legend_x - 400,
        y=legend_y_top + 3,
        text="Green Space",
        text_font_size="20pt",
        text_font_style="bold",
        text_color="#333333",
    )
)

for i, (sz, lbl, gv) in enumerate(zip(ref_sizes, ref_labels, ref_green, strict=True)):
    ly = legend_y_top - i * 3.2
    ref_src = ColumnDataSource(data={"x": [legend_x], "y": [ly], "size": [sz], "green_space": [gv]})
    p.scatter(
        x="x",
        y="y",
        size="size",
        source=ref_src,
        fill_color=transform("green_space", color_mapper),
        fill_alpha=0.7,
        line_color="white",
        line_width=2,
    )
    p.add_layout(
        Label(x=legend_x + 700, y=ly, text=lbl, text_font_size="18pt", text_baseline="middle", text_color="#444444")
    )

p.background_fill_color = "#fafafa"
p.border_fill_color = "white"

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML (interactive — leverages Bokeh's hover tooltips)
output_file("plot.html")
save(p)

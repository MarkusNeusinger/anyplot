""" pyplots.ai
polar-scatter: Polar Scatter Plot
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-26
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Legend, LegendItem
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Wind measurements with prevailing directions
np.random.seed(42)

n_points = 120

# Create realistic wind data with prevailing directions (NE and SW)
# Morning winds (prevailing from NE ~45°)
n_morning = 50
morning_angles = np.random.normal(45, 30, n_morning) % 360
morning_speeds = np.random.gamma(3, 3, n_morning) + 5

# Afternoon winds (prevailing from SW ~225°)
n_afternoon = 45
afternoon_angles = np.random.normal(225, 35, n_afternoon) % 360
afternoon_speeds = np.random.gamma(2.5, 4, n_afternoon) + 3

# Evening winds (variable)
n_evening = 25
evening_angles = np.random.uniform(0, 360, n_evening)
evening_speeds = np.random.gamma(2, 2, n_evening) + 2

# Combine data
angles_deg = np.concatenate([morning_angles, afternoon_angles, evening_angles])
speeds = np.concatenate([morning_speeds, afternoon_speeds, evening_speeds])
categories = ["Morning"] * n_morning + ["Afternoon"] * n_afternoon + ["Evening"] * n_evening

# Convert to radians for polar coordinates
angles_rad = np.radians(angles_deg)

# Convert polar to Cartesian for Bokeh (Bokeh doesn't have native polar support)
x = speeds * np.cos(angles_rad)
y = speeds * np.sin(angles_rad)

# Calculate max radius for gridlines
max_speed = np.ceil(np.max(speeds) / 5) * 5

# Create figure
p = figure(
    width=3600,
    height=3600,
    title="polar-scatter · bokeh · pyplots.ai",
    x_range=(-max_speed * 1.2, max_speed * 1.2),
    y_range=(-max_speed * 1.35, max_speed * 1.2),
    tools="",
    toolbar_location=None,
)

# Draw polar grid - radial circles
for r in np.arange(5, max_speed + 1, 5):
    theta_circle = np.linspace(0, 2 * np.pi, 100)
    circle_x = r * np.cos(theta_circle)
    circle_y = r * np.sin(theta_circle)
    p.line(circle_x, circle_y, line_color="#CCCCCC", line_width=2, line_alpha=0.5)
    # Add radius labels at 45 degrees
    label_x = r * np.cos(np.radians(45)) + 0.5
    label_y = r * np.sin(np.radians(45)) + 0.5
    p.text([label_x], [label_y], text=[f"{int(r)}"], text_font_size="16pt", text_color="#666666", text_alpha=0.8)

# Draw angular gridlines (spokes) at 30° intervals
for angle in range(0, 360, 30):
    rad = np.radians(angle)
    p.line(
        [0, max_speed * 1.05 * np.cos(rad)],
        [0, max_speed * 1.05 * np.sin(rad)],
        line_color="#CCCCCC",
        line_width=2,
        line_alpha=0.5,
    )

# Add cardinal direction labels
directions = {0: "E", 90: "N", 180: "W", 270: "S"}
for angle, label in directions.items():
    rad = np.radians(angle)
    label_r = max_speed * 1.1
    p.text(
        [label_r * np.cos(rad)],
        [label_r * np.sin(rad)],
        text=[label],
        text_font_size="22pt",
        text_font_style="bold",
        text_color="#333333",
        text_align="center",
        text_baseline="middle",
    )

# Add intermediate direction labels
intermediate = {45: "NE", 135: "NW", 225: "SW", 315: "SE"}
for angle, label in intermediate.items():
    rad = np.radians(angle)
    label_r = max_speed * 1.1
    p.text(
        [label_r * np.cos(rad)],
        [label_r * np.sin(rad)],
        text=[label],
        text_font_size="18pt",
        text_color="#666666",
        text_align="center",
        text_baseline="middle",
    )

# Color mapping for categories
colors = {"Morning": "#306998", "Afternoon": "#FFD43B", "Evening": "#E74C3C"}

# Create scatter plot for each category
legend_items = []
renderers = []
for cat in ["Morning", "Afternoon", "Evening"]:
    mask = np.array(categories) == cat
    source = ColumnDataSource(data={"x": x[mask], "y": y[mask], "angle": angles_deg[mask], "speed": speeds[mask]})
    r = p.scatter("x", "y", source=source, size=22, color=colors[cat], alpha=0.75, line_color="white", line_width=2)
    renderers.append(r)
    legend_items.append(LegendItem(label=cat, renderers=[r]))

# Add legend
legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="20pt",
    spacing=15,
    glyph_height=25,
    glyph_width=25,
    background_fill_alpha=0.9,
    border_line_color="#CCCCCC",
    padding=15,
    margin=15,
)
p.add_layout(legend, "right")

# Styling
p.title.text_font_size = "28pt"
p.title.align = "center"
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "white"

# Hide axes (using polar grid instead)
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

# Add axis labels for context (positioned below S label)
p.text(
    [0],
    [-max_speed * 1.25],
    text=["Wind Speed (m/s)"],
    text_font_size="20pt",
    text_color="#333333",
    text_align="center",
    text_baseline="top",
)

# Save as PNG and HTML
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Polar Scatter Plot")

""" pyplots.ai
rose-basic: Basic Rose Chart
Library: altair 6.0.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Monthly rainfall in mm (cyclical 12-month pattern)
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
rainfall = [78, 52, 68, 45, 35, 28, 22, 30, 55, 85, 92, 88]

n = len(months)

# Calculate angles starting at 12 o'clock (top) and going clockwise
# -90 degrees offset to start at top, then proceeding clockwise
angle_step = 360 / n
start_angles = [-90 + i * angle_step for i in range(n)]
end_angles = [-90 + (i + 1) * angle_step for i in range(n)]

# Create DataFrame with explicit angles
df = pd.DataFrame(
    {
        "month": months,
        "value": rainfall,
        "order": range(n),
        "startAngle": np.radians(start_angles),
        "endAngle": np.radians(end_angles),
    }
)

# Max value for radius scaling - use 100 for nicer gridline values
max_val = 100

# Color palette - colorblind-friendly distinct colors
colors = [
    "#306998",  # Python Blue (Jan)
    "#FFD43B",  # Python Yellow (Feb)
    "#4ECDC4",  # Teal (Mar)
    "#FF6B6B",  # Coral (Apr)
    "#95E1D3",  # Mint (May)
    "#F38181",  # Salmon (Jun)
    "#A8D5BA",  # Sage (Jul)
    "#FFC93C",  # Gold (Aug)
    "#5D9CEC",  # Sky Blue (Sep)
    "#AC92EB",  # Lavender (Oct)
    "#EC87C0",  # Pink (Nov)
    "#48CFAD",  # Seafoam (Dec)
]

# Create radial gridlines data (concentric circles at 25, 50, 75, 100 mm)
grid_values = [25, 50, 75, 100]
grid_data = pd.DataFrame({"value": grid_values, "label": [f"{v}" for v in grid_values]})

# Chart radius for the radial visualization
chart_radius = 450

# Radial gridlines - concentric circles using mark_arc
gridlines = (
    alt.Chart(grid_data)
    .mark_arc(filled=False, stroke="#cccccc", strokeWidth=1.5, strokeDash=[6, 4])
    .encode(
        theta=alt.value(2 * np.pi),  # Full circle
        radius=alt.Radius("value:Q", scale=alt.Scale(type="linear", domain=[0, max_val], range=[0, chart_radius])),
    )
)

# Grid labels positioned at 3 o'clock position (right side) to avoid overlap with data
grid_label_data = pd.DataFrame(
    {
        "value": grid_values,
        "label": [f"{v} mm" for v in grid_values],
        # Position labels at 3 o'clock (right) - angle = 0 degrees
        "theta": [0.0] * len(grid_values),
    }
)

grid_labels = (
    alt.Chart(grid_label_data)
    .mark_text(fontSize=18, fontWeight="bold", dx=12, color="#666666", align="left", baseline="middle")
    .encode(
        theta=alt.Theta("theta:Q"),
        radius=alt.Radius("value:Q", scale=alt.Scale(type="linear", domain=[0, max_val], range=[0, chart_radius])),
        text="label:N",
    )
)

# Rose chart using mark_arc with explicit angles to start at 12 o'clock
rose = (
    alt.Chart(df)
    .mark_arc(stroke="#ffffff", strokeWidth=2, innerRadius=0)
    .encode(
        theta=alt.Theta("startAngle:Q", stack=None),
        theta2=alt.Theta2("endAngle:Q"),
        radius=alt.Radius("value:Q", scale=alt.Scale(type="linear", domain=[0, max_val], range=[0, chart_radius])),
        color=alt.Color(
            "month:N",
            scale=alt.Scale(domain=months, range=colors),
            legend=None,  # Legend disabled to control canvas size; colors are self-explanatory with labels
        ),
        tooltip=[alt.Tooltip("month:N", title="Month"), alt.Tooltip("value:Q", title="Rainfall (mm)")],
    )
)

# Calculate label positions - midpoint angle for each segment
mid_angles = [(-90 + (i + 0.5) * angle_step) for i in range(n)]
mid_angles_rad = np.radians(mid_angles)

# For small values that cluster together (Jun-Aug: 28, 22, 30), push labels further out
# to prevent crowding; larger values can have labels closer to segment edge
label_radii = []
for v in rainfall:
    if v < 35:
        # Small segments - push label further outside segment
        label_radii.append(max(v * 1.35, 45))
    else:
        # Normal segments - position just outside
        label_radii.append(v * 1.15)

# Create label data with theta and radius for polar positioning
label_data = pd.DataFrame({"month": months, "value": rainfall, "theta": mid_angles_rad, "labelRadius": label_radii})

# Create month labels positioned at outer edge of chart
month_label_data = pd.DataFrame(
    {
        "month": months,
        "theta": mid_angles_rad,
        "labelRadius": [115] * n,  # Just outside the 100mm gridline
    }
)

# Text labels showing values on each segment using polar coordinates
text = (
    alt.Chart(label_data)
    .mark_text(fontSize=20, fontWeight="bold")
    .encode(
        theta=alt.Theta("theta:Q"),
        radius=alt.Radius(
            "labelRadius:Q", scale=alt.Scale(type="linear", domain=[0, max_val], range=[0, chart_radius])
        ),
        text=alt.Text("value:Q"),
        color=alt.value("#333333"),
    )
)

# Month labels at outer edge
month_labels = (
    alt.Chart(month_label_data)
    .mark_text(fontSize=22, fontWeight="bold")
    .encode(
        theta=alt.Theta("theta:Q"),
        radius=alt.Radius(
            "labelRadius:Q", scale=alt.Scale(type="linear", domain=[0, max_val], range=[0, chart_radius])
        ),
        text=alt.Text("month:N"),
        color=alt.value("#333333"),
    )
)

# Combine all layers
chart = (
    alt.layer(gridlines, grid_labels, rose, text, month_labels)
    .properties(title=alt.Title(text="rose-basic · altair · pyplots.ai", fontSize=32, anchor="middle", offset=15))
    .configure_view(strokeWidth=0)
    .configure_axis(grid=False, domain=False, ticks=False, labels=False, title=None)
)

# Save chart - Altair radial charts position content in upper portion
# Use high scale factor to ensure quality, then crop to center the content
chart.save("plot_raw.png", scale_factor=3.0)
chart.save("plot.html")

# Post-process: crop to center the radial chart and resize to 3600x3600 (square format)
from PIL import Image


img = Image.open("plot_raw.png")
width, height = img.size

# Altair radial charts center content horizontally but place it in the upper portion vertically
# The radial center is approximately at 36% from the top of the rendered image
content_center_y = int(height * 0.36)
content_center_x = width // 2

# Use a crop size that captures all content including outer month labels with some padding
crop_size = min(width, int(height * 0.80))

# Center the crop on the content
left = content_center_x - crop_size // 2
top = content_center_y - crop_size // 2
right = left + crop_size
bottom = top + crop_size

# Adjust if crop extends beyond image boundaries
if left < 0:
    left = 0
    right = crop_size
if top < 0:
    top = 0
    bottom = crop_size
if right > width:
    right = width
    left = width - crop_size
if bottom > height:
    bottom = height
    top = height - crop_size

cropped = img.crop((left, top, right, bottom))

# Resize to target 3600x3600
final = cropped.resize((3600, 3600), Image.Resampling.LANCZOS)
final.save("plot.png")

# Clean up temp file
import os


os.remove("plot_raw.png")

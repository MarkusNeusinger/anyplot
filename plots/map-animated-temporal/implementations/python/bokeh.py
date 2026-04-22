""" pyplots.ai
map-animated-temporal: Animated Map over Time
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-20
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.layouts import column, row
from bokeh.models import Button, ColumnDataSource, CustomJS, HoverTool, Label, Slider
from bokeh.plotting import figure


# Data - Simulated earthquake aftershock sequence over 20 days
np.random.seed(42)

# Create epicenter and spreading aftershocks
n_days = 20
points_per_day = 25
total_points = n_days * points_per_day

# Main earthquake location (simulated Pacific region)
epicenter_lat = 35.0
epicenter_lon = 140.0

timestamps = []
latitudes = []
longitudes = []
magnitudes = []

for day in range(n_days):
    # Aftershocks spread outward over time with decreasing magnitude
    spread = 0.5 + day * 0.15  # Increasing spread radius
    base_magnitude = 5.0 - day * 0.15  # Decreasing average magnitude

    for _ in range(points_per_day):
        angle = np.random.uniform(0, 2 * np.pi)
        distance = np.random.exponential(spread)
        lat = epicenter_lat + distance * np.sin(angle)
        lon = epicenter_lon + distance * np.cos(angle)
        mag = max(2.0, base_magnitude + np.random.normal(0, 0.5))

        timestamps.append(day)
        latitudes.append(lat)
        longitudes.append(lon)
        magnitudes.append(mag)

df = pd.DataFrame({"day": timestamps, "lat": latitudes, "lon": longitudes, "magnitude": magnitudes})

# Create sources for each day
all_sources = {}
for day in range(n_days):
    day_data = df[df["day"] <= day]  # Cumulative: show all points up to this day
    all_sources[day] = {
        "lat": day_data["lat"].tolist(),
        "lon": day_data["lon"].tolist(),
        "magnitude": day_data["magnitude"].tolist(),
        "size": (day_data["magnitude"] * 4).tolist(),  # Size based on magnitude
        "alpha": [0.3 + 0.7 * (1 - (day - d) / n_days) for d in day_data["day"]],  # Fade older
    }

# Initial data source (day 0)
source = ColumnDataSource(
    data={
        "lat": all_sources[0]["lat"],
        "lon": all_sources[0]["lon"],
        "magnitude": all_sources[0]["magnitude"],
        "size": all_sources[0]["size"],
        "alpha": all_sources[0]["alpha"],
    }
)

# Store all data in a separate source for JS access
all_data_source = ColumnDataSource(data={"all_sources": [all_sources]})

# Create figure with geographic bounds
p = figure(
    width=4800,
    height=2700,
    x_range=(130, 150),
    y_range=(28, 42),
    x_axis_label="Longitude",
    y_axis_label="Latitude",
    title="Earthquake Aftershock Sequence · map-animated-temporal · bokeh · pyplots.ai",
    tools="pan,wheel_zoom,box_zoom,reset",
)

# Style the figure for large canvas
p.title.text_font_size = "32pt"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Draw simple coastline approximation (Japan region)
coast_lon = [130, 131, 132, 134, 135, 136, 137, 139, 140, 141, 142, 144, 146, 148, 150]
coast_lat = [33, 34, 34.5, 35, 35.5, 36, 37, 38, 40, 41, 42, 42, 41, 40, 39]
p.line(coast_lon, coast_lat, line_width=3, line_color="#888888", alpha=0.5)

# Draw grid lines for geographic reference
for lat in range(28, 43, 2):
    p.line([130, 150], [lat, lat], line_width=1, line_color="#CCCCCC", alpha=0.3)
for lon in range(130, 151, 2):
    p.line([lon, lon], [28, 42], line_width=1, line_color="#CCCCCC", alpha=0.3)

# Mark epicenter - larger star marker for better visibility in legend
p.scatter(
    [epicenter_lon],
    [epicenter_lat],
    size=40,
    color="#FFD43B",
    marker="star",
    line_color="#B8860B",
    line_width=2,
    legend_label="Epicenter",
)

# Plot aftershocks
aftershocks = p.scatter(
    x="lon",
    y="lat",
    size="size",
    fill_color="#306998",
    fill_alpha="alpha",
    line_color="#1a3a5c",
    line_width=2,
    source=source,
    legend_label="Aftershocks",
)

# Add hover tool
hover = HoverTool(tooltips=[("Location", "(@lon, @lat)"), ("Magnitude", "@magnitude{0.1}")], renderers=[aftershocks])
p.add_tools(hover)

# Time label
time_label = Label(x=131, y=41, text="Day: 0", text_font_size="28pt", text_color="#306998", text_font_style="bold")
p.add_layout(time_label)

# Legend styling - position near the data area for better integration
p.legend.location = "top_right"
p.legend.label_text_font_size = "20pt"
p.legend.background_fill_alpha = 0.9
p.legend.glyph_height = 35
p.legend.glyph_width = 35
p.legend.padding = 15
p.legend.spacing = 10
p.legend.margin = 15

# Create slider
slider = Slider(start=0, end=n_days - 1, value=0, step=1, title="Day", width=800)

# Play button
play_button = Button(label="▶ Play", button_type="success", width=150)

# JavaScript callback for slider
slider_callback = CustomJS(
    args={"source": source, "all_data": all_data_source, "time_label": time_label, "n_days": n_days},
    code="""
    const day = cb_obj.value;
    const all_sources = all_data.data['all_sources'][0];
    const day_data = all_sources[day];

    source.data['lon'] = day_data['lon'];
    source.data['lat'] = day_data['lat'];
    source.data['magnitude'] = day_data['magnitude'];
    source.data['size'] = day_data['size'];
    source.data['alpha'] = day_data['alpha'];
    source.change.emit();

    time_label.text = 'Day: ' + day;
""",
)
slider.js_on_change("value", slider_callback)

# JavaScript callback for play button (animation)
play_callback = CustomJS(
    args={"slider": slider, "button": play_button, "n_days": n_days},
    code="""
    if (button.label.includes('Play')) {
        button.label = '⏸ Pause';
        button.button_type = 'warning';

        window.animation_interval = setInterval(function() {
            let current = slider.value;
            if (current < n_days - 1) {
                slider.value = current + 1;
            } else {
                slider.value = 0;
            }
        }, 500);
    } else {
        button.label = '▶ Play';
        button.button_type = 'success';
        clearInterval(window.animation_interval);
    }
""",
)
play_button.js_on_click(play_callback)

# Layout
controls = row(play_button, slider)
layout = column(p, controls)

# Save outputs
output_file("plot.html", title="Animated Temporal Map")
save(layout)
export_png(p, filename="plot.png")

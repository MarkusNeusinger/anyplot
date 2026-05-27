"""anyplot.ai
map-animated-temporal: Animated Map over Time
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-05-27
"""

import os
import sys
import time
from pathlib import Path


# Change to script directory for consistent file saving
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)

# Remove current directory from sys.path to avoid shadowing the bokeh package
sys.path = [p for p in sys.path if p != str(script_dir) and p != ""]
if __name__ in sys.modules:
    del sys.modules[__name__]

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column, row
from bokeh.models import Button, ColumnDataSource, CustomJS, HoverTool, Label, Slider
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

BRAND = "#009E73"  # anyplot palette position 1 — always first series
EPICENTER_COLOR = "#AE3030"  # matte red — semantic anchor for hazard

# Data — earthquake aftershock sequence, Japan region, 20-day simulation
np.random.seed(42)

n_days = 20
points_per_day = 25
epicenter_lat = 35.0
epicenter_lon = 140.0

timestamps, latitudes, longitudes, magnitudes = [], [], [], []

for day in range(n_days):
    spread = 0.5 + day * 0.15
    base_mag = 5.0 - day * 0.15
    for _ in range(points_per_day):
        angle = np.random.uniform(0, 2 * np.pi)
        dist = np.random.exponential(spread)
        lat = epicenter_lat + dist * np.sin(angle)
        lon = epicenter_lon + dist * np.cos(angle)
        mag = max(2.0, base_mag + np.random.normal(0, 0.5))
        timestamps.append(day)
        latitudes.append(lat)
        longitudes.append(lon)
        magnitudes.append(mag)

df = pd.DataFrame({"day": timestamps, "lat": latitudes, "lon": longitudes, "magnitude": magnitudes})

# Cumulative frames for JS animation
all_frames = {}
for day in range(n_days):
    day_data = df[df["day"] <= day]
    all_frames[day] = {
        "lat": day_data["lat"].tolist(),
        "lon": day_data["lon"].tolist(),
        "magnitude": day_data["magnitude"].tolist(),
        "size": (day_data["magnitude"] * 4).tolist(),
        "alpha": [0.35 + 0.65 * (1.0 - (day - d) / n_days) for d in day_data["day"]],
    }

# Title with scaled fontsize
title_str = "Earthquake Aftershocks · map-animated-temporal · python · bokeh · anyplot.ai"
n_chars = len(title_str)
title_pt = max(34, round(50 * 67 / n_chars)) if n_chars > 67 else 50
title_fontsize = f"{title_pt}pt"

# Initial data source (day 0)
source = ColumnDataSource(
    data={
        "lat": all_frames[0]["lat"],
        "lon": all_frames[0]["lon"],
        "magnitude": all_frames[0]["magnitude"],
        "size": all_frames[0]["size"],
        "alpha": all_frames[0]["alpha"],
    }
)
all_data_source = ColumnDataSource(data={"frames": [all_frames]})

# Figure — 3200×1800 landscape canvas
p = figure(
    width=3200,
    height=1800,
    x_range=(130, 150),
    y_range=(28, 42),
    x_axis_label="Longitude (°E)",
    y_axis_label="Latitude (°N)",
    title=title_str,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Font sizing
p.title.text_font_size = title_fontsize
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.title.text_color = INK
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15

# Coastline approximation (Japan region)
coast_lon = [130, 131, 132, 134, 135, 136, 137, 139, 140, 141, 142, 144, 146, 148, 150]
coast_lat = [33, 34, 34.5, 35, 35.5, 36, 37, 38, 40, 41, 42, 42, 41, 40, 39]
p.line(coast_lon, coast_lat, line_width=4, line_color=INK_SOFT, alpha=0.45)

# Aftershocks (drawn first so epicenter renders on top)
aftershocks = p.scatter(
    x="lon",
    y="lat",
    size="size",
    fill_color=BRAND,
    fill_alpha="alpha",
    line_color=PAGE_BG,
    line_width=1,
    source=source,
    legend_label="Aftershocks",
)

# Epicenter marker (drawn on top of aftershocks)
p.scatter(
    [epicenter_lon],
    [epicenter_lat],
    size=55,
    color=EPICENTER_COLOR,
    marker="star",
    line_color=INK,
    line_width=2,
    legend_label="Epicenter (M7.2)",
)

hover = HoverTool(
    tooltips=[("Position", "(@lon{0.2f}°E, @lat{0.2f}°N)"), ("Magnitude", "@magnitude{0.1f}")], renderers=[aftershocks]
)
p.add_tools(hover)

# Day label overlay
time_label = Label(
    x=131,
    y=40.2,
    text="Day 0",
    text_font_size="38pt",
    text_color=INK,
    text_font_style="bold",
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.85,
)
p.add_layout(time_label)

# Legend
p.legend.location = "bottom_right"
p.legend.label_text_font_size = "34pt"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.padding = 20
p.legend.spacing = 15
p.legend.margin = 20

# Slider and play button
slider = Slider(start=0, end=n_days - 1, value=0, step=1, title="Day", width=1000)
play_button = Button(label="▶ Play", button_type="success", width=200)

slider_callback = CustomJS(
    args={"source": source, "all_data": all_data_source, "time_label": time_label, "n_days": n_days},
    code="""
    const day = cb_obj.value;
    const frames = all_data.data['frames'][0];
    const frame = frames[day];

    source.data['lon'] = frame['lon'];
    source.data['lat'] = frame['lat'];
    source.data['magnitude'] = frame['magnitude'];
    source.data['size'] = frame['size'];
    source.data['alpha'] = frame['alpha'];
    source.change.emit();

    time_label.text = 'Day ' + day;
    """,
)
slider.js_on_change("value", slider_callback)

play_callback = CustomJS(
    args={"slider": slider, "button": play_button, "n_days": n_days},
    code="""
    if (button.label.includes('Play')) {
        button.label = '⏸ Pause';
        button.button_type = 'warning';
        window.animation_interval = setInterval(function() {
            const cur = slider.value;
            slider.value = cur < n_days - 1 ? cur + 1 : 0;
        }, 500);
    } else {
        button.label = '▶ Play';
        button.button_type = 'success';
        clearInterval(window.animation_interval);
    }
    """,
)
play_button.js_on_click(play_callback)

controls = row(play_button, slider)
layout = column(p, controls)

# Save interactive HTML — figure (1800 px) is at the top; controls sit below the fold
output_file(f"plot-{THEME}.html", title="Earthquake Aftershock Animation")
save(layout)

# Screenshot: CDP override locks viewport to exact figure dimensions,
# so save_screenshot() captures only the 3200×1800 figure area
W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

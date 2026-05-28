""" anyplot.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-15
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column, row
from bokeh.models import Button, ColumnDataSource, CustomJS, Div, HoverTool, Label, Slider
from bokeh.plotting import figure
from bokeh.transform import factor_cmap
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (regions)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data: Simulated country metrics over 20 years (Gapminder-style)
np.random.seed(42)

n_countries = 15
years = np.arange(2004, 2024)
n_years = len(years)

countries = [
    "Country A",
    "Country B",
    "Country C",
    "Country D",
    "Country E",
    "Country F",
    "Country G",
    "Country H",
    "Country I",
    "Country J",
    "Country K",
    "Country L",
    "Country M",
    "Country N",
    "Country O",
]

regions = ["North", "South", "East", "West", "Central"]
country_regions = [regions[i % 5] for i in range(n_countries)]

# Generate time-series data for each country
data_frames = []
for i, country in enumerate(countries):
    base_gdp = np.random.uniform(5000, 40000)
    base_life = np.random.uniform(55, 75)
    base_pop = np.random.uniform(5, 200)  # millions

    gdp_growth = np.random.uniform(0.02, 0.06)
    life_improvement = np.random.uniform(0.2, 0.5)
    pop_growth = np.random.uniform(0.005, 0.02)

    # Add some noise and variation
    gdp_noise = np.cumsum(np.random.randn(n_years) * 500)
    life_noise = np.cumsum(np.random.randn(n_years) * 0.3)
    pop_noise = np.cumsum(np.random.randn(n_years) * 0.5)

    gdp = base_gdp * (1 + gdp_growth) ** np.arange(n_years) + gdp_noise
    life_exp = base_life + life_improvement * np.arange(n_years) + life_noise
    population = base_pop * (1 + pop_growth) ** np.arange(n_years) + pop_noise

    # Ensure positive values
    gdp = np.maximum(gdp, 1000)
    life_exp = np.clip(life_exp, 40, 90)
    population = np.maximum(population, 1)

    for j, year in enumerate(years):
        data_frames.append(
            {
                "country": country,
                "region": country_regions[i],
                "year": year,
                "gdp_per_capita": gdp[j],
                "life_expectancy": life_exp[j],
                "population": population[j],
            }
        )

df = pd.DataFrame(data_frames)

# Initial data (first year)
initial_year = years[0]
initial_data = df[df["year"] == initial_year].copy()

# Create ColumnDataSource
source = ColumnDataSource(
    data={
        "x": initial_data["gdp_per_capita"].values,
        "y": initial_data["life_expectancy"].values,
        "size": (initial_data["population"].values ** 0.5) * 5,
        "country": initial_data["country"].values,
        "region": initial_data["region"].values,
        "population": initial_data["population"].values,
    }
)

# Store all data for animation
all_data = {}
for year in years:
    year_data = df[df["year"] == year]
    all_data[str(year)] = {
        "x": year_data["gdp_per_capita"].tolist(),
        "y": year_data["life_expectancy"].tolist(),
        "size": [(p**0.5) * 5 for p in year_data["population"].values],
        "country": year_data["country"].tolist(),
        "region": year_data["region"].tolist(),
        "population": year_data["population"].tolist(),
    }

# Define regions and color palette using Okabe-Ito
regions_list = ["North", "South", "East", "West", "Central"]
color_palette = IMPRINT

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="scatter-animated-controls · bokeh · anyplot.ai",
    x_axis_label="GDP per Capita (USD)",
    y_axis_label="Life Expectancy (Years)",
    x_range=(0, 80000),
    y_range=(40, 95),
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Style the figure with theme-adaptive colors
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

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

# Grid styling
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Add margins
p.min_border_left = 120
p.min_border_right = 120
p.min_border_top = 100
p.min_border_bottom = 100

# Add scatter plot
scatter = p.scatter(
    x="x",
    y="y",
    size="size",
    color=factor_cmap("region", palette=color_palette, factors=regions_list),
    alpha=0.7,
    line_color=PAGE_BG,
    line_width=1,
    source=source,
    legend_field="region",
)

# Configure legend
p.legend.location = "top_left"
p.legend.title = "Region"
p.legend.title_text_font_size = "18pt"
p.legend.label_text_font_size = "16pt"
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 30
p.legend.glyph_width = 30
p.legend.spacing = 12
p.legend.padding = 15
p.legend.margin = 20

# Add hover tool
hover = HoverTool(
    tooltips=[
        ("Country", "@country"),
        ("Region", "@region"),
        ("GDP per Capita", "$@x{0,0}"),
        ("Life Expectancy", "@y{0.1} years"),
        ("Population", "@population{0.1} million"),
    ],
    renderers=[scatter],
)
p.add_tools(hover)

# Add year label
year_label = Label(
    x=70000, y=50, text=str(initial_year), text_font_size="150pt", text_color=INK, text_alpha=0.15, text_align="right"
)
p.add_layout(year_label)

# Create slider
slider = Slider(start=int(years[0]), end=int(years[-1]), value=int(years[0]), step=1, title="Year", width=600)

# Create play/pause button
button = Button(label="▶ Play", button_type="success", width=150)

# JavaScript callback for slider
slider_callback = CustomJS(
    args={"source": source, "all_data": all_data, "year_label": year_label},
    code="""
    const year = cb_obj.value.toString();
    const data = all_data[year];

    source.data['x'] = data['x'];
    source.data['y'] = data['y'];
    source.data['size'] = data['size'];
    source.data['country'] = data['country'];
    source.data['region'] = data['region'];
    source.data['population'] = data['population'];
    source.change.emit();

    year_label.text = year;
""",
)
slider.js_on_change("value", slider_callback)

# JavaScript callback for play/pause button
button_callback = CustomJS(
    args={"button": button, "slider": slider, "years_start": int(years[0]), "years_end": int(years[-1])},
    code="""
    if (button.label.includes('Play')) {
        button.label = '⏸ Pause';
        button.button_type = 'warning';

        // Start animation
        window.animation_interval = setInterval(function() {
            if (slider.value >= slider.end) {
                slider.value = slider.start;
            } else {
                slider.value = slider.value + 1;
            }
        }, 500);
    } else {
        button.label = '▶ Play';
        button.button_type = 'success';

        // Stop animation
        if (window.animation_interval) {
            clearInterval(window.animation_interval);
        }
    }
""",
)
button.js_on_click(button_callback)

# Create title div
title_div = Div(
    text="""
    <div style="font-size: 28pt; font-weight: bold; margin-bottom: 20px; color: inherit;">
        Country Development Over Time
    </div>
    <div style="font-size: 18pt; color: inherit; margin-bottom: 10px; opacity: 0.8;">
        Bubble size represents population. Click Play to animate or drag the slider.
    </div>
""",
    width=1000,
)

# Layout
controls = row(button, slider)
layout = column(title_div, controls, p)

# Save HTML (interactive version with controls)
output_file(f"plot-{THEME}.html")
save(layout)

# Screenshot with Selenium for PNG export
W, H = 4800, 2700
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
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

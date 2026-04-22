""" pyplots.ai
scatter-animated-controls: Animated Scatter Plot with Play Controls
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.layouts import column, row
from bokeh.models import Button, ColumnDataSource, CustomJS, Div, HoverTool, Label, Slider
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.transform import factor_cmap


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

# Create ColumnDataSource (color is handled by factor_cmap based on region)
source = ColumnDataSource(
    data={
        "x": initial_data["gdp_per_capita"].values,
        "y": initial_data["life_expectancy"].values,
        "size": (initial_data["population"].values ** 0.5) * 5,  # Scale for visibility
        "country": initial_data["country"].values,
        "region": initial_data["region"].values,
        "population": initial_data["population"].values,
    }
)

# Store all data for animation (color is handled by factor_cmap based on region)
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

# Define regions list and color palette for factor_cmap
regions_list = ["North", "South", "East", "West", "Central"]
color_palette = ["#306998", "#FFD43B", "#E15759", "#76B7B2", "#59A14F"]

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="scatter-animated-controls · bokeh · pyplots.ai",
    x_axis_label="GDP per Capita (USD)",
    y_axis_label="Life Expectancy (Years)",
    x_range=(0, 80000),
    y_range=(40, 95),
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

# Style the figure - increased font sizes for better readability at 4800x2700
p.title.text_font_size = "48pt"
p.xaxis.axis_label_text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "36pt"
p.xaxis.major_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "28pt"

# Grid styling
p.grid.grid_line_alpha = 0.3
p.grid.grid_line_dash = [6, 4]

# Background
p.background_fill_color = "#fafafa"

# Add margins to prevent legend clipping
p.min_border_left = 120
p.min_border_right = 120
p.min_border_top = 100
p.min_border_bottom = 100

# Add scatter plot with legend_field for native legend in PNG export
scatter = p.scatter(
    x="x",
    y="y",
    size="size",
    color=factor_cmap("region", palette=color_palette, factors=regions_list),
    alpha=0.7,
    line_color="white",
    line_width=2,
    source=source,
    legend_field="region",
)

# Configure legend for visibility in PNG export - positioned inside plot with large fonts
p.legend.location = "top_left"
p.legend.title = "Region"
p.legend.title_text_font_size = "36pt"
p.legend.label_text_font_size = "32pt"
p.legend.glyph_height = 60
p.legend.glyph_width = 60
p.legend.spacing = 15
p.legend.padding = 30
p.legend.margin = 40
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = "#aaaaaa"
p.legend.border_line_width = 2

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

# Add year label (large background text) - increased size for better visibility
year_label = Label(
    x=70000,
    y=50,
    text=str(initial_year),
    text_font_size="150pt",
    text_color="#cccccc",
    text_alpha=0.5,
    text_align="right",
)
p.add_layout(year_label)

# Create slider
slider = Slider(start=int(years[0]), end=int(years[-1]), value=int(years[0]), step=1, title="Year", width=600)

# Create play/pause button
button = Button(label="▶ Play", button_type="success", width=150)

# Create legend info display
legend_html = """
<div style="font-size: 20pt; padding: 15px; background: #f5f5f5; border-radius: 8px;">
    <strong style="font-size: 24pt;">Regions:</strong><br>
    <span style="color: #306998;">●</span> North &nbsp;&nbsp;
    <span style="color: #FFD43B;">●</span> South &nbsp;&nbsp;
    <span style="color: #E15759;">●</span> East &nbsp;&nbsp;
    <span style="color: #76B7B2;">●</span> West &nbsp;&nbsp;
    <span style="color: #59A14F;">●</span> Central
</div>
"""
legend_div = Div(text=legend_html, width=800)

# JavaScript callback for slider (region drives color via factor_cmap)
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
    <div style="font-size: 28pt; font-weight: bold; margin-bottom: 20px; color: #333;">
        Country Development Over Time (2004-2023)
    </div>
    <div style="font-size: 18pt; color: #666; margin-bottom: 10px;">
        Bubble size represents population. Click Play to animate or drag the slider.
    </div>
""",
    width=1000,
)

# Layout
controls = row(button, slider, legend_div)
layout = column(title_div, controls, p)

# Save HTML (interactive version with controls)
save(layout, filename="plot.html", title="Animated Scatter Plot", resources=CDN)

# For PNG export, show the middle year frame as a representative snapshot
middle_year = years[len(years) // 2]
middle_data = df[df["year"] == middle_year]

# Update source for static export (color via factor_cmap based on region)
source.data = {
    "x": middle_data["gdp_per_capita"].values,
    "y": middle_data["life_expectancy"].values,
    "size": (middle_data["population"].values ** 0.5) * 5,
    "country": middle_data["country"].values,
    "region": middle_data["region"].values,
    "population": middle_data["population"].values,
}
year_label.text = str(middle_year)

# Export PNG (static snapshot)
export_png(p, filename="plot.png")

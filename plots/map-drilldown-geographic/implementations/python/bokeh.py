""" pyplots.ai
map-drilldown-geographic: Drillable Geographic Map
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 87/100 | Created: 2026-01-20
"""

import numpy as np
from bokeh.io import export_png
from bokeh.layouts import column
from bokeh.models import ColorBar, ColumnDataSource, CustomJS, Div, HoverTool, LinearColorMapper, TapTool
from bokeh.palettes import Blues9
from bokeh.plotting import figure


np.random.seed(42)

# =============================================================================
# Data: Hierarchical geographic data with countries -> states -> cities
# Using synthetic sales data in millions USD
# =============================================================================

# Countries with approximate polygon boundaries (simplified rectangles for demo)
countries_data = {
    "name": ["United States", "Canada", "Mexico", "Brazil", "Argentina"],
    "value": [850, 320, 180, 420, 95],  # Aggregated sales
    "x": [
        [-125, -65, -65, -125],
        [-140, -50, -50, -140],
        [-118, -86, -86, -118],
        [-74, -34, -34, -74],
        [-73, -53, -53, -73],
    ],
    "y": [[24, 24, 49, 49], [49, 49, 72, 72], [14, 14, 32, 32], [-34, -34, 5, 5], [-55, -55, -22, -22]],
    "centroid_x": [-95, -95, -102, -54, -63],
    "centroid_y": [37, 60, 23, -15, -38],
    "has_children": [True, True, True, True, True],
}

# US States data (shown when drilling into US)
us_states_data = {
    "name": ["California", "Texas", "New York", "Florida", "Illinois", "Washington"],
    "value": [220, 180, 150, 120, 90, 90],
    "x": [
        [-124, -114, -114, -124],
        [-106, -93, -93, -106],
        [-80, -72, -72, -80],
        [-87, -80, -80, -87],
        [-91, -87, -87, -91],
        [-124, -117, -117, -124],
    ],
    "y": [[32, 32, 42, 42], [26, 26, 36, 36], [40, 40, 45, 45], [25, 25, 31, 31], [37, 37, 42, 42], [45, 45, 49, 49]],
    "centroid_x": [-119, -99.5, -76, -83.5, -89, -120.5],
    "centroid_y": [37, 31, 42.5, 28, 39.5, 47],
    "parent": ["United States"] * 6,
    "has_children": [True, True, True, True, True, True],
}

# California cities (shown when drilling into California)
ca_cities_data = {
    "name": ["Los Angeles", "San Francisco", "San Diego", "Sacramento", "San Jose"],
    "value": [85, 55, 35, 25, 20],
    "x": [
        [-118.8, -117.5, -117.5, -118.8],
        [-122.8, -122.0, -122.0, -122.8],
        [-117.5, -116.8, -116.8, -117.5],
        [-121.8, -121.0, -121.0, -121.8],
        [-122.2, -121.5, -121.5, -122.2],
    ],
    "y": [
        [33.5, 33.5, 34.5, 34.5],
        [37.3, 37.3, 38.0, 38.0],
        [32.4, 32.4, 33.2, 33.2],
        [38.2, 38.2, 39.0, 39.0],
        [37.0, 37.0, 37.6, 37.6],
    ],
    "centroid_x": [-118.15, -122.4, -117.15, -121.4, -121.85],
    "centroid_y": [34, 37.65, 32.8, 38.6, 37.3],
    "parent": ["California"] * 5,
    "has_children": [False, False, False, False, False],
}

# Color mapper for choropleth
color_mapper = LinearColorMapper(palette=Blues9[::-1], low=0, high=900)

# =============================================================================
# Create main figure
# =============================================================================
p = figure(
    width=4800,
    height=2700,
    x_range=(-140, -25),
    y_range=(-60, 75),
    tools="pan,wheel_zoom,reset",
    toolbar_location="right",
)

# Main title
p.title.text = "map-drilldown-geographic · bokeh · pyplots.ai"
p.title.text_font_size = "28pt"
p.title.align = "center"

# =============================================================================
# Country level patches (initial view)
# =============================================================================
countries_source = ColumnDataSource(
    data={
        "xs": countries_data["x"],
        "ys": countries_data["y"],
        "name": countries_data["name"],
        "value": countries_data["value"],
        "centroid_x": countries_data["centroid_x"],
        "centroid_y": countries_data["centroid_y"],
        "has_children": countries_data["has_children"],
    }
)

country_patches = p.patches(
    xs="xs",
    ys="ys",
    source=countries_source,
    fill_color={"field": "value", "transform": color_mapper},
    line_color="#306998",
    line_width=3,
    alpha=0.8,
    hover_fill_color="#FFD43B",
    hover_line_color="#306998",
    hover_alpha=0.9,
    selection_fill_color="#FFD43B",
    name="countries",
)

# Country labels - name (with contrasting background for visibility in PNG)
countries_label_source = ColumnDataSource(
    data={
        "x": countries_data["centroid_x"],
        "y": [cy + 4 for cy in countries_data["centroid_y"]],  # Offset up for name
        "name": countries_data["name"],
    }
)

p.text(
    x="x",
    y="y",
    text="name",
    source=countries_label_source,
    text_font_size="28pt",
    text_align="center",
    text_baseline="middle",
    text_color="#000000",
    text_font_style="bold",
    background_fill_color="rgba(255, 255, 255, 0.85)",
    background_fill_alpha=0.85,
    name="country_labels",
)

# Country value labels - displayed below name for static view visibility
countries_value_source = ColumnDataSource(
    data={
        "x": countries_data["centroid_x"],
        "y": [cy - 5 for cy in countries_data["centroid_y"]],  # Offset down for value
        "value": [f"${v}M" for v in countries_data["value"]],
    }
)

p.text(
    x="x",
    y="y",
    text="value",
    source=countries_value_source,
    text_font_size="24pt",
    text_align="center",
    text_baseline="middle",
    text_color="#1a3c5a",
    text_font_style="bold",
    background_fill_color="rgba(255, 255, 255, 0.85)",
    background_fill_alpha=0.85,
    name="country_value_labels",
)

# =============================================================================
# US States level patches (hidden initially)
# =============================================================================
states_source = ColumnDataSource(
    data={
        "xs": us_states_data["x"],
        "ys": us_states_data["y"],
        "name": us_states_data["name"],
        "value": us_states_data["value"],
        "centroid_x": us_states_data["centroid_x"],
        "centroid_y": us_states_data["centroid_y"],
        "has_children": us_states_data["has_children"],
    }
)

state_patches = p.patches(
    xs="xs",
    ys="ys",
    source=states_source,
    fill_color={"field": "value", "transform": color_mapper},
    line_color="#306998",
    line_width=2,
    alpha=0.8,
    hover_fill_color="#FFD43B",
    hover_line_color="#306998",
    hover_alpha=0.9,
    visible=False,
    name="states",
)

states_label_source = ColumnDataSource(
    data={
        "x": us_states_data["centroid_x"],
        "y": [cy + 1.5 for cy in us_states_data["centroid_y"]],  # Offset up for name
        "name": us_states_data["name"],
    }
)

state_labels = p.text(
    x="x",
    y="y",
    text="name",
    source=states_label_source,
    text_font_size="22pt",
    text_align="center",
    text_baseline="middle",
    text_color="#000000",
    text_font_style="bold",
    background_fill_color="rgba(255, 255, 255, 0.85)",
    background_fill_alpha=0.85,
    visible=False,
    name="state_labels",
)

# State value labels
states_value_source = ColumnDataSource(
    data={
        "x": us_states_data["centroid_x"],
        "y": [cy - 2 for cy in us_states_data["centroid_y"]],  # Offset down for value
        "value": [f"${v}M" for v in us_states_data["value"]],
    }
)

state_value_labels = p.text(
    x="x",
    y="y",
    text="value",
    source=states_value_source,
    text_font_size="20pt",
    text_align="center",
    text_baseline="middle",
    text_color="#1a3c5a",
    text_font_style="bold",
    background_fill_color="rgba(255, 255, 255, 0.85)",
    background_fill_alpha=0.85,
    visible=False,
    name="state_value_labels",
)

# =============================================================================
# California cities level patches (hidden initially)
# =============================================================================
cities_source = ColumnDataSource(
    data={
        "xs": ca_cities_data["x"],
        "ys": ca_cities_data["y"],
        "name": ca_cities_data["name"],
        "value": ca_cities_data["value"],
        "centroid_x": ca_cities_data["centroid_x"],
        "centroid_y": ca_cities_data["centroid_y"],
        "has_children": ca_cities_data["has_children"],
    }
)

city_patches = p.patches(
    xs="xs",
    ys="ys",
    source=cities_source,
    fill_color={"field": "value", "transform": color_mapper},
    line_color="#306998",
    line_width=2,
    alpha=0.8,
    hover_fill_color="#FFD43B",
    hover_line_color="#306998",
    hover_alpha=0.9,
    visible=False,
    name="cities",
)

cities_label_source = ColumnDataSource(
    data={
        "x": ca_cities_data["centroid_x"],
        "y": [cy + 0.25 for cy in ca_cities_data["centroid_y"]],  # Offset up for name
        "name": ca_cities_data["name"],
    }
)

city_labels = p.text(
    x="x",
    y="y",
    text="name",
    source=cities_label_source,
    text_font_size="20pt",
    text_align="center",
    text_baseline="middle",
    text_color="#000000",
    text_font_style="bold",
    background_fill_color="rgba(255, 255, 255, 0.85)",
    background_fill_alpha=0.85,
    visible=False,
    name="city_labels",
)

# City value labels
cities_value_source = ColumnDataSource(
    data={
        "x": ca_cities_data["centroid_x"],
        "y": [cy - 0.35 for cy in ca_cities_data["centroid_y"]],  # Offset down for value
        "value": [f"${v}M" for v in ca_cities_data["value"]],
    }
)

city_value_labels = p.text(
    x="x",
    y="y",
    text="value",
    source=cities_value_source,
    text_font_size="18pt",
    text_align="center",
    text_baseline="middle",
    text_color="#1a3c5a",
    text_font_style="bold",
    background_fill_color="rgba(255, 255, 255, 0.85)",
    background_fill_alpha=0.85,
    visible=False,
    name="city_value_labels",
)

# =============================================================================
# Breadcrumb navigation
# =============================================================================
breadcrumb_div = Div(
    text="""<div style='font-size: 24pt; font-family: sans-serif; padding: 15px 30px;
                        background: #f5f5f5; border-radius: 8px; display: inline-block;'>
            <span style='color: #306998; font-weight: bold;'>📍 World</span>
            <span id='breadcrumb-country' style='display: none;'>
                <span style='color: #888;'> › </span>
                <span class='bc-link' style='color: #306998; cursor: pointer;'>Country</span>
            </span>
            <span id='breadcrumb-state' style='display: none;'>
                <span style='color: #888;'> › </span>
                <span class='bc-link' style='color: #306998; cursor: pointer;'>State</span>
            </span>
            </div>""",
    width=4800,
    height=70,
)

# =============================================================================
# Color bar legend - positioned with margin to avoid cutoff
# =============================================================================
color_bar = ColorBar(
    color_mapper=color_mapper,
    width=50,
    height=700,
    location=(0, 0),
    title="Sales\n($M)",
    title_text_font_size="26pt",
    title_text_font_style="bold",
    major_label_text_font_size="20pt",
    title_standoff=20,
    margin=30,
    padding=20,
)
p.add_layout(color_bar, "right")
p.min_border_right = 300  # Ensure space for color bar

# =============================================================================
# Hover tool with tooltips
# =============================================================================
hover = HoverTool(
    renderers=[country_patches, state_patches, city_patches],
    tooltips=[("Region", "@name"), ("Sales", "$@value{0}M")],
    mode="mouse",
)
p.add_tools(hover)

# =============================================================================
# Tap tool for drill-down interaction
# =============================================================================
tap_callback = CustomJS(
    args={
        "p": p,
        "country_patches": country_patches,
        "state_patches": state_patches,
        "city_patches": city_patches,
        "state_labels": state_labels,
        "city_labels": city_labels,
        "state_value_labels": state_value_labels,
        "city_value_labels": city_value_labels,
        "breadcrumb": breadcrumb_div,
    },
    code="""
    // Get the selected indices from the tapped renderer
    const countries_selected = country_patches.data_source.selected.indices;
    const states_selected = state_patches.data_source.selected.indices;
    const cities_selected = city_patches.data_source.selected.indices;

    if (countries_selected.length > 0 && country_patches.visible) {
        const idx = countries_selected[0];
        const name = country_patches.data_source.data['name'][idx];

        if (name === 'United States') {
            // Drill down to US states
            country_patches.visible = false;
            state_patches.visible = true;
            state_labels.visible = true;
            state_value_labels.visible = true;

            // Update view bounds to US
            p.x_range.start = -130;
            p.x_range.end = -65;
            p.y_range.start = 20;
            p.y_range.end = 55;

            // Update breadcrumb
            breadcrumb.text = `<div style='font-size: 24pt; font-family: sans-serif; padding: 15px 30px;
                              background: #f5f5f5; border-radius: 8px; display: inline-block;'>
                <span style='color: #306998; cursor: pointer;' onclick='window.drillUp("world")'>📍 World</span>
                <span style='color: #888;'> › </span>
                <span style='color: #306998; font-weight: bold;'>United States</span>
            </div>`;
        }
        country_patches.data_source.selected.indices = [];
    }

    if (states_selected.length > 0 && state_patches.visible) {
        const idx = states_selected[0];
        const name = state_patches.data_source.data['name'][idx];

        if (name === 'California') {
            // Drill down to California cities
            state_patches.visible = false;
            state_labels.visible = false;
            state_value_labels.visible = false;
            city_patches.visible = true;
            city_labels.visible = true;
            city_value_labels.visible = true;

            // Update view bounds to California
            p.x_range.start = -125;
            p.x_range.end = -114;
            p.y_range.start = 32;
            p.y_range.end = 42;

            // Update breadcrumb
            breadcrumb.text = `<div style='font-size: 24pt; font-family: sans-serif; padding: 15px 30px;
                              background: #f5f5f5; border-radius: 8px; display: inline-block;'>
                <span style='color: #306998; cursor: pointer;' onclick='window.drillUp("world")'>📍 World</span>
                <span style='color: #888;'> › </span>
                <span style='color: #306998; cursor: pointer;' onclick='window.drillUp("us")'>United States</span>
                <span style='color: #888;'> › </span>
                <span style='color: #306998; font-weight: bold;'>California</span>
            </div>`;
        }
        state_patches.data_source.selected.indices = [];
    }

    city_patches.data_source.selected.indices = [];
""",
)

tap_tool = TapTool(callback=tap_callback, renderers=[country_patches, state_patches, city_patches])
p.add_tools(tap_tool)

# =============================================================================
# Styling
# =============================================================================
p.xaxis.axis_label = "Longitude"
p.yaxis.axis_label = "Latitude"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.background_fill_color = "#f0f8ff"
p.border_fill_color = "#ffffff"
p.outline_line_color = "#306998"
p.outline_line_width = 2

# Instruction text
instruction_div = Div(
    text="""<div style='font-size: 22pt; font-family: sans-serif; color: #555;
                        text-align: center; padding: 10px;'>
            💡 <b>Click on a region to drill down</b> into its subdivisions.
            Currently showing: Countries → States (US) → Cities (California)
            </div>""",
    width=4800,
    height=60,
)

# =============================================================================
# Layout
# =============================================================================
layout = column(breadcrumb_div, p, instruction_div)

# =============================================================================
# Save output
# =============================================================================
export_png(layout, filename="plot.png")

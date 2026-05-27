""" anyplot.ai
linked-views-selection: Multiple Linked Views with Selection Sync
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-17
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.layouts import column, gridplot, row
from bokeh.models import Button, ColumnDataSource, CustomJS, Div
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

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - using iris-like multivariate data
np.random.seed(42)
n_points = 150

categories = ["Species A", "Species B", "Species C"]
category_list = []
x_data = []
y_data = []
value_data = []

for i, cat in enumerate(categories):
    n = 50
    category_list.extend([cat] * n)
    x_data.extend(np.random.normal(loc=4 + i * 2, scale=0.6, size=n))
    y_data.extend(np.random.normal(loc=2 + i * 1.5, scale=0.5, size=n))
    value_data.extend(np.random.normal(loc=10 + i * 5, scale=2, size=n))

df = pd.DataFrame({"x": x_data, "y": y_data, "category": category_list, "value": value_data})

# Create ColumnDataSource - the key to linked views in Bokeh
source = ColumnDataSource(
    data={"x": df["x"].values, "y": df["y"].values, "category": df["category"].values, "value": df["value"].values}
)

# Color mapping for categories using Okabe-Ito
color_palette = IMPRINT[:3]
color_mapper = factor_cmap("category", palette=color_palette, factors=categories)

# Create scatter plot (main selection view)
scatter = figure(
    width=2400,
    height=1350,
    title="Scatter Plot - Use Box Select or Lasso to Select Points",
    x_axis_label="Sepal Length (cm)",
    y_axis_label="Sepal Width (cm)",
    tools="pan,wheel_zoom,reset,box_select,lasso_select,tap",
)

scatter_renderer = scatter.scatter(
    "x",
    "y",
    source=source,
    size=15,
    color=color_mapper,
    alpha=0.8,
    selection_color=IMPRINT[1],
    selection_alpha=1.0,
    nonselection_alpha=0.15,
    nonselection_color=INK_SOFT,
)

# Style scatter plot
scatter.background_fill_color = PAGE_BG
scatter.border_fill_color = PAGE_BG
scatter.outline_line_color = INK_SOFT
scatter.title.text_font_size = "28pt"
scatter.title.text_color = INK
scatter.xaxis.axis_label_text_font_size = "22pt"
scatter.yaxis.axis_label_text_font_size = "22pt"
scatter.xaxis.axis_label_text_color = INK
scatter.yaxis.axis_label_text_color = INK
scatter.xaxis.major_label_text_font_size = "18pt"
scatter.yaxis.major_label_text_font_size = "18pt"
scatter.xaxis.major_label_text_color = INK_SOFT
scatter.yaxis.major_label_text_color = INK_SOFT
scatter.xaxis.axis_line_color = INK_SOFT
scatter.yaxis.axis_line_color = INK_SOFT
scatter.xgrid.grid_line_color = INK
scatter.xgrid.grid_line_alpha = 0.10
scatter.ygrid.grid_line_color = INK
scatter.ygrid.grid_line_alpha = 0.10

# Create histogram of values
hist_values, hist_edges = np.histogram(df["value"], bins=20)
hist_source = ColumnDataSource(data={"top": hist_values, "left": hist_edges[:-1], "right": hist_edges[1:]})

histogram = figure(
    width=2400,
    height=1350,
    title="Value Distribution - Updates with Selection",
    x_axis_label="Value (units)",
    y_axis_label="Count",
    tools="pan,wheel_zoom,reset",
)

histogram.quad(
    top="top",
    bottom=0,
    left="left",
    right="right",
    source=hist_source,
    fill_color=IMPRINT[0],
    line_color=PAGE_BG,
    alpha=0.8,
)

# Style histogram
histogram.background_fill_color = PAGE_BG
histogram.border_fill_color = PAGE_BG
histogram.outline_line_color = INK_SOFT
histogram.title.text_font_size = "28pt"
histogram.title.text_color = INK
histogram.xaxis.axis_label_text_font_size = "22pt"
histogram.yaxis.axis_label_text_font_size = "22pt"
histogram.xaxis.axis_label_text_color = INK
histogram.yaxis.axis_label_text_color = INK
histogram.xaxis.major_label_text_font_size = "18pt"
histogram.yaxis.major_label_text_font_size = "18pt"
histogram.xaxis.major_label_text_color = INK_SOFT
histogram.yaxis.major_label_text_color = INK_SOFT
histogram.xaxis.axis_line_color = INK_SOFT
histogram.yaxis.axis_line_color = INK_SOFT
histogram.xgrid.grid_line_color = INK
histogram.xgrid.grid_line_alpha = 0.10
histogram.ygrid.grid_line_color = INK
histogram.ygrid.grid_line_alpha = 0.10

# Create bar chart by category
category_counts = df["category"].value_counts()
bar_source = ColumnDataSource(
    data={"categories": categories, "counts": [category_counts.get(c, 0) for c in categories], "colors": color_palette}
)

bar_chart = figure(
    width=2400,
    height=1350,
    x_range=categories,
    title="Category Distribution - Updates with Selection",
    x_axis_label="Category",
    y_axis_label="Count",
    tools="pan,wheel_zoom,reset",
)

bar_chart.vbar(
    x="categories",
    top="counts",
    width=0.6,
    source=bar_source,
    color="colors",
    alpha=0.8,
    line_color=PAGE_BG,
    line_width=2,
)

# Style bar chart
bar_chart.background_fill_color = PAGE_BG
bar_chart.border_fill_color = PAGE_BG
bar_chart.outline_line_color = INK_SOFT
bar_chart.title.text_font_size = "28pt"
bar_chart.title.text_color = INK
bar_chart.xaxis.axis_label_text_font_size = "22pt"
bar_chart.yaxis.axis_label_text_font_size = "22pt"
bar_chart.xaxis.axis_label_text_color = INK
bar_chart.yaxis.axis_label_text_color = INK
bar_chart.xaxis.major_label_text_font_size = "18pt"
bar_chart.yaxis.major_label_text_font_size = "18pt"
bar_chart.xaxis.major_label_text_color = INK_SOFT
bar_chart.yaxis.major_label_text_color = INK_SOFT
bar_chart.xaxis.axis_line_color = INK_SOFT
bar_chart.yaxis.axis_line_color = INK_SOFT
bar_chart.xgrid.grid_line_color = None
bar_chart.ygrid.grid_line_color = INK
bar_chart.ygrid.grid_line_alpha = 0.10

# Create second scatter plot (value vs y)
scatter2 = figure(
    width=2400,
    height=1350,
    title="Value vs Sepal Width - Linked Selection",
    x_axis_label="Value (units)",
    y_axis_label="Sepal Width (cm)",
    tools="pan,wheel_zoom,reset,box_select,lasso_select,tap",
)

scatter2.scatter(
    "value",
    "y",
    source=source,
    size=15,
    color=color_mapper,
    alpha=0.8,
    selection_color=IMPRINT[1],
    selection_alpha=1.0,
    nonselection_alpha=0.15,
    nonselection_color=INK_SOFT,
)

# Style second scatter
scatter2.background_fill_color = PAGE_BG
scatter2.border_fill_color = PAGE_BG
scatter2.outline_line_color = INK_SOFT
scatter2.title.text_font_size = "28pt"
scatter2.title.text_color = INK
scatter2.xaxis.axis_label_text_font_size = "22pt"
scatter2.yaxis.axis_label_text_font_size = "22pt"
scatter2.xaxis.axis_label_text_color = INK
scatter2.yaxis.axis_label_text_color = INK
scatter2.xaxis.major_label_text_font_size = "18pt"
scatter2.yaxis.major_label_text_font_size = "18pt"
scatter2.xaxis.major_label_text_color = INK_SOFT
scatter2.yaxis.major_label_text_color = INK_SOFT
scatter2.xaxis.axis_line_color = INK_SOFT
scatter2.yaxis.axis_line_color = INK_SOFT
scatter2.xgrid.grid_line_color = INK
scatter2.xgrid.grid_line_alpha = 0.10
scatter2.ygrid.grid_line_color = INK
scatter2.ygrid.grid_line_alpha = 0.10

# JavaScript callback to update histogram and bar chart on selection
callback = CustomJS(
    args={"source": source, "hist_source": hist_source, "bar_source": bar_source},
    code="""
    const indices = source.selected.indices;
    const data = source.data;
    const hist_data = hist_source.data;
    const bar_data = bar_source.data;

    if (indices.length === 0) {
        // Reset histogram
        const values = data['value'];
        const min_val = Math.min(...values);
        const max_val = Math.max(...values);
        const n_bins = 20;
        const bin_width = (max_val - min_val) / n_bins;

        const counts = new Array(n_bins).fill(0);
        const left = [];
        const right = [];

        for (let i = 0; i < n_bins; i++) {
            left.push(min_val + i * bin_width);
            right.push(min_val + (i + 1) * bin_width);
        }

        for (let i = 0; i < values.length; i++) {
            const bin_idx = Math.min(Math.floor((values[i] - min_val) / bin_width), n_bins - 1);
            counts[bin_idx]++;
        }

        hist_data['top'] = counts;
        hist_data['left'] = left;
        hist_data['right'] = right;

        // Reset bar chart
        const categories = ['Species A', 'Species B', 'Species C'];
        const cat_counts = new Array(categories.length).fill(0);
        for (let i = 0; i < data['category'].length; i++) {
            const cat_idx = categories.indexOf(data['category'][i]);
            if (cat_idx >= 0) cat_counts[cat_idx]++;
        }
        bar_data['counts'] = cat_counts;
    } else {
        // Update histogram with selected values
        const selected_values = indices.map(i => data['value'][i]);
        const min_val = Math.min(...data['value']);
        const max_val = Math.max(...data['value']);
        const n_bins = 20;
        const bin_width = (max_val - min_val) / n_bins;

        const counts = new Array(n_bins).fill(0);
        const left = [];
        const right = [];

        for (let i = 0; i < n_bins; i++) {
            left.push(min_val + i * bin_width);
            right.push(min_val + (i + 1) * bin_width);
        }

        for (const val of selected_values) {
            const bin_idx = Math.min(Math.floor((val - min_val) / bin_width), n_bins - 1);
            counts[bin_idx]++;
        }

        hist_data['top'] = counts;
        hist_data['left'] = left;
        hist_data['right'] = right;

        // Update bar chart with selected categories
        const categories = ['Species A', 'Species B', 'Species C'];
        const cat_counts = new Array(categories.length).fill(0);
        for (const idx of indices) {
            const cat_idx = categories.indexOf(data['category'][idx]);
            if (cat_idx >= 0) cat_counts[cat_idx]++;
        }
        bar_data['counts'] = cat_counts;
    }

    hist_source.change.emit();
    bar_source.change.emit();
""",
)

source.selected.js_on_change("indices", callback)

# Clear Selection button
clear_button = Button(label="Clear Selection", button_type="warning", width=200, height=50)
clear_callback = CustomJS(
    args={
        "source": source,
        "hist_source": hist_source,
        "bar_source": bar_source,
        "df_value": df["value"].values.tolist(),
    },
    code="""
    source.selected.indices = [];

    // Reset histogram
    const values = df_value;
    const min_val = Math.min(...values);
    const max_val = Math.max(...values);
    const n_bins = 20;
    const bin_width = (max_val - min_val) / n_bins;

    const counts = new Array(n_bins).fill(0);
    const left = [];
    const right = [];

    for (let i = 0; i < n_bins; i++) {
        left.push(min_val + i * bin_width);
        right.push(min_val + (i + 1) * bin_width);
    }

    for (let i = 0; i < values.length; i++) {
        const bin_idx = Math.min(Math.floor((values[i] - min_val) / bin_width), n_bins - 1);
        counts[bin_idx]++;
    }

    hist_source.data['top'] = counts;
    hist_source.data['left'] = left;
    hist_source.data['right'] = right;
    hist_source.change.emit();

    // Reset bar chart
    const categories = ['Species A', 'Species B', 'Species C'];
    bar_source.data['counts'] = [50, 50, 50];
    bar_source.change.emit();

    source.change.emit();
""",
)
clear_button.js_on_click(clear_callback)

# Title as Div element
title_div = Div(
    text=f"<h1 style='font-size: 40pt; text-align: center; margin: 20px 0; "
    f"font-family: sans-serif; color: {INK};'>linked-views-selection · bokeh · anyplot.ai</h1>",
    width=4800,
)

# Button container centered
button_div = Div(text="", width=2200)
button_row = row(button_div, clear_button, width=4800)

# Create grid layout
grid = gridplot([[scatter, scatter2], [histogram, bar_chart]], merge_tools=True)

layout = column(title_div, button_row, grid)

# Save as HTML (interactive)
output_file(f"plot-{THEME}.html")
save(layout)

# Screenshot with Selenium
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

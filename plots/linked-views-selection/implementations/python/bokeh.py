""" pyplots.ai
linked-views-selection: Multiple Linked Views with Selection Sync
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-08
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, save
from bokeh.layouts import column, gridplot, row
from bokeh.models import Button, ColumnDataSource, CustomJS, Div
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.transform import factor_cmap


# Data - using iris-like multivariate data
np.random.seed(42)
n_points = 150

# Create three distinct clusters
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
    data={
        "x": df["x"].values,
        "y": df["y"].values,
        "category": df["category"].values,
        "value": df["value"].values,
        "original_alpha": [0.8] * len(df),
        "alpha": [0.8] * len(df),
    }
)

# Color mapping for categories
colors = ["#306998", "#FFD43B", "#7CB342"]  # Python Blue, Python Yellow, Green
color_mapper = factor_cmap("category", palette=colors, factors=categories)

# Create scatter plot (main selection view)
scatter = figure(
    width=2400,
    height=1300,
    title="Scatter Plot - Use Box Select or Lasso to Select Points",
    x_axis_label="Sepal Length (cm)",
    y_axis_label="Sepal Width (cm)",
    tools="pan,wheel_zoom,reset,box_select,lasso_select,tap",
)

# Create scatter glyphs per category for legend
scatter_renderers = []
for i, cat in enumerate(categories):
    indices = [j for j, c in enumerate(df["category"]) if c == cat]
    cat_source = ColumnDataSource(data={"x": df["x"].iloc[indices].values, "y": df["y"].iloc[indices].values})
    r = scatter.scatter("x", "y", source=cat_source, size=25, color=colors[i], alpha=0.8, legend_label=cat)
    scatter_renderers.append(r)

# Main scatter renderer with shared source for linked selection
scatter_renderer = scatter.scatter(
    "x",
    "y",
    source=source,
    size=25,
    color=color_mapper,
    alpha="alpha",
    selection_color="red",
    selection_alpha=1.0,
    nonselection_alpha=0.15,
    nonselection_color="gray",
)
scatter_renderer.visible = True

# Style scatter plot
scatter.title.text_font_size = "28pt"
scatter.xaxis.axis_label_text_font_size = "24pt"
scatter.yaxis.axis_label_text_font_size = "24pt"
scatter.xaxis.major_label_text_font_size = "20pt"
scatter.yaxis.major_label_text_font_size = "20pt"
scatter.grid.grid_line_alpha = 0.3
scatter.legend.label_text_font_size = "18pt"
scatter.legend.location = "top_left"
scatter.legend.click_policy = "hide"

# Create histogram of values
hist_values, hist_edges = np.histogram(df["value"], bins=20)

hist_source = ColumnDataSource(
    data={"top": hist_values, "left": hist_edges[:-1], "right": hist_edges[1:], "alpha": [0.8] * len(hist_values)}
)

histogram = figure(
    width=2400,
    height=1300,
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
    fill_color="#306998",
    line_color="white",
    alpha="alpha",
)

# Style histogram
histogram.title.text_font_size = "28pt"
histogram.xaxis.axis_label_text_font_size = "24pt"
histogram.yaxis.axis_label_text_font_size = "24pt"
histogram.xaxis.major_label_text_font_size = "20pt"
histogram.yaxis.major_label_text_font_size = "20pt"
histogram.grid.grid_line_alpha = 0.3

# Create bar chart by category
category_counts = df["category"].value_counts()
bar_source = ColumnDataSource(
    data={
        "categories": categories,
        "counts": [category_counts.get(c, 0) for c in categories],
        "colors": colors,
        "alpha": [0.8] * len(categories),
    }
)

bar_chart = figure(
    width=2400,
    height=1300,
    x_range=categories,
    title="Category Distribution - Updates with Selection",
    x_axis_label="Category",
    y_axis_label="Count",
    tools="pan,wheel_zoom,reset,tap",
)

bar_chart.vbar(
    x="categories",
    top="counts",
    width=0.7,
    source=bar_source,
    color="colors",
    alpha="alpha",
    line_color="white",
    line_width=2,
)

# Style bar chart
bar_chart.title.text_font_size = "28pt"
bar_chart.xaxis.axis_label_text_font_size = "24pt"
bar_chart.yaxis.axis_label_text_font_size = "24pt"
bar_chart.xaxis.major_label_text_font_size = "20pt"
bar_chart.yaxis.major_label_text_font_size = "20pt"
bar_chart.xgrid.grid_line_color = None
bar_chart.y_range.start = 0
bar_chart.grid.grid_line_alpha = 0.3

# Create a second scatter plot (value vs y) to show cross-view linking
scatter2 = figure(
    width=2400,
    height=1300,
    title="Value vs Sepal Width - Linked Selection",
    x_axis_label="Value (units)",
    y_axis_label="Sepal Width (cm)",
    tools="pan,wheel_zoom,reset,box_select,lasso_select,tap",
)

scatter2.scatter(
    "value",
    "y",
    source=source,  # Same source = automatic linking!
    size=25,
    color=color_mapper,
    alpha="alpha",
    selection_color="red",
    selection_alpha=1.0,
    nonselection_alpha=0.15,
    nonselection_color="gray",
)

# Style second scatter
scatter2.title.text_font_size = "28pt"
scatter2.xaxis.axis_label_text_font_size = "24pt"
scatter2.yaxis.axis_label_text_font_size = "24pt"
scatter2.xaxis.major_label_text_font_size = "20pt"
scatter2.yaxis.major_label_text_font_size = "20pt"
scatter2.grid.grid_line_alpha = 0.3

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
        hist_data['alpha'] = new Array(n_bins).fill(0.8);

        // Reset bar chart
        const categories = ['Species A', 'Species B', 'Species C'];
        const cat_counts = new Array(categories.length).fill(0);
        for (let i = 0; i < data['category'].length; i++) {
            const cat_idx = categories.indexOf(data['category'][i]);
            if (cat_idx >= 0) cat_counts[cat_idx]++;
        }
        bar_data['counts'] = cat_counts;
        bar_data['alpha'] = new Array(categories.length).fill(0.8);
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
        hist_data['alpha'] = new Array(n_bins).fill(0.8);

        // Update bar chart with selected categories
        const categories = ['Species A', 'Species B', 'Species C'];
        const cat_counts = new Array(categories.length).fill(0);
        for (const idx of indices) {
            const cat_idx = categories.indexOf(data['category'][idx]);
            if (cat_idx >= 0) cat_counts[cat_idx]++;
        }
        bar_data['counts'] = cat_counts;
        bar_data['alpha'] = new Array(categories.length).fill(0.8);
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

# Title as Div element (avoids missing renderers warning)
title_div = Div(
    text="<h1 style='font-size: 40pt; text-align: center; margin: 20px 0; "
    "font-family: sans-serif;'>linked-views-selection · bokeh · pyplots.ai</h1>",
    width=4800,
)

# Button container centered
button_div = Div(text="", width=2200)
button_row = row(button_div, clear_button, width=4800)

# Create grid layout
grid = gridplot([[scatter, scatter2], [histogram, bar_chart]], merge_tools=True)

layout = column(title_div, button_row, grid)

# Save as HTML for interactivity
save(layout, filename="plot.html", title="Linked Views Selection", resources=CDN)

# Export PNG for static preview
export_png(layout, filename="plot.png")

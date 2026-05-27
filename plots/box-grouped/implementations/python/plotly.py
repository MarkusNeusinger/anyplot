""" anyplot.ai
box-grouped: Grouped Box Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-08
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

# Data - Employee performance scores by department and experience level
np.random.seed(42)

categories = ["Sales", "Engineering", "Marketing", "Support"]
subcategories = ["Junior", "Mid-Level", "Senior"]

# Generate realistic performance data with varying distributions
data = {
    "Sales": {
        "Junior": np.random.normal(65, 12, 50),
        "Mid-Level": np.random.normal(75, 10, 50),
        "Senior": np.random.normal(85, 8, 50),
    },
    "Engineering": {
        "Junior": np.random.normal(60, 15, 50),
        "Mid-Level": np.random.normal(78, 9, 50),
        "Senior": np.random.normal(88, 6, 50),
    },
    "Marketing": {
        "Junior": np.random.normal(62, 14, 50),
        "Mid-Level": np.random.normal(72, 11, 50),
        "Senior": np.random.normal(82, 9, 50),
    },
    "Support": {
        "Junior": np.random.normal(58, 13, 50),
        "Mid-Level": np.random.normal(70, 10, 50),
        "Senior": np.random.normal(80, 7, 50),
    },
}

# Add some outliers for feature coverage
data["Sales"]["Junior"] = np.append(data["Sales"]["Junior"], [35, 95])
data["Engineering"]["Senior"] = np.append(data["Engineering"]["Senior"], [55, 95])
data["Marketing"]["Mid-Level"] = np.append(data["Marketing"]["Mid-Level"], [40, 98])

# Create figure
fig = go.Figure()

# Add box traces for each subcategory
for i, subcat in enumerate(subcategories):
    x_vals = []
    y_vals = []
    for cat in categories:
        values = data[cat][subcat]
        x_vals.extend([cat] * len(values))
        y_vals.extend(values)

    fig.add_trace(
        go.Box(
            x=x_vals,
            y=y_vals,
            name=subcat,
            marker_color=IMPRINT[i],
            boxmean=False,
            line={"width": 2},
            marker={"size": 8, "opacity": 0.7},
            boxpoints="outliers",
        )
    )

# Update layout for 4800x2700 resolution
fig.update_layout(
    title={
        "text": "box-grouped · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Department", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Performance Score (0-100)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    legend={
        "title": {"text": "Experience Level", "font": {"size": 20, "color": INK}},
        "font": {"size": 18, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "x": 1.02,
        "y": 1,
        "xanchor": "left",
        "yanchor": "top",
    },
    boxmode="group",
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 100, "r": 200, "t": 100, "b": 100},
)

# Save as PNG and HTML
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

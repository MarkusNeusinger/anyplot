""" pyplots.ai
heatmap-basic: Basic Heatmap
Library: plotly 6.5.2 | Python 3.14.3
Quality: 92/100 | Updated: 2026-02-15
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)

months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
categories = ["Electronics", "Clothing", "Food & Beverage", "Books", "Sports", "Home & Garden", "Beauty", "Toys"]

# Monthly sales growth (%) relative to annual average — diverging around zero
base = np.random.randn(len(categories), len(months)) * 8
# Seasonal patterns: summer lift for outdoor/leisure, holiday lift for gifts
for i, cat in enumerate(categories):
    if cat in ("Sports", "Toys", "Home & Garden"):
        base[i, 5:8] += 12  # Summer
    if cat in ("Electronics", "Toys", "Books", "Beauty"):
        base[i, 10:12] += 18  # Holiday season
    if cat == "Food & Beverage":
        base[i, 10:12] += 8  # Modest holiday lift
    if cat == "Clothing":
        base[i, 3:5] += 10  # Spring fashion
        base[i, 8:10] += 10  # Back-to-school
values = np.round(base, 1)

# Font family for publication-quality typography
font_family = "Palatino, Georgia, serif"

# Plot
fig = go.Figure(
    data=go.Heatmap(
        z=values,
        x=months,
        y=categories,
        colorscale="RdBu_r",
        zmid=0,
        colorbar={
            "title": {"text": "Sales Growth (%)", "font": {"size": 20, "family": font_family}},
            "tickfont": {"size": 16, "family": font_family},
            "ticksuffix": "%",
            "thickness": 20,
            "len": 0.75,
            "x": 1.005,
            "xpad": 4,
            "outlinewidth": 0,
        },
        text=values,
        texttemplate="%{text:+.1f}",
        textfont={"size": 15, "family": font_family},
        hovertemplate="<b>%{y}</b> · %{x}<br>Growth: %{z:+.1f}%<extra></extra>",
        xgap=2,
        ygap=2,
    )
)

# Layout — tighter margins maximise heatmap area; serif font elevates polish
fig.update_layout(
    title={
        "text": (
            "Monthly Sales Growth · heatmap-basic · plotly · pyplots.ai"
            "<br><sup style='color:#555; font-size:17px; letter-spacing:0.3px'>"
            "Retail categories show clear seasonal surges — "
            "summer outdoor/leisure peaks and Q4 holiday gift spikes"
            "</sup>"
        ),
        "font": {"size": 28, "family": font_family, "color": "#1a1a1a"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
        "yanchor": "top",
    },
    xaxis={
        "title": {"text": "Month", "font": {"size": 22, "family": font_family, "color": "#333"}},
        "tickfont": {"size": 18, "family": font_family, "color": "#444"},
        "side": "bottom",
    },
    yaxis={
        "title": {"text": "Product Category", "font": {"size": 22, "family": font_family, "color": "#333"}},
        "tickfont": {"size": 18, "family": font_family, "color": "#444"},
        "autorange": "reversed",
    },
    template="plotly_white",
    margin={"l": 140, "r": 60, "t": 120, "b": 65},
    width=1600,
    height=900,
    paper_bgcolor="#fafafa",
    plot_bgcolor="#fafafa",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")

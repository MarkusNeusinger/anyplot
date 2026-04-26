""" anyplot.ai
lollipop-basic: Basic Lollipop Chart
Library: plotly 6.7.0 | Python 3.14.4
Quality: 87/100 | Updated: 2026-04-26
"""

import os

import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1 — ALWAYS first series

# Data — Product sales by category (deterministic, sorted descending)
categories = [
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports",
    "Books",
    "Toys",
    "Beauty",
    "Automotive",
    "Food & Grocery",
    "Health",
]
values = [124820, 97340, 86715, 75260, 64480, 53905, 47620, 41370, 37815, 30945]

# Plot
fig = go.Figure()

# Stems — one segmented Scatter trace via None separators (single trace, fewer DOM nodes)
stem_x = []
stem_y = []
for cat, val in zip(categories, values, strict=True):
    stem_x.extend([cat, cat, None])
    stem_y.extend([0, val, None])

fig.add_trace(
    go.Scatter(x=stem_x, y=stem_y, mode="lines", line={"color": BRAND, "width": 3}, showlegend=False, hoverinfo="skip")
)

# Markers — circular dots at the top of each stem
fig.add_trace(
    go.Scatter(
        x=categories,
        y=values,
        mode="markers",
        marker={"color": BRAND, "size": 22, "line": {"color": PAGE_BG, "width": 2.5}, "symbol": "circle"},
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>Sales: $%{y:,.0f}<extra></extra>",
        cliponaxis=False,
    )
)

# Style
fig.update_layout(
    title={
        "text": "Product Sales by Category · lollipop-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.95,
    },
    xaxis={
        "title": {"text": "Product Category", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "tickangle": -35,
        "showgrid": False,
        "linecolor": INK_SOFT,
        "ticks": "outside",
        "tickcolor": INK_SOFT,
        "ticklen": 6,
    },
    yaxis={
        "title": {"text": "Sales ($)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "tickformat": "$,.0f",
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": INK_SOFT,
        "zerolinewidth": 1.5,
        "linecolor": INK_SOFT,
        "range": [0, max(values) * 1.1],
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK, "family": "Inter, system-ui, sans-serif"},
    margin={"l": 110, "r": 60, "t": 110, "b": 160},
    showlegend=False,
    hoverlabel={"bgcolor": ELEVATED_BG, "bordercolor": INK_SOFT, "font": {"color": INK, "size": 16}},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

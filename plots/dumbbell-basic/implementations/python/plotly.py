"""pyplots.ai
dumbbell-basic: Basic Dumbbell Chart
Library: plotly 6.5.0 | Python 3.13.11
"""

import os

import plotly.graph_objects as go


# Theme-adaptive chrome tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (theme-independent data colors)
BEFORE_COLOR = "#009E73"  # position 1 — first categorical series
AFTER_COLOR = "#D55E00"  # position 2 — second series

# Data — Employee satisfaction scores before and after policy changes.
# Deterministic, hand-picked values (no RNG): one department (Legal) shows a
# slight regression to demonstrate full data range including negative change.
categories = [
    "Engineering",
    "Sales",
    "Marketing",
    "Customer Support",
    "Finance",
    "Human Resources",
    "Operations",
    "Product",
    "Legal",
]
before = [62, 71, 58, 45, 68, 52, 64, 73, 70]
after = [78, 82, 75, 69, 74, 71, 79, 85, 67]

# Sort by difference (largest improvement at top, regression at bottom)
data = sorted(zip(categories, before, after, strict=True), key=lambda x: x[2] - x[1])
categories = [d[0] for d in data]
before = [d[1] for d in data]
after = [d[2] for d in data]

fig = go.Figure()

# Connecting lines (one per category)
for i, cat in enumerate(categories):
    fig.add_trace(
        go.Scatter(
            x=[before[i], after[i]],
            y=[cat, cat],
            mode="lines",
            line={"color": INK_SOFT, "width": 2},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# "Before" markers — Okabe-Ito green (brand)
fig.add_trace(
    go.Scatter(
        x=before,
        y=categories,
        mode="markers",
        marker={"size": 18, "color": BEFORE_COLOR, "line": {"color": PAGE_BG, "width": 2}},
        name="Before",
        hovertemplate="<b>%{y}</b><br>Before: %{x}/100<extra></extra>",
    )
)

# "After" markers — Okabe-Ito vermillion
fig.add_trace(
    go.Scatter(
        x=after,
        y=categories,
        mode="markers",
        marker={"size": 18, "color": AFTER_COLOR, "line": {"color": PAGE_BG, "width": 2}},
        name="After",
        hovertemplate="<b>%{y}</b><br>After: %{x}/100<extra></extra>",
    )
)

fig.update_layout(
    title={
        "text": "Employee Satisfaction · dumbbell-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Satisfaction Score (out of 100)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "range": [35, 95],
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Department", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "showgrid": True,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
        "font": {"size": 16, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 170, "r": 60, "t": 110, "b": 90},
)

fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

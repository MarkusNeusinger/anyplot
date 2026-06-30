"""anyplot.ai
dumbbell-basic: Basic Dumbbell Chart
Library: plotly | Python
"""

import os

import plotly.graph_objects as go


# Theme-adaptive chrome tokens (Imprint style guide)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette data colors (theme-independent)
BEFORE_COLOR = "#009E73"  # position 1 — first categorical series
AFTER_COLOR = "#C475FD"  # position 2 — second series
AMBER = "#DDCC77"  # semantic anchor — warning / regression flag

# Employee satisfaction scores before and after policy changes (deterministic)
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

# Sort ascending by delta (regression at top, largest gain at bottom)
data = sorted(zip(categories, before, after, strict=True), key=lambda x: x[2] - x[1])
categories = [d[0] for d in data]
before = [d[1] for d in data]
after = [d[2] for d in data]
deltas = [a - b for a, b in zip(after, before, strict=True)]

fig = go.Figure()

# Connecting lines — amber for regression, subtle ink-soft for improvement
for i in range(len(categories)):
    is_regression = deltas[i] < 0
    fig.add_trace(
        go.Scatter(
            x=[before[i], after[i]],
            y=[categories[i], categories[i]],
            mode="lines",
            line={"color": AMBER if is_regression else INK_SOFT, "width": 2.5 if is_regression else 1.5},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# "Before" markers — Imprint green (position 1)
fig.add_trace(
    go.Scatter(
        x=before,
        y=categories,
        mode="markers",
        marker={"size": 14, "color": BEFORE_COLOR, "line": {"color": PAGE_BG, "width": 2}},
        name="Before",
        hovertemplate="<b>%{y}</b><br>Before: %{x}/100<extra></extra>",
    )
)

# "After" markers — Imprint lavender (position 2)
fig.add_trace(
    go.Scatter(
        x=after,
        y=categories,
        mode="markers",
        marker={"size": 14, "color": AFTER_COLOR, "line": {"color": PAGE_BG, "width": 2}},
        name="After",
        hovertemplate="<b>%{y}</b><br>After: %{x}/100<extra></extra>",
    )
)

# Delta labels to the right of each dumbbell — amber for regression
annotations = []
for cat, b, a, delta in zip(categories, before, after, deltas, strict=True):
    sign = "+" if delta >= 0 else ""
    label_color = AMBER if delta < 0 else INK_SOFT
    annotations.append(
        {
            "x": max(b, a) + 1.5,
            "y": cat,
            "text": f"{sign}{delta} pts",
            "showarrow": False,
            "font": {"size": 11, "color": label_color},
            "xanchor": "left",
            "yanchor": "middle",
        }
    )

fig.update_layout(
    autosize=False,
    title={
        "text": "Employee Satisfaction · dumbbell-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Satisfaction Score (out of 100)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [35, 100],
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "showgrid": True,
    },
    yaxis={
        "title": {"text": "Department", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "showgrid": False,
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
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    annotations=annotations,
    margin={"l": 150, "r": 90, "t": 80, "b": 60},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

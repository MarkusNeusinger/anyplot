""" anyplot.ai
bar-grouped: Grouped Bar Chart
Library: plotly 6.9.0 | Python 3.13.14
Quality: 86/100 | Updated: 2026-08-05
"""

import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint categorical palette — device types are abstract groups, canonical order applies
COLORS = ["#009E73", "#C475FD", "#4467A3"]

# Data: monthly website sessions (thousands) by traffic source, split by device type
categories = ["Organic Search", "Direct", "Social Media", "Paid Search", "Referral"]
devices = {"Desktop": [420, 210, 96, 185, 132], "Mobile": [312, 168, 224, 148, 90], "Tablet": [64, 47, 58, 42, 31]}

# Create figure
fig = go.Figure()

for i, (device, values) in enumerate(devices.items()):
    fig.add_trace(
        go.Bar(
            name=device,
            x=categories,
            y=values,
            marker={"color": COLORS[i], "line": {"color": PAGE_BG, "width": 1.5}},
            text=values,
            textposition="outside",
            textfont={"size": 11, "color": INK},
            hovertemplate=(f"<b>{device}</b><br>Source: %{{x}}<br>Sessions: %{{y}}K<br><extra></extra>"),
        )
    )

# Callout: Social Media is the only source where mobile sessions outpace desktop
fig.add_annotation(
    x="Social Media",
    y=224,
    text="Social skews mobile-first —<br>2.3× desktop sessions",
    showarrow=True,
    arrowhead=2,
    arrowcolor=INK_SOFT,
    ax=70,
    ay=-55,
    font={"size": 11, "color": INK},
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=6,
)

# Layout
fig.update_layout(
    autosize=False,
    title={
        "text": "bar-grouped · python · plotly · anyplot.ai",
        "font": {"size": 19, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Traffic Source", "font": {"size": 15, "color": INK}},
        "tickfont": {"size": 12, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "mirror": False,
    },
    yaxis={
        "title": {"text": "Monthly Sessions (thousands)", "font": {"size": 15, "color": INK}},
        "tickfont": {"size": 12, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "mirror": False,
    },
    barmode="group",
    bargap=0.2,
    bargroupgap=0.1,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend={
        "font": {"size": 12, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
    },
    margin={"l": 90, "r": 40, "t": 110, "b": 70},
    hovermode="x unified",
)

# Save outputs
script_dir = os.path.dirname(os.path.abspath(__file__))
fig.write_image(os.path.join(script_dir, f"plot-{THEME}.png"), width=800, height=450, scale=4)
fig.write_html(os.path.join(script_dir, f"plot-{THEME}.html"), include_plotlyjs="cdn")

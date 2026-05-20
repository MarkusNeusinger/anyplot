""" anyplot.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: plotly 6.7.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-20
"""

import os
import sys


# Remove current directory from path to avoid importing local plotly.py
sys.path = [p for p in sys.path if p not in ("", ".", os.path.dirname(__file__))]

import plotly.graph_objects as go  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9"]

# Data: 2024 Retail Sales — time-based hierarchy (year → quarter → month)
# Level 1: Quarterly totals (values in $K)
quarter_names = ["Q1 (Jan–Mar)", "Q2 (Apr–Jun)", "Q3 (Jul–Sep)", "Q4 (Oct–Dec)"]
quarter_values = [1240, 1680, 2140, 2380]
quarter_labels = ["$1.24M", "$1.68M", "$2.14M", "$2.38M"]
quarter_colors = OKABE_ITO[:4]

# Level 2: Monthly breakdown for Q3 (peak summer / back-to-school)
q3_month_names = ["July", "August", "September"]
q3_month_values = [680, 750, 710]
q3_month_labels = ["$680K", "$750K", "$710K"]

# Level 2: Monthly breakdown for Q4 (holiday season)
q4_month_names = ["October", "November", "December"]
q4_month_values = [740, 940, 700]
q4_month_labels = ["$740K", "$940K", "$700K"]

month_colors = OKABE_ITO[:3]

# Shared bar trace kwargs (using dict literals to satisfy ruff C408)
bar_kwargs_annual = {
    "x": quarter_names,
    "y": quarter_values,
    "text": quarter_labels,
    "textposition": "outside",
    "textfont": {"size": 12, "color": INK},
    "marker": {"color": quarter_colors, "line": {"color": PAGE_BG, "width": 2}},
    "hovertemplate": "<b>%{x}</b><br>Revenue: %{text}<extra></extra>",
    "cliponaxis": False,
}

bar_kwargs_q3 = {
    "x": q3_month_names,
    "y": q3_month_values,
    "text": q3_month_labels,
    "textposition": "outside",
    "textfont": {"size": 12, "color": INK},
    "marker": {"color": month_colors, "line": {"color": PAGE_BG, "width": 2}},
    "hovertemplate": "<b>%{x}</b><br>Revenue: %{text}<extra></extra>",
    "cliponaxis": False,
}

bar_kwargs_q4 = {
    "x": q4_month_names,
    "y": q4_month_values,
    "text": q4_month_labels,
    "textposition": "outside",
    "textfont": {"size": 12, "color": INK},
    "marker": {"color": month_colors, "line": {"color": PAGE_BG, "width": 2}},
    "hovertemplate": "<b>%{x}</b><br>Revenue: %{text}<extra></extra>",
    "cliponaxis": False,
}

# Figure — root level (annual overview: all quarters)
fig = go.Figure(go.Bar(**bar_kwargs_annual))

# Animation frames for drill-level navigation
fig.frames = [
    go.Frame(
        name="annual",
        data=[go.Bar(**bar_kwargs_annual)],
        layout=go.Layout(
            title_text="2024 Retail Sales · bar-drilldown · python · plotly · anyplot.ai",
            xaxis={"title": {"text": "Quarter", "font": {"size": 12, "color": INK}}},
            yaxis={
                "title": {"text": "Revenue ($K)", "font": {"size": 12, "color": INK}},
                "range": [0, max(quarter_values) * 1.22],
            },
        ),
    ),
    go.Frame(
        name="q3",
        data=[go.Bar(**bar_kwargs_q3)],
        layout=go.Layout(
            title_text="Q3 Jul–Sep Detail · bar-drilldown · python · plotly · anyplot.ai",
            xaxis={"title": {"text": "Month  ·  Path: 2024 > Q3", "font": {"size": 12, "color": INK}}},
            yaxis={
                "title": {"text": "Revenue ($K)", "font": {"size": 12, "color": INK}},
                "range": [0, max(q3_month_values) * 1.22],
            },
        ),
    ),
    go.Frame(
        name="q4",
        data=[go.Bar(**bar_kwargs_q4)],
        layout=go.Layout(
            title_text="Q4 Oct–Dec Detail · bar-drilldown · python · plotly · anyplot.ai",
            xaxis={"title": {"text": "Month  ·  Path: 2024 > Q4", "font": {"size": 12, "color": INK}}},
            yaxis={
                "title": {"text": "Revenue ($K)", "font": {"size": 12, "color": INK}},
                "range": [0, max(q4_month_values) * 1.22],
            },
        ),
    ),
]

# Layout with theme-adaptive chrome
fig.update_layout(
    title={
        "text": "2024 Retail Sales · bar-drilldown · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Quarter", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "showgrid": False,
    },
    yaxis={
        "title": {"text": "Revenue ($K)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "tickformat": ",d",
        "range": [0, max(quarter_values) * 1.22],
        "showgrid": True,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    margin={"t": 80, "b": 110, "l": 80, "r": 40},
    annotations=[
        {
            "text": "Select a level from the dropdown to drill into monthly detail",
            "xref": "paper",
            "yref": "paper",
            "x": 0.5,
            "y": -0.2,
            "showarrow": False,
            "font": {"size": 10, "color": INK_SOFT},
            "xanchor": "center",
        }
    ],
    updatemenus=[
        {
            "type": "dropdown",
            "direction": "down",
            "x": 0.0,
            "y": 1.14,
            "xanchor": "left",
            "yanchor": "top",
            "showactive": True,
            "active": 0,
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "font": {"size": 11, "color": INK},
            "pad": {"r": 10, "t": 5},
            "buttons": [
                {
                    "label": "▶  2024 Annual — All Quarters",
                    "method": "animate",
                    "args": [
                        ["annual"],
                        {
                            "mode": "immediate",
                            "frame": {"duration": 400, "redraw": True},
                            "transition": {"duration": 250},
                        },
                    ],
                },
                {
                    "label": "▸  Q3 Jul–Sep — Monthly Detail",
                    "method": "animate",
                    "args": [
                        ["q3"],
                        {
                            "mode": "immediate",
                            "frame": {"duration": 400, "redraw": True},
                            "transition": {"duration": 250},
                        },
                    ],
                },
                {
                    "label": "▸  Q4 Oct–Dec — Monthly Detail",
                    "method": "animate",
                    "args": [
                        ["q4"],
                        {
                            "mode": "immediate",
                            "frame": {"duration": 400, "redraw": True},
                            "transition": {"duration": 250},
                        },
                    ],
                },
            ],
        }
    ],
)

# Save outputs (theme-suffixed)
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn", config={"displayModeBar": True, "displaylogo": False})

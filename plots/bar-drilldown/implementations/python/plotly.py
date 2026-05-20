""" anyplot.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: plotly 6.7.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-20
"""

import importlib
import os
import sys


sys.path = [p for p in sys.path if p not in ("", ".", os.path.dirname(__file__))]
go = importlib.import_module("plotly.graph_objects")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9"]

# Data: 2024 Retail Sales — year → quarter → month hierarchy
# Level 1: Quarterly totals (values in $K)
quarter_names = ["Q1 (Jan–Mar)", "Q2 (Apr–Jun)", "Q3 (Jul–Sep)", "Q4 (Oct–Dec)"]
quarter_values = [1240, 1680, 2140, 2380]
quarter_labels = ["$1.24M", "$1.68M", "$2.14M", "$2.38M"]
quarter_colors = OKABE_ITO[:4]

# Level 2: Monthly breakdowns per quarter
q1_month_names = ["January", "February", "March"]
q1_month_values = [390, 420, 430]
q1_month_labels = ["$390K", "$420K", "$430K"]

q2_month_names = ["April", "May", "June"]
q2_month_values = [520, 570, 590]
q2_month_labels = ["$520K", "$570K", "$590K"]

q3_month_names = ["July", "August", "September"]
q3_month_values = [680, 750, 710]
q3_month_labels = ["$680K", "$750K", "$710K"]

q4_month_names = ["October", "November", "December"]
q4_month_values = [740, 940, 700]
q4_month_labels = ["$740K", "$940K", "$700K"]

month_colors = OKABE_ITO[:3]

# Shared chrome for bar traces — per-level data/color overridden via merge
_bar_chrome = {
    "textposition": "outside",
    "textfont": {"size": 12, "color": INK},
    "hovertemplate": "<b>%{x}</b><br>Revenue: %{text}<extra></extra>",
    "cliponaxis": False,
}
_bar_edge = {"color": PAGE_BG, "width": 2}

# Q1–Q3 are muted (0.75) to draw the eye to Q4 as the holiday peak
bar_kwargs_annual = {
    **_bar_chrome,
    "x": quarter_names,
    "y": quarter_values,
    "text": quarter_labels,
    "marker": {"color": quarter_colors, "line": _bar_edge, "opacity": [0.75, 0.75, 0.75, 1.0]},
}
bar_kwargs_q1 = {
    **_bar_chrome,
    "x": q1_month_names,
    "y": q1_month_values,
    "text": q1_month_labels,
    "marker": {"color": month_colors, "line": _bar_edge},
}
bar_kwargs_q2 = {
    **_bar_chrome,
    "x": q2_month_names,
    "y": q2_month_values,
    "text": q2_month_labels,
    "marker": {"color": month_colors, "line": _bar_edge},
}
bar_kwargs_q3 = {
    **_bar_chrome,
    "x": q3_month_names,
    "y": q3_month_values,
    "text": q3_month_labels,
    "marker": {"color": month_colors, "line": _bar_edge},
}
bar_kwargs_q4 = {
    **_bar_chrome,
    "x": q4_month_names,
    "y": q4_month_values,
    "text": q4_month_labels,
    "marker": {"color": month_colors, "line": _bar_edge},
}

# Annotations shared across all views
_footer_ann = {
    "text": "Select a level from the dropdown to drill into monthly detail",
    "xref": "paper",
    "yref": "paper",
    "x": 0.5,
    "y": -0.18,
    "showarrow": False,
    "font": {"size": 10, "color": INK_SOFT},
    "xanchor": "center",
}

# Q4 holiday-season callout — annual view only
_peak_ann = {
    "text": "★ Holiday Peak",
    "x": "Q4 (Oct–Dec)",
    "xref": "x",
    "y": max(quarter_values) * 1.25,
    "yref": "y",
    "showarrow": False,
    "font": {"size": 9, "color": OKABE_ITO[3]},
    "xanchor": "center",
    "yanchor": "bottom",
}

# y-axis range for annual view — extra headroom for the peak callout
Q_RANGE = [0, max(quarter_values) * 1.38]

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
            yaxis={"title": {"text": "Revenue ($K)", "font": {"size": 12, "color": INK}}, "range": Q_RANGE},
            annotations=[_footer_ann, _peak_ann],
        ),
    ),
    go.Frame(
        name="q1",
        data=[go.Bar(**bar_kwargs_q1)],
        layout=go.Layout(
            title_text="Q1 Jan–Mar Detail · bar-drilldown · python · plotly · anyplot.ai",
            xaxis={"title": {"text": "Month  ·  Path: 2024 > Q1", "font": {"size": 12, "color": INK}}},
            yaxis={
                "title": {"text": "Revenue ($K)", "font": {"size": 12, "color": INK}},
                "range": [0, max(q1_month_values) * 1.3],
            },
            annotations=[_footer_ann],
        ),
    ),
    go.Frame(
        name="q2",
        data=[go.Bar(**bar_kwargs_q2)],
        layout=go.Layout(
            title_text="Q2 Apr–Jun Detail · bar-drilldown · python · plotly · anyplot.ai",
            xaxis={"title": {"text": "Month  ·  Path: 2024 > Q2", "font": {"size": 12, "color": INK}}},
            yaxis={
                "title": {"text": "Revenue ($K)", "font": {"size": 12, "color": INK}},
                "range": [0, max(q2_month_values) * 1.3],
            },
            annotations=[_footer_ann],
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
                "range": [0, max(q3_month_values) * 1.3],
            },
            annotations=[_footer_ann],
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
                "range": [0, max(q4_month_values) * 1.3],
            },
            annotations=[_footer_ann],
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
        "range": Q_RANGE,
        "showgrid": True,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    margin={"t": 80, "b": 80, "l": 80, "r": 40},
    annotations=[_footer_ann, _peak_ann],
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
                    "label": "▸  Q1 Jan–Mar — Monthly Detail",
                    "method": "animate",
                    "args": [
                        ["q1"],
                        {
                            "mode": "immediate",
                            "frame": {"duration": 400, "redraw": True},
                            "transition": {"duration": 250},
                        },
                    ],
                },
                {
                    "label": "▸  Q2 Apr–Jun — Monthly Detail",
                    "method": "animate",
                    "args": [
                        ["q2"],
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

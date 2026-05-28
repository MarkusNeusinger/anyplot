""" anyplot.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: plotly 6.7.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-23
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
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette — positions 1–4 for 4 quarters
PALETTE = ["#009E73", "#C475FD", "#AE3030", "#4467A3"]

# Data: 2024 Retail Sales — quarter → month two-level hierarchy
QUARTERS = [
    {"name": "Q1 (Jan–Mar)", "value": 1240, "label": "$1.24M", "key": "q1"},
    {"name": "Q2 (Apr–Jun)", "value": 1680, "label": "$1.68M", "key": "q2"},
    {"name": "Q3 (Jul–Sep)", "value": 2140, "label": "$2.14M", "key": "q3"},
    {"name": "Q4 (Oct–Dec)", "value": 2380, "label": "$2.38M", "key": "q4"},
]
MONTHLY = {
    "q1": {
        "names": ["January", "February", "March"],
        "values": [390, 420, 430],
        "labels": ["$390K", "$420K", "$430K"],
        "path": "2024 > Q1",
        "prefix": "Q1 Jan–Mar Detail",
    },
    "q2": {
        "names": ["April", "May", "June"],
        "values": [520, 570, 590],
        "labels": ["$520K", "$570K", "$590K"],
        "path": "2024 > Q2",
        "prefix": "Q2 Apr–Jun Detail",
    },
    "q3": {
        "names": ["July", "August", "September"],
        "values": [680, 750, 710],
        "labels": ["$680K", "$750K", "$710K"],
        "path": "2024 > Q3",
        "prefix": "Q3 Jul–Sep Detail",
    },
    "q4": {
        "names": ["October", "November", "December"],
        "values": [740, 940, 700],
        "labels": ["$740K", "$940K", "$700K"],
        "path": "2024 > Q4",
        "prefix": "Q4 Oct–Dec Detail",
    },
}

_edge = {"color": PAGE_BG, "width": 2}
_chrome = {
    "textposition": "outside",
    "textfont": {"size": 12, "color": INK},
    "hovertemplate": "<b>%{x}</b><br>Revenue: %{text}<extra></extra>",
    "cliponaxis": False,
}

# Annual trace — Q4 at full opacity (holiday peak focal point), Q1–Q3 muted
annual_trace = go.Bar(
    **_chrome,
    x=[q["name"] for q in QUARTERS],
    y=[q["value"] for q in QUARTERS],
    text=[q["label"] for q in QUARTERS],
    marker={"color": PALETTE, "line": _edge, "opacity": [0.7, 0.7, 0.7, 1.0]},
)

# Monthly traces — bars inherit parent quarter's palette color (cross-level color identity)
monthly_traces = [
    go.Bar(
        **_chrome,
        x=MONTHLY[q["key"]]["names"],
        y=MONTHLY[q["key"]]["values"],
        text=MONTHLY[q["key"]]["labels"],
        marker={"color": PALETTE[i], "line": _edge},
    )
    for i, q in enumerate(QUARTERS)
]

# Annotations
_footer = {
    "text": "Click a quarter bar to drill into monthly detail  ·  use the dropdown to navigate back",
    "xref": "paper",
    "yref": "paper",
    "x": 0.5,
    "y": -0.18,
    "showarrow": False,
    "font": {"size": 10, "color": INK_SOFT},
    "xanchor": "center",
}
Q_RANGE = [0, max(q["value"] for q in QUARTERS) * 1.38]
_peak = {
    "text": "★ Holiday Peak",
    "x": "Q4 (Oct–Dec)",
    "xref": "x",
    "y": max(q["value"] for q in QUARTERS) * 1.25,
    "yref": "y",
    "showarrow": False,
    "font": {"size": 10, "color": PALETTE[3]},
    "xanchor": "center",
}

# Frames — annual overview + one per quarter
ANNUAL_TITLE = "2024 Retail Sales · bar-drilldown · python · plotly · anyplot.ai"

annual_frame = go.Frame(
    name="annual",
    data=[annual_trace],
    layout=go.Layout(
        title_text=ANNUAL_TITLE,
        xaxis={"title": {"text": "Quarter", "font": {"size": 12, "color": INK}}},
        yaxis={"title": {"text": "Revenue ($K)", "font": {"size": 12, "color": INK}}, "range": Q_RANGE},
        annotations=[_footer, _peak],
    ),
)
quarterly_frames = [
    go.Frame(
        name=q["key"],
        data=[monthly_traces[i]],
        layout=go.Layout(
            title_text=(f"{MONTHLY[q['key']]['prefix']} · bar-drilldown · python · plotly · anyplot.ai"),
            xaxis={
                "title": {"text": f"Month  ·  Path: {MONTHLY[q['key']]['path']}", "font": {"size": 12, "color": INK}}
            },
            yaxis={
                "title": {"text": "Revenue ($K)", "font": {"size": 12, "color": INK}},
                "range": [0, max(MONTHLY[q["key"]]["values"]) * 1.3],
            },
            annotations=[_footer],
        ),
    )
    for i, q in enumerate(QUARTERS)
]

# Dropdown navigation buttons
dropdown_buttons = [
    {
        "label": "▶  2024 Annual — All Quarters",
        "method": "animate",
        "args": [
            ["annual"],
            {"mode": "immediate", "frame": {"duration": 400, "redraw": True}, "transition": {"duration": 250}},
        ],
    }
] + [
    {
        "label": f"▸  {q['name']} — Monthly Detail",
        "method": "animate",
        "args": [
            [q["key"]],
            {"mode": "immediate", "frame": {"duration": 400, "redraw": True}, "transition": {"duration": 250}},
        ],
    }
    for q in QUARTERS
]

# Figure
fig = go.Figure(annual_trace)
fig.frames = [annual_frame] + quarterly_frames

fig.update_layout(
    autosize=False,
    title={"text": ANNUAL_TITLE, "font": {"size": 16, "color": INK}, "x": 0.5, "xanchor": "center"},
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
        "zerolinecolor": INK_SOFT,
        "tickformat": ",d",
        "range": Q_RANGE,
        "showgrid": True,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    margin={"t": 80, "b": 80, "l": 80, "r": 40},
    annotations=[_footer, _peak],
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
            "buttons": dropdown_buttons,
        }
    ],
)

# Save PNG — 3200×1800 landscape
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)

# Click-on-bar JavaScript: clicking a quarter bar drills into it; clicking a month bar returns to annual
_click_js = (
    "var el = document.querySelectorAll('.js-plotly-plot')[0];"
    "var drillMap = {"
    "'Q1 (Jan–Mar)': 'q1',"
    "'Q2 (Apr–Jun)': 'q2',"
    "'Q3 (Jul–Sep)': 'q3',"
    "'Q4 (Oct–Dec)': 'q4'"
    "};"
    "el.on('plotly_click', function(data) {"
    "  var label = data.points[0].x;"
    "  var target = drillMap[label] !== undefined ? drillMap[label] : 'annual';"
    "  Plotly.animate(el, [target], {"
    "    mode: 'immediate',"
    "    frame: {duration: 400, redraw: true},"
    "    transition: {duration: 250}"
    "  });"
    "});"
)
fig.write_html(
    f"plot-{THEME}.html",
    include_plotlyjs="cdn",
    config={"displayModeBar": True, "displaylogo": False},
    post_script=_click_js,
)

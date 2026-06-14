""" anyplot.ai
bar-heart-rate-zones: Time in Heart Rate Zones Bar Chart
Library: plotly 6.8.0 | Python 3.13.13
Quality: 91/100 | Created: 2026-06-14
"""

import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Zone colors — Imprint palette, semantically mapped to fitness zone conventions:
# Z1 grey → theme-adaptive muted; Z2 blue → Imprint #3; Z3 green → Imprint #1 (brand);
# Z4 orange → Imprint #4 ochre; Z5 red → Imprint #5 matte red
ZONE_COLORS = [INK_MUTED, "#4467A3", "#009E73", "#BD8233", "#AE3030"]

# Data — 60-min tempo run
zones = ["Z1", "Z2", "Z3", "Z4", "Z5"]
zone_names = ["Recovery", "Endurance", "Aerobic", "Threshold", "Maximum"]
minutes = [8, 22, 15, 12, 3]
hr_ranges = ["< 115 bpm", "115–133 bpm", "133–152 bpm", "152–171 bpm", "> 171 bpm"]

title = "60-min Tempo Run · bar-heart-rate-zones · python · plotly · anyplot.ai"
title_size = max(11, round(16 * 67 / len(title)))

tick_labels = [f"<b>{z}</b> {name}<br>{hr}" for z, name, hr in zip(zones, zone_names, hr_ranges, strict=False)]

# Plot
fig = go.Figure(
    go.Bar(
        x=zones,
        y=minutes,
        marker_color=ZONE_COLORS,
        marker_line={"width": 1, "color": INK_SOFT},
        text=[f"{m} min" for m in minutes],
        textposition="outside",
        textfont={"size": 14, "color": INK},
        constraintext="none",
        hovertemplate="<b>%{x}</b><br>Time in zone: %{y} min<extra></extra>",
    )
)

fig.add_hline(
    y=12,
    line_color=INK_MUTED,
    line_dash="dot",
    line_width=2,
    annotation_text="12 min / zone avg",
    annotation_font={"size": 10, "color": INK_MUTED},
    annotation_position="top right",
)

fig.update_layout(
    autosize=False,
    bargap=0.4,
    margin={"l": 80, "r": 40, "t": 80, "b": 65},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title={"text": title, "font": {"size": title_size, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "tickmode": "array",
        "tickvals": zones,
        "ticktext": tick_labels,
        "tickfont": {"size": 11, "color": INK_SOFT},
        "showline": False,
        "showgrid": False,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Time (min)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "showline": False,
        "zeroline": False,
        "range": [0, max(minutes) * 1.4],
    },
    showlegend=False,
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

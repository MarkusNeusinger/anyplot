"""anyplot.ai
gauge-activity-rings: Activity Rings Progress Chart
Library: plotly 6.8.0 | Python 3.13.13
Quality: 89/100 | Created: 2026-06-14
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — daily fitness summary (outer ring = primary metric)
metrics = [
    {"name": "Move", "value": 420, "goal": 600, "unit": "kcal"},
    {"name": "Exercise", "value": 25, "goal": 30, "unit": "min"},
    {"name": "Stand", "value": 9, "goal": 12, "unit": "hr"},
]
ring_colors = IMPRINT_PALETTE[:3]  # green, lavender, blue (outer → inner)

# Ring geometry — outer to inner
radii = [0.83, 0.58, 0.33]
line_width = 30  # px on the 600×600 logical canvas (→ 120 px in 2400×2400 output)
TRACK_ALPHA = 0.14 if THEME == "light" else 0.22  # higher in dark mode so track reads on near-black bg


def arc_xy(radius, fraction):
    fraction = min(fraction, 1.0)
    n = max(400, int(600 / radius))  # more points for inner (smaller) rings to stay smooth
    angles = np.linspace(90, 90 - fraction * 360, n)
    return (radius * np.cos(np.radians(angles))).tolist(), (radius * np.sin(np.radians(angles))).tolist()


def circle_xy(radius):
    n = max(400, int(600 / radius))
    angles = np.linspace(0, 360, n + 1)
    return (radius * np.cos(np.radians(angles))).tolist(), (radius * np.sin(np.radians(angles))).tolist()


def hex_to_rgba(h, alpha):
    r, g, b = int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)
    return f"rgba({r},{g},{b},{alpha})"


# Title — 51 chars, below 67-char baseline → no shrink needed
title = "gauge-activity-rings · python · plotly · anyplot.ai"
n_chars = len(title)
title_size = max(11, round(16 * (67 / n_chars if n_chars > 67 else 1.0)))

# Figure
fig = go.Figure()

for metric, radius, color in zip(metrics, radii, ring_colors, strict=False):
    fraction = metric["value"] / metric["goal"]
    track_color = hex_to_rgba(color, TRACK_ALPHA)

    # Background track (full circle, faint)
    cx, cy = circle_xy(radius)
    fig.add_trace(
        go.Scatter(
            x=cx,
            y=cy,
            mode="lines",
            line={"color": track_color, "width": line_width},
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Progress arc (clockwise from 12 o'clock)
    ax, ay = arc_xy(radius, fraction)
    pct = fraction * 100
    legend_label = f"{metric['name']}  {metric['value']}/{metric['goal']} {metric['unit']}"
    fig.add_trace(
        go.Scatter(
            x=ax,
            y=ay,
            mode="lines",
            line={"color": color, "width": line_width},
            name=legend_label,
            hovertemplate=(
                f"<b>{metric['name']}</b><br>"
                f"{metric['value']} / {metric['goal']} {metric['unit']}<br>"
                f"{pct:.0f}% complete<extra></extra>"
            ),
        )
    )

    # Rounded end caps — markers matching line width at arc endpoints
    s_x = radius * np.cos(np.radians(90))
    s_y = radius * np.sin(np.radians(90))
    end_angle = 90 - fraction * 360
    e_x = radius * np.cos(np.radians(end_angle))
    e_y = radius * np.sin(np.radians(end_angle))

    fig.add_trace(
        go.Scatter(
            x=[s_x, e_x],
            y=[s_y, e_y],
            mode="markers",
            marker={"color": color, "size": line_width, "line": {"width": 0}},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Center annotation — average completion across all three rings
avg_pct = np.mean([m["value"] / m["goal"] for m in metrics]) * 100
fig.add_annotation(
    x=0, y=0.09, text=f"<b>{avg_pct:.0f}%</b>", font={"size": 28, "color": INK}, showarrow=False, xanchor="center"
)
fig.add_annotation(
    x=0, y=-0.10, text="avg. complete", font={"size": 11, "color": INK_MUTED}, showarrow=False, xanchor="center"
)

# Layout — square canvas (2400×2400 via width=600 height=600 scale=4)
fig.update_layout(
    title={
        "text": title,
        "font": {"size": title_size, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.98,
        "yanchor": "top",
    },
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    showlegend=True,
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"color": INK_SOFT, "size": 11},
        "orientation": "h",
        "x": 0.5,
        "xanchor": "center",
        "y": -0.04,
        "yanchor": "top",
        "traceorder": "normal",
        "itemsizing": "constant",
    },
    margin={"l": 75, "r": 75, "t": 70, "b": 95},
    xaxis={
        "range": [-1.08, 1.08],
        "showgrid": False,
        "showticklabels": False,
        "zeroline": False,
        "showline": False,
        "scaleanchor": "y",
        "scaleratio": 1,
    },
    yaxis={"range": [-1.08, 1.08], "showgrid": False, "showticklabels": False, "zeroline": False, "showline": False},
)

# Save — square: width=600, height=600, scale=4 → 2400×2400 px
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

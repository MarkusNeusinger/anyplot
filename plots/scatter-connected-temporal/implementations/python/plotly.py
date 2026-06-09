"""anyplot.ai
scatter-connected-temporal: Connected Scatter Plot with Temporal Path
Library: plotly 6.6.0 | Python 3.14.3
Quality: 91/100 | Updated: 2026-06-09
"""

import os

import numpy as np
import plotly.colors as pc
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint sequential colormap — green (#009E73) → blue (#4467A3)
imprint_seq = [[0.0, "#009E73"], [1.0, "#4467A3"]]

# Data - US Phillips Curve: Unemployment vs Inflation (1990-2023)
years = np.arange(1990, 2024)
n = len(years)

unemployment = np.array(
    [
        5.6,
        6.8,
        7.5,
        6.9,
        6.1,
        5.6,
        5.4,
        4.9,
        4.5,
        4.2,  # 1990s recovery
        4.0,
        4.7,
        5.8,
        6.0,
        5.5,
        5.1,
        4.6,
        4.6,
        5.8,
        9.3,  # 2000s + recession
        9.6,
        8.9,
        8.1,
        7.4,
        6.2,
        5.3,
        4.9,
        4.4,
        3.9,
        3.7,  # 2010s recovery
        8.1,
        5.4,
        3.6,
        3.6,  # 2020s pandemic
    ]
)

inflation = np.array(
    [
        5.4,
        4.2,
        3.0,
        3.0,
        2.6,
        2.8,
        3.0,
        2.3,
        1.6,
        2.2,  # 1990s
        3.4,
        2.8,
        1.6,
        2.3,
        2.7,
        3.4,
        3.2,
        2.8,
        3.8,
        -0.4,  # 2000s
        1.6,
        3.2,
        2.1,
        1.5,
        1.6,
        0.1,
        1.3,
        2.1,
        2.4,
        1.8,  # 2010s
        1.2,
        4.7,
        8.0,
        4.1,  # 2020s
    ]
)

t_norm = np.linspace(0, 1, n)

fig = go.Figure()

# Line segments colored by Imprint sequential gradient
seg_colors = pc.sample_colorscale(imprint_seq, [t_norm[i] for i in range(n - 1)])

for i in range(n - 1):
    r, g, b = pc.unlabel_rgb(seg_colors[i])
    fig.add_trace(
        go.Scatter(
            x=unemployment[i : i + 2],
            y=inflation[i : i + 2],
            mode="lines",
            line={"color": f"rgba({r}, {g}, {b}, 0.6)", "width": 3.5},
            hoverinfo="skip",
            showlegend=False,
        )
    )

# Data points with Imprint sequential gradient and colorbar
fig.add_trace(
    go.Scatter(
        x=unemployment,
        y=inflation,
        mode="markers",
        marker={
            "size": 14,
            "color": t_norm,
            "colorscale": imprint_seq,
            "line": {"color": PAGE_BG, "width": 2},
            "colorbar": {
                "title": {"text": "Year", "font": {"size": 12, "color": INK}},
                "tickvals": [0, 0.2, 0.4, 0.6, 0.8, 1],
                "ticktext": ["1990", "1997", "2003", "2010", "2017", "2023"],
                "tickfont": {"size": 10, "color": INK_SOFT},
                "len": 0.75,
                "thickness": 18,
                "outlinewidth": 0,
                "x": 1.02,
                "bgcolor": PAGE_BG,
            },
        },
        customdata=np.column_stack([years, unemployment, inflation]),
        hovertemplate=(
            "<b>%{customdata[0]:.0f}</b><br>"
            "Unemployment: %{customdata[1]:.1f}%<br>"
            "Inflation: %{customdata[2]:.1f}%"
            "<extra></extra>"
        ),
        showlegend=False,
    )
)

# Year annotations at key time points
key_points = {
    0: ("1990", 45, -35),
    9: ("1999", -50, -40),
    19: ("2009", 50, 30),
    30: ("2020", -55, 35),
    32: ("2022", -55, -35),
    33: ("2023", 50, -30),
}

for idx, (label, ax_off, ay_off) in key_points.items():
    fig.add_annotation(
        x=unemployment[idx],
        y=inflation[idx],
        text=f"<b>{label}</b>",
        showarrow=True,
        arrowhead=0,
        arrowcolor=INK_MUTED,
        arrowwidth=1.5,
        ax=ax_off,
        ay=ay_off,
        font={"size": 11, "color": INK},
        bgcolor=ELEVATED_BG,
        borderpad=4,
    )

# Directional arrows indicating temporal flow
for start_idx, end_idx in [(10, 13), (27, 30)]:
    fig.add_annotation(
        x=unemployment[end_idx],
        y=inflation[end_idx],
        ax=unemployment[start_idx],
        ay=inflation[start_idx],
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=3,
        arrowsize=2,
        arrowwidth=2.5,
        arrowcolor=INK_SOFT,
        opacity=0.6,
    )

# Decade labels for context
for x_pos, y_pos, decade in [(6.8, 5.0, "1990s"), (7.8, -0.1, "2000s"), (4.0, 0.3, "2010s"), (5.8, 7.5, "2020s")]:
    fig.add_annotation(
        x=x_pos, y=y_pos, text=f"<i>{decade}</i>", showarrow=False, font={"size": 12, "color": INK_MUTED}
    )

# Layout
title_text = "scatter-connected-temporal · python · plotly · anyplot.ai"
title_n = len(title_text)
title_size = max(round(16 * (67 / title_n if title_n > 67 else 1.0)), 11)

fig.update_layout(
    autosize=False,
    title={"text": title_text, "font": {"size": title_size, "color": INK}, "x": 0.5, "y": 0.97},
    xaxis={
        "title": {"text": "Unemployment Rate (%)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "griddash": "dot",
        "zeroline": False,
        "showline": False,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Inflation Rate (%)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "griddash": "dot",
        "zeroline": False,
        "showline": False,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    template="plotly_white",
    margin={"l": 80, "r": 100, "t": 80, "b": 60},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

""" anyplot.ai
lollipop-basic: Basic Lollipop Chart
Library: plotly 6.8.0 | Python 3.13.14
Quality: 87/100 | Updated: 2026-07-01
"""

import os

import plotly.graph_objects as go


# Theme tokens — Imprint palette / default-style-guide.md "Theme-adaptive Chrome"
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"  # Imprint palette position 1 — featured / top-performer series

# Data — global tech gadget market revenue, 2025 estimates (USD billions), sorted descending
gadgets = [
    "Smartphones",
    "Laptops",
    "Smart TVs",
    "Tablets",
    "Gaming Consoles",
    "Smartwatches",
    "Wireless Earbuds",
    "Smart Speakers",
    "E-readers",
    "Smart Home Hubs",
]
revenue = [485, 145, 95, 80, 70, 52, 38, 18, 8, 6]

# Colour mapping: top performer gets BRAND; the rest use INK_MUTED ("other/rest" semantic anchor)
marker_colors = [BRAND if i == 0 else INK_MUTED for i in range(len(gadgets))]

fig = go.Figure()

# Stem for top performer (Smartphones) — BRAND colour, slightly thicker
fig.add_trace(
    go.Scatter(
        x=[gadgets[0], gadgets[0], None],
        y=[0, revenue[0], None],
        mode="lines",
        line={"color": BRAND, "width": 2.5},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Stems for the remaining categories — muted, single None-separated trace
rest_x: list = []
rest_y: list = []
for gadget, val in zip(gadgets[1:], revenue[1:], strict=True):
    rest_x.extend([gadget, gadget, None])
    rest_y.extend([0, val, None])
fig.add_trace(
    go.Scatter(
        x=rest_x, y=rest_y, mode="lines", line={"color": INK_MUTED, "width": 2}, showlegend=False, hoverinfo="skip"
    )
)

# Markers — single trace with per-point colour array
fig.add_trace(
    go.Scatter(
        x=gadgets,
        y=revenue,
        mode="markers",
        marker={"color": marker_colors, "size": 12, "line": {"color": PAGE_BG, "width": 2}, "symbol": "circle"},
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>Revenue: $%{y}B<extra></extra>",
        cliponaxis=False,
    )
)

# Callout annotation on the top performer for data storytelling
fig.add_annotation(
    x=gadgets[0],
    y=revenue[0],
    text=f"<b>${revenue[0]}B</b><br>Market leader",
    showarrow=True,
    arrowhead=2,
    arrowcolor=BRAND,
    arrowwidth=1.5,
    ax=55,
    ay=-38,
    font={"size": 10, "color": BRAND},
    bgcolor=ELEVATED_BG,
    bordercolor=BRAND,
    borderwidth=1,
    borderpad=4,
    align="left",
)

# Title length ≈ 72 chars → fontsize = round(16 × 67 / 72) = 15
fig.update_layout(
    autosize=False,
    title={
        "text": "Tech Gadget Market Revenue (2025) · lollipop-basic · plotly · anyplot.ai",
        "font": {"size": 15, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
        "yanchor": "top",
    },
    xaxis={
        "title": {"text": "Gadget Category", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickangle": -35,
        "showgrid": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "mirror": False,
        "ticks": "outside",
        "tickcolor": INK_SOFT,
        "ticklen": 4,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Revenue (USD Billions)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickprefix": "$",
        "ticksuffix": "B",
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": INK_SOFT,
        "zerolinewidth": 1,
        "showline": True,
        "linecolor": INK_SOFT,
        "mirror": False,
        "range": [0, max(revenue) * 1.15],
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK, "family": "Inter, system-ui, sans-serif"},
    margin={"l": 85, "r": 50, "t": 80, "b": 110},
    showlegend=False,
    hoverlabel={"bgcolor": ELEVATED_BG, "bordercolor": INK_SOFT, "font": {"color": INK, "size": 12}},
)

# Save — canvas hard rule: width=800, height=450, scale=4 → 3200×1800 px (landscape)
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

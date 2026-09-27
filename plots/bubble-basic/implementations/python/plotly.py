""" anyplot.ai
bubble-basic: Basic Bubble Chart
Library: plotly 7.1.0 | Python 3.13.15
Quality: 87/100 | Updated: 2026-09-27
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Continuous colorscale — imprint_seq (brand green → blue, single-polarity)
imprint_seq = [[0.0, "#009E73"], [1.0, "#4467A3"]]

# Data — Tech companies: R&D investment vs. product-market-fit score
np.random.seed(42)
n = 62
rd_pct = np.random.uniform(4, 42, n)  # R&D spend as % of revenue
pmf = np.clip(rd_pct * 1.3 + np.random.normal(0, 17, n) + 18, 8, 98)
revenue_m = np.clip(np.abs(np.random.normal(750, 380, n)), 40, 2200)

# Anchor key data points for visual storytelling
rd_pct[0], pmf[0], revenue_m[0] = 39, 96, 2100  # R&D powerhouse
rd_pct[1], pmf[1], revenue_m[1] = 36, 91, 1800
rd_pct[2], pmf[2], revenue_m[2] = 33, 87, 1650
rd_pct[5], pmf[5], revenue_m[5] = 7, 24, 180  # underinvestors
rd_pct[6], pmf[6], revenue_m[6] = 5, 18, 120
rd_pct[10], pmf[10], revenue_m[10] = 22, 92, 920  # efficient innovator

# Bubble sizing via sizeref (Plotly's idiomatic area-based scaling).
# Max on-screen diameter trimmed to 34 (from 37) and sizemin lowered to 7 so
# the dense low-R&D/low-PMF cluster overlaps less while the lowest-revenue
# bubbles stay clearly visible.
sizeref = 2.0 * float(revenue_m.max()) / (34.0**2)
cmin, cmax = float(revenue_m.min()), float(revenue_m.max())

# Legend swatch colors tinted along imprint_seq (green->blue) so each swatch
# matches what a real data bubble of that revenue would render.
imprint_seq_rgb = (np.array([0x00, 0x9E, 0x73]), np.array([0x44, 0x67, 0xA3]))


title = "R&D Investment vs. Product-Market Fit · bubble-basic · python · plotly · anyplot.ai"
title_size = max(11, round(16 * 67 / len(title))) if len(title) > 67 else 16

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=rd_pct,
        y=pmf,
        mode="markers",
        customdata=revenue_m,
        marker={
            "size": revenue_m,
            "sizemode": "area",
            "sizeref": sizeref,
            "sizemin": 7,
            "color": revenue_m,
            "cmin": cmin,
            "cmax": cmax,
            "colorscale": imprint_seq,
            "showscale": True,
            "colorbar": {
                "title": {"text": "Revenue", "font": {"size": 9, "color": INK}},
                "ticksuffix": "M",
                "thickness": 14,
                "len": 0.55,
                "x": 1.02,
                "xanchor": "left",
                "tickfont": {"size": 8, "color": INK_SOFT},
                "outlinewidth": 0.5,
                "outlinecolor": INK_SOFT,
            },
            "opacity": 0.5,
            "line": {"width": 1.5, "color": PAGE_BG},
        },
        hovertemplate=(
            "<b>R&D Spend:</b> %{x:.1f}%<br>"
            "<b>PMF Score:</b> %{y:.0f}<br>"
            "<b>Revenue:</b> $%{customdata:.0f}M<extra></extra>"
        ),
        showlegend=False,
    )
)

# Size legend — three reference bubbles (anchored near the data's min/mid/max
# revenue), tinted along imprint_seq so the swatch color matches what a real
# data bubble of that revenue would render
for size_label in [100, 600, 2000]:
    t = max(0.0, min(1.0, (size_label - cmin) / (cmax - cmin)))
    r, g, b = (imprint_seq_rgb[0] + (imprint_seq_rgb[1] - imprint_seq_rgb[0]) * t).round().astype(int)
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={
                "size": size_label,
                "sizemode": "area",
                "sizeref": sizeref,
                "sizemin": 7,
                "color": f"#{r:02X}{g:02X}{b:02X}",
                "opacity": 0.5,
                "line": {"width": 1.5, "color": PAGE_BG},
            },
            name=f"${size_label}M",
            showlegend=True,
        )
    )

fig.update_layout(
    autosize=False,
    title={"text": title, "font": {"size": title_size, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "R&D Spend (% of Revenue)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "ticks": "",
    },
    yaxis={
        "title": {"text": "Product-Market-Fit Score", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zeroline": False,
        "ticks": "",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK, "family": "Lato, 'DejaVu Sans', sans-serif"},
    legend={
        "title": {"text": "Revenue (size)", "font": {"size": 10, "color": INK}},
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 0.5,
        "x": 0.02,
        "y": 0.98,
        "xanchor": "left",
        "yanchor": "top",
    },
    margin={"l": 80, "r": 110, "t": 80, "b": 60},
    # Subtle zone highlight around the R&D-powerhouse cluster (indices 0-2:
    # high R&D spend, high PMF, high revenue) — a third layer of visual
    # hierarchy beyond the two point-specific callouts below.
    shapes=[
        {
            "type": "rect",
            "x0": 29,
            "x1": 41,
            "y0": 83,
            "y1": 99,
            "line": {"color": INK_SOFT, "width": 1, "dash": "dot"},
            "fillcolor": GRID,
            "layer": "below",
        }
    ],
    annotations=[
        {
            "x": 35,
            "y": 99,
            "yshift": 6,
            "text": "R&D powerhouses",
            "font": {"size": 9, "color": INK_SOFT},
            "showarrow": False,
            "xanchor": "center",
            "yanchor": "bottom",
        },
        {
            "x": rd_pct[10],
            "y": pmf[10],
            "text": "Efficient innovator<br>(low R&D, high PMF)",
            "font": {"size": 10, "color": INK},
            "showarrow": True,
            "arrowhead": 2,
            "arrowcolor": INK_SOFT,
            "ax": 40,
            "ay": -40,
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 0.5,
            "borderpad": 4,
        },
        {
            "x": rd_pct[6],
            "y": pmf[6],
            "text": "Underinvested laggard<br>(low R&D, low PMF)",
            "font": {"size": 10, "color": INK},
            "showarrow": True,
            "arrowhead": 2,
            "arrowcolor": INK_SOFT,
            "ax": -50,
            "ay": 40,
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 0.5,
            "borderpad": 4,
        },
    ],
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

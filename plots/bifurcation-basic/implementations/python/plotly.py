"""anyplot.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: plotly | Python 3.13
Quality: pending | Created: 2026-06-17
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"  # Imprint palette position 1 — ALWAYS first series

# Data: Logistic map x(n+1) = r * x(n) * (1 - x(n))
r_values = np.linspace(2.5, 4.0, 2000)
transient = 200
iterations = 100

r_all = []
x_all = []

for r in r_values:
    x = 0.5
    for _ in range(transient):
        x = r * x * (1.0 - x)
    for _ in range(iterations):
        x = r * x * (1.0 - x)
        r_all.append(r)
        x_all.append(x)

r_all = np.array(r_all)
x_all = np.array(x_all)

# Plot — Scattergl renders the ~200K density points performantly via WebGL
fig = go.Figure()

# Subtle emphasis on the chaotic regime (r > onset of chaos)
chaos_onset = 3.5699
fig.add_vrect(x0=chaos_onset, x1=4.05, fillcolor=INK_MUTED, opacity=0.06, line_width=0, layer="below")

fig.add_trace(
    go.Scattergl(
        x=r_all,
        y=x_all,
        mode="markers",
        marker={"size": 2, "color": BRAND, "opacity": 0.13},
        showlegend=False,
        hovertemplate="r = %{x:.4f}<br>x = %{y:.4f}<extra></extra>",
    )
)

# Key bifurcation points (period-doubling cascade → chaos). The spec explicitly
# asks for these labels — reference lines use the neutral/structural ink token.
# The last three are tightly packed in r, so labels are staggered across two
# rows (alternating y) and anchored outward to avoid overlap.
bifurcation_points = [
    (3.0, "Period-2", 1.04, "center"),
    (3.449, "Period-4", 1.04, "right"),
    (3.544, "Period-8", 1.135, "center"),
    (chaos_onset, "Chaos onset", 1.04, "left"),
]

annotations = []
for r_bif, label, y_lab, anchor in bifurcation_points:
    fig.add_vline(x=r_bif, line={"color": INK_SOFT, "width": 1.5, "dash": "dot"})
    annotations.append(
        {
            "x": r_bif,
            "y": y_lab,
            "yref": "paper",
            "text": f"<b>{label}</b><br>r ≈ {r_bif}",
            "showarrow": False,
            "font": {"size": 14, "color": INK, "family": "Arial, sans-serif"},
            "bgcolor": ELEVATED_BG,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
            "borderpad": 4,
            "xanchor": anchor,
        }
    )

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "bifurcation-basic · python · plotly · anyplot.ai",
        "font": {"size": 20, "color": INK, "family": "Arial Black, Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    xaxis={
        "title": {"text": "Growth Rate (r)", "font": {"size": 15, "color": INK}, "standoff": 12},
        "tickfont": {"size": 12, "color": INK_SOFT},
        "showgrid": False,
        "range": [2.45, 4.05],
        "zeroline": False,
        "dtick": 0.25,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Steady-State Population (x)", "font": {"size": 15, "color": INK}, "standoff": 12},
        "tickfont": {"size": 12, "color": INK_SOFT},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "range": [-0.05, 1.05],
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    font={"color": INK},
    showlegend=False,
    margin={"l": 90, "r": 50, "t": 150, "b": 70},
    annotations=annotations,
    plot_bgcolor=PAGE_BG,
    paper_bgcolor=PAGE_BG,
    hoverlabel={"bgcolor": ELEVATED_BG, "font_size": 14, "font_color": INK},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

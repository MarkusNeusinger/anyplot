""" pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-20
"""

import numpy as np
import plotly.graph_objects as go


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

# Plot
python_blue = "#306998"

fig = go.Figure()

fig.add_trace(
    go.Scattergl(
        x=r_all,
        y=x_all,
        mode="markers",
        marker={"size": 1, "color": python_blue, "opacity": 0.15},
        showlegend=False,
        hovertemplate="r = %{x:.4f}<br>x = %{y:.4f}<extra></extra>",
    )
)

# Key bifurcation points
bifurcation_points = [(3.0, "Period-2"), (3.449, "Period-4"), (3.544, "Period-8"), (3.5699, "Chaos onset")]

annotations = []
offsets = {"Period-2": "center", "Period-4": "right", "Period-8": "right", "Chaos onset": "left"}
for r_bif, label in bifurcation_points:
    fig.add_vline(x=r_bif, line={"color": "rgba(200, 80, 80, 0.35)", "width": 1.5, "dash": "dot"})
    annotations.append(
        {
            "x": r_bif,
            "y": 1.03,
            "yref": "paper",
            "text": f"<b>{label}</b><br>r ≈ {r_bif}",
            "showarrow": False,
            "font": {"size": 13, "color": "#8B3A3A", "family": "Arial, sans-serif"},
            "bgcolor": "rgba(255,255,255,0.9)",
            "borderpad": 4,
            "xanchor": offsets[label],
        }
    )

# Style
fig.update_layout(
    title={
        "text": "Logistic Map · bifurcation-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2C3E50", "family": "Arial Black, Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.95,
    },
    xaxis={
        "title": {"text": "Growth Rate (r)", "font": {"size": 22, "family": "Arial, sans-serif"}, "standoff": 12},
        "tickfont": {"size": 18},
        "showgrid": False,
        "range": [2.45, 4.05],
        "zeroline": False,
        "dtick": 0.25,
    },
    yaxis={
        "title": {
            "text": "Steady-State Population (x)",
            "font": {"size": 22, "family": "Arial, sans-serif"},
            "standoff": 12,
        },
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.06)",
        "range": [-0.05, 1.05],
        "zeroline": False,
    },
    template="plotly_white",
    showlegend=False,
    margin={"l": 80, "r": 40, "t": 130, "b": 70},
    annotations=annotations,
    plot_bgcolor="white",
    paper_bgcolor="#FAFBFC",
    hoverlabel={"bgcolor": "white", "font_size": 14, "font_color": python_blue},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")

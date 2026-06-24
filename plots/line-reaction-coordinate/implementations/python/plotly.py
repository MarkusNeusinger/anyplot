"""anyplot.ai
line-reaction-coordinate: Reaction Coordinate Energy Diagram
Library: plotly 6.8.0 | Python 3.13.14
Quality: 89/100 | Updated: 2026-06-24
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens — Imprint palette (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette — curve + scientific annotation colors
BRAND = "#009E73"  # brand green — main reaction curve (Imprint position 1)
EA_COLOR = "#4467A3"  # blue — activation energy (Imprint position 3, kinetic)
DH_COLOR = "#BD8233"  # ochre — enthalpy change (Imprint position 4, thermodynamic)
FILL_COLOR = "rgba(0,158,115,0.10)" if THEME == "light" else "rgba(0,158,115,0.15)"

# Data — single-step exothermic reaction
reactant_energy = 50.0
transition_energy = 120.0
product_energy = 20.0
peak_pos = 0.4

reaction_coord = np.linspace(0, 1, 500)

baseline = reactant_energy + (product_energy - reactant_energy) * (3 * reaction_coord**2 - 2 * reaction_coord**3)

barrier_height = transition_energy - (
    reactant_energy + (product_energy - reactant_energy) * (3 * peak_pos**2 - 2 * peak_pos**3)
)
gaussian_bump = barrier_height * np.exp(-((reaction_coord - peak_pos) ** 2) / (2 * 0.018))

energy = baseline + gaussian_bump
peak_idx = int(np.argmax(energy))

# Plot
fig = go.Figure()

# Filled area under curve with brand green tint
fig.add_trace(
    go.Scatter(
        x=reaction_coord,
        y=energy,
        mode="lines",
        line={"color": "rgba(0,0,0,0)", "width": 0},
        fill="tozeroy",
        fillcolor=FILL_COLOR,
        showlegend=False,
        hoverinfo="skip",
    )
)

# Main reaction energy curve
fig.add_trace(
    go.Scatter(
        x=reaction_coord,
        y=energy,
        mode="lines",
        line={"color": BRAND, "width": 4, "shape": "spline"},
        showlegend=False,
        hovertemplate="Reaction Coordinate: %{x:.2f}<br>Energy: %{y:.1f} kJ/mol<extra></extra>",
    )
)

# Transition state peak marker dot
fig.add_trace(
    go.Scatter(
        x=[reaction_coord[peak_idx]],
        y=[energy[peak_idx]],
        mode="markers",
        marker={"color": BRAND, "size": 12, "symbol": "circle", "line": {"color": PAGE_BG, "width": 2}},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Horizontal dashed lines at reactant and product energy levels
for x0, x1, y_level in [(-0.05, 0.28, reactant_energy), (0.72, 1.05, product_energy)]:
    fig.add_shape(
        type="line", x0=x0, x1=x1, y0=y_level, y1=y_level, line={"color": INK_SOFT, "width": 1.5, "dash": "dash"}
    )

# Reference dashed line at reactant level on ΔH side
fig.add_shape(
    type="line",
    x0=0.82,
    x1=0.94,
    y0=reactant_energy,
    y1=reactant_energy,
    line={"color": INK_SOFT, "width": 1, "dash": "dot"},
)

# Reference dashed line at transition state level for Ea
ea_x = 0.14
fig.add_shape(
    type="line",
    x0=ea_x - 0.02,
    x1=peak_pos + 0.08,
    y0=transition_energy,
    y1=transition_energy,
    line={"color": INK_SOFT, "width": 1, "dash": "dot"},
)

# Activation energy (Ea) double-headed arrow
fig.add_shape(
    type="line", x0=ea_x, y0=reactant_energy, x1=ea_x, y1=transition_energy, line={"color": EA_COLOR, "width": 2.5}
)
fig.add_annotation(
    x=ea_x,
    y=transition_energy,
    ax=0,
    ay=-14,
    text="",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2.5,
    arrowcolor=EA_COLOR,
)
fig.add_annotation(
    x=ea_x,
    y=reactant_energy,
    ax=0,
    ay=14,
    text="",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2.5,
    arrowcolor=EA_COLOR,
)
fig.add_annotation(
    x=ea_x,
    y=(reactant_energy + transition_energy) / 2,
    text="<b>E<sub>a</sub> = 70 kJ/mol</b>",
    showarrow=False,
    xanchor="right",
    xshift=-14,
    font={"size": 12, "color": EA_COLOR, "family": "Arial, sans-serif"},
)

# Enthalpy change (ΔH) double-headed arrow
dh_x = 0.88
fig.add_shape(
    type="line", x0=dh_x, y0=product_energy, x1=dh_x, y1=reactant_energy, line={"color": DH_COLOR, "width": 2.5}
)
fig.add_annotation(
    x=dh_x,
    y=reactant_energy,
    ax=0,
    ay=-14,
    text="",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2.5,
    arrowcolor=DH_COLOR,
)
fig.add_annotation(
    x=dh_x,
    y=product_energy,
    ax=0,
    ay=14,
    text="",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.5,
    arrowwidth=2.5,
    arrowcolor=DH_COLOR,
)
fig.add_annotation(
    x=dh_x,
    y=(reactant_energy + product_energy) / 2,
    text="<b>ΔH = −30 kJ/mol</b>",
    showarrow=False,
    xanchor="left",
    xshift=14,
    font={"size": 12, "color": DH_COLOR, "family": "Arial, sans-serif"},
)

# Labels — Reactants, Transition State, Products
fig.add_annotation(
    x=0.02,
    y=reactant_energy,
    text="<b>Reactants</b><br>50 kJ/mol",
    showarrow=False,
    yshift=34,
    xanchor="left",
    font={"size": 12, "color": INK, "family": "Arial, sans-serif"},
)

fig.add_annotation(
    x=reaction_coord[peak_idx],
    y=energy[peak_idx],
    text="<b>Transition State</b><br>120 kJ/mol",
    showarrow=True,
    ay=-55,
    ax=45,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=1.5,
    arrowcolor=INK_SOFT,
    font={"size": 12, "color": INK, "family": "Arial, sans-serif"},
)

fig.add_annotation(
    x=0.98,
    y=product_energy,
    text="<b>Products</b><br>20 kJ/mol",
    showarrow=False,
    yshift=-32,
    xanchor="right",
    font={"size": 12, "color": INK, "family": "Arial, sans-serif"},
)

# Title — length 55 chars < 67 baseline, no scaling needed
title = "line-reaction-coordinate · python · plotly · anyplot.ai"
title_len = len(title)
title_fontsize = round(16 * (67 / title_len)) if title_len > 67 else 16

# Style
fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"family": "Arial, sans-serif", "color": INK},
    title={
        "text": title,
        "font": {"size": title_fontsize, "family": "Arial, sans-serif", "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {
            "text": "Reaction Coordinate",
            "font": {"size": 12, "family": "Arial, sans-serif", "color": INK},
            "standoff": 15,
        },
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "showticklabels": False,
        "zeroline": False,
        "range": [-0.08, 1.08],
        "showline": True,
        "linecolor": INK_SOFT,
        "linewidth": 1,
    },
    yaxis={
        "title": {
            "text": "Potential Energy (kJ/mol)",
            "font": {"size": 12, "family": "Arial, sans-serif", "color": INK},
            "standoff": 10,
        },
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "range": [0, 140],
        "showline": True,
        "linecolor": INK_SOFT,
        "linewidth": 1,
        "dtick": 20,
    },
    margin={"l": 85, "r": 40, "t": 80, "b": 65},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

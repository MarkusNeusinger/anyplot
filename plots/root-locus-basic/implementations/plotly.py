"""pyplots.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: plotly | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import numpy as np
import plotly.graph_objects as go


# Data: Transfer function G(s) = 1 / (s(s+1)(s+3))
# Open-loop poles at s = 0, -1, -3; no zeros
# Closed-loop characteristic: s(s+1)(s+3) + K = 0  =>  s^3 + 4s^2 + 3s + K = 0
open_loop_poles = np.array([0.0, -1.0, -3.0])
open_loop_zeros = np.array([])

gains = np.concatenate(
    [
        np.linspace(0, 0.5, 200),
        np.linspace(0.5, 4, 400),
        np.linspace(4, 12, 400),
        np.linspace(12, 50, 300),
        np.linspace(50, 200, 200),
    ]
)

branches = {i: {"real": [], "imag": [], "gain": []} for i in range(3)}

prev_roots = open_loop_poles.copy().astype(complex)
for K in gains:
    coeffs = [1, 4, 3, K]
    roots = np.roots(coeffs)
    roots = np.sort_complex(roots)

    # Match roots to branches by nearest assignment
    used = [False] * len(roots)
    assignment = [0] * len(roots)
    for i in range(len(prev_roots)):
        best_j = -1
        best_dist = np.inf
        for j in range(len(roots)):
            if not used[j]:
                d = abs(prev_roots[i] - roots[j])
                if d < best_dist:
                    best_dist = d
                    best_j = j
        used[best_j] = True
        assignment[i] = best_j

    for i in range(3):
        r = roots[assignment[i]]
        branches[i]["real"].append(r.real)
        branches[i]["imag"].append(r.imag)
        branches[i]["gain"].append(K)

    prev_roots = np.array([roots[assignment[i]] for i in range(3)])

# Colors for branches
branch_colors = ["#306998", "#E8833A", "#5BA85B"]

# Plot
fig = go.Figure()

# Locus branches
for i in range(3):
    fig.add_trace(
        go.Scatter(
            x=branches[i]["real"],
            y=branches[i]["imag"],
            mode="lines",
            line={"width": 3, "color": branch_colors[i]},
            name=f"Branch {i + 1}",
            hovertemplate="Re = %{x:.3f}<br>Im = %{y:.3f}<br>K = %{customdata:.2f}<extra>Branch "
            + str(i + 1)
            + "</extra>",
            customdata=branches[i]["gain"],
        )
    )

# Direction arrows on branches indicating increasing gain
for i in range(3):
    n = len(branches[i]["real"])
    for frac in [0.3, 0.65]:
        idx = int(n * frac)
        if idx < n - 5:
            dx = branches[i]["real"][idx + 5] - branches[i]["real"][idx]
            dy = branches[i]["imag"][idx + 5] - branches[i]["imag"][idx]
            norm = np.sqrt(dx**2 + dy**2)
            if norm > 1e-6:
                fig.add_annotation(
                    x=branches[i]["real"][idx],
                    y=branches[i]["imag"][idx],
                    ax=-dx / norm * 25,
                    ay=dy / norm * 25,
                    xref="x",
                    yref="y",
                    axref="pixel",
                    ayref="pixel",
                    showarrow=True,
                    arrowhead=3,
                    arrowsize=1.8,
                    arrowwidth=2.5,
                    arrowcolor=branch_colors[i],
                    text="",
                )

# Open-loop poles (x markers)
fig.add_trace(
    go.Scatter(
        x=open_loop_poles.real,
        y=np.zeros(len(open_loop_poles)),
        mode="markers",
        marker={"symbol": "x", "size": 16, "color": "#2C3E50", "line": {"width": 3}},
        name="Open-loop poles",
        hovertemplate="Pole: %{x:.1f}<extra></extra>",
    )
)

# Imaginary axis crossing: Routh criterion gives K_crit = 12, roots at s = ±j√3
K_crit = 12.0
jw_cross = np.sqrt(3)
fig.add_trace(
    go.Scatter(
        x=[0, 0],
        y=[jw_cross, -jw_cross],
        mode="markers",
        marker={"symbol": "diamond", "size": 14, "color": "#E74C3C", "line": {"width": 2, "color": "white"}},
        name=f"jω crossing (K={K_crit:.0f})",
        hovertemplate="s = ±j√3<br>K = 12<extra></extra>",
    )
)

# Breakaway point: derivative of K w.r.t. s = 0 => s ≈ -0.451
s_break = -0.451
K_break = -(s_break**3 + 4 * s_break**2 + 3 * s_break)
fig.add_trace(
    go.Scatter(
        x=[s_break],
        y=[0],
        mode="markers",
        marker={"symbol": "star", "size": 16, "color": "#9B59B6", "line": {"width": 1.5, "color": "white"}},
        name=f"Breakaway (K={K_break:.2f})",
        hovertemplate="s ≈ -0.451<br>K ≈ %{customdata:.2f}<extra></extra>",
        customdata=[K_break],
    )
)

# Constant damping ratio lines (ζ = 0.2, 0.4, 0.6, 0.8)
r_max = 5.0
for zeta in [0.2, 0.4, 0.6, 0.8]:
    r_line = np.linspace(0, r_max, 2)
    fig.add_trace(
        go.Scatter(
            x=-r_line * zeta,
            y=r_line * np.sqrt(1 - zeta**2),
            mode="lines",
            line={"width": 1, "color": "rgba(150,150,150,0.3)", "dash": "dash"},
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=-r_line * zeta,
            y=-r_line * np.sqrt(1 - zeta**2),
            mode="lines",
            line={"width": 1, "color": "rgba(150,150,150,0.3)", "dash": "dash"},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Constant natural frequency circles (ωn = 1, 2, 3)
theta = np.linspace(np.pi / 2, np.pi, 100)
for wn in [1, 2, 3]:
    fig.add_trace(
        go.Scatter(
            x=wn * np.cos(theta),
            y=wn * np.sin(theta),
            mode="lines",
            line={"width": 1, "color": "rgba(150,150,150,0.2)", "dash": "dot"},
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=wn * np.cos(theta),
            y=-wn * np.sin(theta),
            mode="lines",
            line={"width": 1, "color": "rgba(150,150,150,0.2)", "dash": "dot"},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Real axis segments of root locus (to the left of odd number of poles/zeros)
# For G(s) = 1/(s(s+1)(s+3)): segments [-1, 0] and [-inf, -3]
fig.add_trace(
    go.Scatter(
        x=[-1, 0],
        y=[0, 0],
        mode="lines",
        line={"width": 5, "color": "rgba(48,105,152,0.25)"},
        showlegend=False,
        hoverinfo="skip",
    )
)
fig.add_trace(
    go.Scatter(
        x=[-5.5, -3],
        y=[0, 0],
        mode="lines",
        line={"width": 5, "color": "rgba(48,105,152,0.25)"},
        showlegend=False,
        hoverinfo="skip",
    )
)

# Style
fig.update_layout(
    title={
        "text": "root-locus-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2C3E50", "family": "Arial Black, Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.95,
    },
    xaxis={
        "title": {"text": "Real Axis (σ)", "font": {"size": 22, "family": "Arial, sans-serif"}, "standoff": 12},
        "tickfont": {"size": 18},
        "zeroline": True,
        "zerolinewidth": 1.5,
        "zerolinecolor": "rgba(0,0,0,0.3)",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.06)",
        "range": [-5.5, 2],
        "constrain": "domain",
        "dtick": 1,
    },
    yaxis={
        "title": {"text": "Imaginary Axis (jω)", "font": {"size": 22, "family": "Arial, sans-serif"}, "standoff": 12},
        "tickfont": {"size": 18},
        "zeroline": True,
        "zerolinewidth": 1.5,
        "zerolinecolor": "rgba(0,0,0,0.3)",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.06)",
        "range": [-5, 5],
        "dtick": 1,
    },
    template="plotly_white",
    legend={
        "font": {"size": 15},
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "rgba(0,0,0,0.1)",
        "borderwidth": 1,
        "x": 0.02,
        "y": 0.98,
    },
    margin={"l": 80, "r": 40, "t": 100, "b": 70},
    plot_bgcolor="white",
    paper_bgcolor="#FAFBFC",
    hoverlabel={"bgcolor": "white", "font_size": 14},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")

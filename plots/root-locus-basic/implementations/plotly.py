"""pyplots.ai
root-locus-basic: Root Locus Plot for Control Systems
Library: plotly 6.6.0 | Python 3.14.3
"""

import numpy as np
import plotly.graph_objects as go


# Data: Transfer function G(s) = 1 / (s(s+1)(s+3))
# Open-loop poles at s = 0, -1, -3; no zeros
# Closed-loop characteristic: s(s+1)(s+3) + K = 0  =>  s^3 + 4s^2 + 3s + K = 0
open_loop_poles = np.array([0.0, -1.0, -3.0])

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

# Colors for branches — strong contrast against gray reference lines
branch_colors = ["#306998", "#D4541B", "#2E8B57"]
branch_names = ["Branch 1 (from s=0)", "Branch 2 (from s=−1)", "Branch 3 (from s=−3)"]

# Plot
fig = go.Figure()

# Real axis segments of root locus (background layer, drawn first)
# For G(s) = 1/(s(s+1)(s+3)): segments [-1, 0] and [-inf, -3]
for seg in [[-1, 0], [-5.5, -3]]:
    fig.add_trace(
        go.Scatter(
            x=seg,
            y=[0, 0],
            mode="lines",
            line={"width": 8, "color": "rgba(48,105,152,0.15)"},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Constant damping ratio lines (ζ = 0.2, 0.4, 0.6, 0.8)
r_max = 5.5
for zeta in [0.2, 0.4, 0.6, 0.8]:
    r_line = np.linspace(0, r_max, 2)
    x_vals = -r_line * zeta
    y_vals = r_line * np.sqrt(1 - zeta**2)
    for sign in [1, -1]:
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=sign * y_vals,
                mode="lines",
                line={"width": 1, "color": "rgba(160,160,160,0.35)", "dash": "dash"},
                showlegend=False,
                hoverinfo="skip",
            )
        )
    # Label damping ratio at the top of each line
    fig.add_annotation(
        x=x_vals[-1],
        y=y_vals[-1] + 0.15,
        text=f"ζ={zeta}",
        showarrow=False,
        font={"size": 11, "color": "rgba(120,120,120,0.7)"},
    )

# Constant natural frequency circles (ωn = 1, 2, 3)
theta = np.linspace(np.pi / 2, np.pi, 100)
for wn in [1, 2, 3]:
    for sign in [1, -1]:
        fig.add_trace(
            go.Scatter(
                x=wn * np.cos(theta),
                y=sign * wn * np.sin(theta),
                mode="lines",
                line={"width": 1, "color": "rgba(160,160,160,0.25)", "dash": "dot"},
                showlegend=False,
                hoverinfo="skip",
            )
        )
    # Label natural frequency at top of arc
    fig.add_annotation(
        x=wn * np.cos(np.pi * 0.55),
        y=wn * np.sin(np.pi * 0.55) + 0.15,
        text=f"ωn={wn}",
        showarrow=False,
        font={"size": 11, "color": "rgba(120,120,120,0.6)"},
    )

# Stability boundary — vertical line at real axis = 0
fig.add_shape(
    type="line", x0=0, x1=0, y0=-5.5, y1=5.5, line={"color": "rgba(220,60,60,0.12)", "width": 18}, layer="below"
)
fig.add_annotation(
    x=0.35,
    y=4.8,
    text="Stability<br>Boundary",
    showarrow=False,
    font={"size": 12, "color": "rgba(200,60,60,0.5)", "family": "Arial, sans-serif"},
)

# Locus branches with gradient-like coloring via varying opacity
for i in range(3):
    fig.add_trace(
        go.Scatter(
            x=branches[i]["real"],
            y=branches[i]["imag"],
            mode="lines",
            line={"width": 3.5, "color": branch_colors[i]},
            name=branch_names[i],
            legendgroup=f"branch{i}",
            hovertemplate=(
                "<b>Branch " + str(i + 1) + "</b><br>"
                "σ = %{x:.3f}<br>"
                "jω = %{y:.3f}<br>"
                "K = %{customdata:.2f}"
                "<extra></extra>"
            ),
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

# Open-loop poles (x markers) — larger and bolder
fig.add_trace(
    go.Scatter(
        x=open_loop_poles.real,
        y=np.zeros(len(open_loop_poles)),
        mode="markers+text",
        marker={"symbol": "x-thin", "size": 20, "color": "#1A1A2E", "line": {"width": 3.5}},
        text=["s=0", "s=−1", "s=−3"],
        textposition="top center",
        textfont={"size": 13, "color": "#1A1A2E"},
        name="Open-loop poles",
        hovertemplate="Pole at s = %{x:.1f}<extra></extra>",
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
        marker={"symbol": "diamond", "size": 16, "color": "#E74C3C", "line": {"width": 2.5, "color": "white"}},
        name=f"jω crossing (K={K_crit:.0f})",
        hovertemplate="s = %{y:+.3f}j<br>K = 12 (critical gain)<extra></extra>",
    )
)
# Annotate jw crossing with K value
fig.add_annotation(
    x=0,
    y=jw_cross,
    text=f"  K={K_crit:.0f}",
    showarrow=True,
    arrowhead=0,
    arrowwidth=1,
    arrowcolor="#E74C3C",
    ax=45,
    ay=-20,
    font={"size": 13, "color": "#E74C3C", "family": "Arial, sans-serif"},
)

# Breakaway point: derivative of K w.r.t. s = 0 => s ≈ -0.451
s_break = -0.451
K_break = -(s_break**3 + 4 * s_break**2 + 3 * s_break)
fig.add_trace(
    go.Scatter(
        x=[s_break],
        y=[0],
        mode="markers",
        marker={"symbol": "star", "size": 22, "color": "#8E44AD", "line": {"width": 2, "color": "white"}},
        name=f"Breakaway (K≈{K_break:.2f})",
        hovertemplate="Breakaway point<br>s ≈ −0.451<br>K ≈ %{customdata:.2f}<extra></extra>",
        customdata=[K_break],
    )
)
# Annotate breakaway
fig.add_annotation(
    x=s_break,
    y=0,
    text=f"  K≈{K_break:.2f}",
    showarrow=True,
    arrowhead=0,
    arrowwidth=1,
    arrowcolor="#8E44AD",
    ax=-50,
    ay=30,
    font={"size": 13, "color": "#8E44AD", "family": "Arial, sans-serif"},
)

# Style — equal axis scaling via scaleanchor
axis_range = 5.5
fig.update_layout(
    title={
        "text": "root-locus-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#1A1A2E", "family": "Arial Black, Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Real Axis (σ)", "font": {"size": 22, "family": "Arial, sans-serif"}, "standoff": 12},
        "tickfont": {"size": 18},
        "zeroline": True,
        "zerolinewidth": 1.5,
        "zerolinecolor": "rgba(0,0,0,0.2)",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.05)",
        "range": [-axis_range, 2],
        "constrain": "domain",
        "dtick": 1,
    },
    yaxis={
        "title": {"text": "Imaginary Axis (jω)", "font": {"size": 22, "family": "Arial, sans-serif"}, "standoff": 12},
        "tickfont": {"size": 18},
        "zeroline": True,
        "zerolinewidth": 1.5,
        "zerolinecolor": "rgba(0,0,0,0.2)",
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.05)",
        "range": [-axis_range, axis_range],
        "scaleanchor": "x",
        "scaleratio": 1,
        "dtick": 1,
    },
    template="plotly_white",
    legend={
        "font": {"size": 14, "family": "Arial, sans-serif"},
        "bgcolor": "rgba(255,255,255,0.92)",
        "bordercolor": "rgba(0,0,0,0.08)",
        "borderwidth": 1,
        "x": 0.01,
        "y": 0.99,
        "itemsizing": "constant",
    },
    margin={"l": 80, "r": 40, "t": 100, "b": 70},
    plot_bgcolor="white",
    paper_bgcolor="#F8F9FB",
    hoverlabel={"bgcolor": "white", "font_size": 14, "bordercolor": "#ccc"},
)

# Add subtitle annotation for transfer function
fig.add_annotation(
    text="G(s) = 1 / s(s+1)(s+3)",
    xref="paper",
    yref="paper",
    x=0.5,
    y=1.01,
    showarrow=False,
    font={"size": 16, "color": "#555", "family": "Courier New, monospace"},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")

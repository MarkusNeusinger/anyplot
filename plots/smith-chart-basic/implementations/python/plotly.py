""" pyplots.ai
smith-chart-basic: Smith Chart for RF/Impedance
Library: plotly 6.5.2 | Python 3.13.11
Quality: 91/100 | Created: 2026-01-15
"""

import numpy as np
import plotly.graph_objects as go


# Reference impedance
Z0 = 50  # ohms

# Generate sample impedance data (antenna-like frequency sweep)
np.random.seed(42)
freq = np.linspace(1e9, 6e9, 50)  # 1-6 GHz

# Simulate realistic antenna impedance trajectory
# Starting inductive, moving through resonance to capacitive
t = np.linspace(0, 2 * np.pi, 50)
z_real = 25 + 40 * np.sin(t / 2) ** 2 + 5 * np.random.randn(50)
z_imag = 60 * np.cos(t) + 10 * np.sin(2 * t)

# Normalize impedance
z_norm = (z_real + 1j * z_imag) / Z0

# Calculate reflection coefficient (gamma)
gamma = (z_norm - 1) / (z_norm + 1)
gamma_real = gamma.real
gamma_imag = gamma.imag

# Create figure
fig = go.Figure()

# Draw Smith chart grid - constant resistance circles
r_values = [0, 0.2, 0.5, 1, 2, 5]
theta_grid = np.linspace(0, 2 * np.pi, 200)

for r in r_values:
    # Constant resistance circle: center at (r/(r+1), 0), radius 1/(r+1)
    center_x = r / (r + 1)
    radius = 1 / (r + 1)
    circle_x = center_x + radius * np.cos(theta_grid)
    circle_y = radius * np.sin(theta_grid)
    # Clip to unit circle
    mask = circle_x**2 + circle_y**2 <= 1.01
    circle_x_clipped = np.where(mask, circle_x, np.nan)
    circle_y_clipped = np.where(mask, circle_y, np.nan)
    fig.add_trace(
        go.Scatter(
            x=circle_x_clipped,
            y=circle_y_clipped,
            mode="lines",
            line=dict(color="rgba(100,100,100,0.4)", width=1),
            hoverinfo="skip",
            showlegend=False,
        )
    )

# Draw constant reactance arcs
x_values = [0.2, 0.5, 1, 2, 5]

for x in x_values:
    # Constant reactance arc: center at (1, 1/x), radius 1/x
    center_y = 1 / x
    radius = 1 / x
    arc_theta = np.linspace(-np.pi, np.pi, 400)
    arc_x = 1 + radius * np.cos(arc_theta)
    arc_y = center_y + radius * np.sin(arc_theta)
    # Clip to unit circle
    mask = (arc_x**2 + arc_y**2 <= 1.01) & (arc_x >= -1)
    arc_x_clipped = np.where(mask, arc_x, np.nan)
    arc_y_clipped = np.where(mask, arc_y, np.nan)
    fig.add_trace(
        go.Scatter(
            x=arc_x_clipped,
            y=arc_y_clipped,
            mode="lines",
            line=dict(color="rgba(100,100,100,0.4)", width=1),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    # Negative reactance (mirror)
    fig.add_trace(
        go.Scatter(
            x=arc_x_clipped,
            y=-arc_y_clipped,
            mode="lines",
            line=dict(color="rgba(100,100,100,0.4)", width=1),
            hoverinfo="skip",
            showlegend=False,
        )
    )

# Draw horizontal axis (real axis)
fig.add_trace(
    go.Scatter(
        x=[-1, 1],
        y=[0, 0],
        mode="lines",
        line=dict(color="rgba(100,100,100,0.5)", width=1),
        hoverinfo="skip",
        showlegend=False,
    )
)

# Draw unit circle (boundary)
boundary_theta = np.linspace(0, 2 * np.pi, 200)
fig.add_trace(
    go.Scatter(
        x=np.cos(boundary_theta),
        y=np.sin(boundary_theta),
        mode="lines",
        line=dict(color="#306998", width=2),
        hoverinfo="skip",
        showlegend=False,
    )
)

# Plot impedance locus
freq_ghz = freq / 1e9
hover_text = [f"{f:.2f} GHz<br>Z = {z_real[i]:.1f} + j{z_imag[i]:.1f} Ω" for i, f in enumerate(freq_ghz)]

fig.add_trace(
    go.Scatter(
        x=gamma_real,
        y=gamma_imag,
        mode="lines+markers",
        line=dict(color="#306998", width=4),
        marker=dict(size=10, color="#FFD43B", line=dict(color="#306998", width=2)),
        name="Impedance Locus",
        text=hover_text,
        hoverinfo="text",
    )
)

# Add frequency labels at key points with varied positions to avoid overlap
label_configs = [
    (0, 40, -40),  # 1.0 GHz - upper right
    (16, -50, -30),  # 2.6 GHz - left
    (32, 50, 30),  # 4.3 GHz - right
    (49, 40, -50),  # 6.0 GHz - upper right
]
for idx, ax_offset, ay_offset in label_configs:
    fig.add_annotation(
        x=gamma_real[idx],
        y=gamma_imag[idx],
        text=f"{freq_ghz[idx]:.1f} GHz",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="#306998",
        ax=ax_offset,
        ay=ay_offset,
        font=dict(size=16, color="#306998"),
        bgcolor="white",
        bordercolor="#306998",
        borderwidth=1,
        borderpad=4,
    )

# Mark center (matched condition)
fig.add_trace(
    go.Scatter(
        x=[0],
        y=[0],
        mode="markers",
        marker=dict(size=15, color="#FFD43B", symbol="x", line=dict(color="#306998", width=3)),
        name="Matched (Z = Z₀)",
        hoverinfo="name",
    )
)

# Update layout
fig.update_layout(
    title=dict(text="smith-chart-basic · plotly · pyplots.ai", font=dict(size=28), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Real(Γ)", font=dict(size=22)),
        tickfont=dict(size=18),
        range=[-1.15, 1.15],
        scaleanchor="y",
        scaleratio=1,
        showgrid=False,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Imag(Γ)", font=dict(size=22)),
        tickfont=dict(size=18),
        range=[-1.15, 1.15],
        showgrid=False,
        zeroline=False,
    ),
    template="plotly_white",
    legend=dict(
        x=0.02, y=0.98, font=dict(size=18), bgcolor="rgba(255,255,255,0.9)", bordercolor="#306998", borderwidth=1
    ),
    margin=dict(l=80, r=80, t=100, b=80),
)

# Add resistance labels on the right
r_labels = [(0, "0"), (0.2, "0.2"), (0.5, "0.5"), (1, "1"), (2, "2"), (5, "5")]
for r, label in r_labels:
    x_pos = r / (r + 1) + 1 / (r + 1)
    if x_pos <= 1.0:
        fig.add_annotation(x=x_pos, y=0, text=label, showarrow=False, font=dict(size=14, color="gray"), yshift=-20)

# Add reactance labels at chart boundary
reactance_label_positions = [
    (1, 0.85, 0.52, "+j1"),  # +j1 label
    (1, 0.85, -0.52, "-j1"),  # -j1 label
    (0.5, 0.6, 0.8, "+j0.5"),  # +j0.5 label
    (0.5, 0.6, -0.8, "-j0.5"),  # -j0.5 label
]
for _x, lx, ly, label in reactance_label_positions:
    fig.add_annotation(x=lx, y=ly, text=label, showarrow=False, font=dict(size=14, color="gray"))

# Save as PNG and HTML
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")

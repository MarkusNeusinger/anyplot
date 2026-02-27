"""pyplots.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: plotly | Python 3.13
Quality: pending | Created: 2026-02-27
"""

import plotly.graph_objects as go


# Data - Hydrogen atom energy levels (E_n = -13.6/n² eV)
quantum_numbers = [1, 2, 3, 4, 5, 6]
energies = {n: -13.6 / n**2 for n in quantum_numbers}

# Transitions: (upper_n, lower_n, label)
lyman_series = [(2, 1, "Ly-α<br>121.6 nm"), (3, 1, "Ly-β<br>102.6 nm"), (4, 1, "Ly-γ<br>97.2 nm")]
balmer_series = [(3, 2, "Hα<br>656.3 nm"), (4, 2, "Hβ<br>486.1 nm"), (5, 2, "Hγ<br>434.0 nm"), (6, 2, "Hδ<br>410.2 nm")]

# Colors mapped to spectral characteristics
lyman_colors = ["#9C27B0", "#7B1FA2", "#6A1B9A"]
balmer_colors = ["#D32F2F", "#0288D1", "#5E35B1", "#4527A0"]

# Plot
fig = go.Figure()

# Invisible trace to establish coordinate system
fig.add_trace(
    go.Scatter(x=[0, 1], y=[-15, 2.5], mode="markers", marker={"opacity": 0}, showlegend=False, hoverinfo="skip")
)

# Energy level lines
line_left = 0.15
line_right = 0.85
for _n, energy in energies.items():
    fig.add_shape(type="line", x0=line_left, x1=line_right, y0=energy, y1=energy, line={"color": "#306998", "width": 3})

# Right-side quantum number labels (well-separated: n=1,2,3)
for n in [1, 2, 3]:
    fig.add_annotation(
        x=line_right + 0.02,
        y=energies[n],
        text=f"<b>n = {n}</b>",
        showarrow=False,
        font={"size": 16, "color": "#306998"},
        xanchor="left",
        yanchor="middle",
    )

# Right-side labels for crowded upper levels (n=4,5,6) with yshift to avoid overlap
upper_label_shifts = {4: -10, 5: 2, 6: 14}
for n, shift in upper_label_shifts.items():
    fig.add_annotation(
        x=line_right + 0.02,
        y=energies[n],
        text=f"<b>n = {n}</b>",
        showarrow=False,
        font={"size": 13, "color": "#306998"},
        xanchor="left",
        yanchor="middle",
        yshift=shift,
    )

# Left-side energy labels (only for well-separated levels to avoid clutter)
for n in [1, 2, 3]:
    fig.add_annotation(
        x=line_left - 0.02,
        y=energies[n],
        text=f"{energies[n]:.2f} eV",
        showarrow=False,
        font={"size": 14, "color": "#555"},
        xanchor="right",
        yanchor="middle",
    )

# Ionization limit
fig.add_shape(type="line", x0=0.1, x1=0.9, y0=0, y1=0, line={"color": "#999", "width": 2, "dash": "dash"})
fig.add_annotation(
    x=line_right + 0.02,
    y=0,
    text="<b>Ionization</b>  (0 eV)",
    showarrow=False,
    font={"size": 13, "color": "#999"},
    xanchor="left",
    yanchor="bottom",
    yshift=4,
)

# Lyman series transition arrows (left portion)
lyman_x = [0.26, 0.32, 0.38]
for i, (n_up, n_low, label) in enumerate(lyman_series):
    e_up = energies[n_up]
    e_low = energies[n_low]
    fig.add_annotation(
        x=lyman_x[i],
        y=e_low + 0.2,
        ax=lyman_x[i],
        ay=e_up - 0.2,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.5,
        arrowwidth=2.5,
        arrowcolor=lyman_colors[i],
        text="",
    )
    fig.add_annotation(
        x=lyman_x[i] - 0.015,
        y=(e_up + e_low) / 2,
        text=label,
        showarrow=False,
        font={"size": 11, "color": lyman_colors[i]},
        xanchor="right",
    )

# Balmer series transition arrows (right portion)
balmer_x = [0.56, 0.62, 0.68, 0.74]
for i, (n_up, n_low, label) in enumerate(balmer_series):
    e_up = energies[n_up]
    e_low = energies[n_low]
    fig.add_annotation(
        x=balmer_x[i],
        y=e_low + 0.15,
        ax=balmer_x[i],
        ay=e_up - 0.15,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.5,
        arrowwidth=2.5,
        arrowcolor=balmer_colors[i],
        text="",
    )
    fig.add_annotation(
        x=balmer_x[i] + 0.015,
        y=(e_up + e_low) / 2,
        text=label,
        showarrow=False,
        font={"size": 11, "color": balmer_colors[i]},
        xanchor="left",
    )

# Series group labels
fig.add_annotation(
    x=0.32, y=1.5, text="<b>Lyman Series</b> (UV)", showarrow=False, font={"size": 18, "color": "#7B1FA2"}
)
fig.add_annotation(
    x=0.65, y=1.5, text="<b>Balmer Series</b> (Visible)", showarrow=False, font={"size": 18, "color": "#D32F2F"}
)

# Layout
fig.update_layout(
    title={
        "text": "Hydrogen Atom · energy-level-atomic · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"visible": False, "range": [0, 1], "fixedrange": True},
    yaxis={
        "title": {"text": "Energy (eV)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [-15, 2.5],
        "zeroline": False,
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
    },
    template="plotly_white",
    plot_bgcolor="white",
    margin={"l": 120, "r": 140, "t": 80, "b": 60},
    showlegend=False,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")

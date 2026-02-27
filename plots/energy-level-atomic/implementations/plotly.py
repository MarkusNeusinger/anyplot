""" pyplots.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: plotly 6.5.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-02-27
"""

import plotly.graph_objects as go


# Data - Hydrogen atom energy levels (E_n = -13.6/n² eV)
quantum_numbers = [1, 2, 3, 4, 5, 6]
energies = {n: -13.6 / n**2 for n in quantum_numbers}

# Transitions: (upper_n, lower_n, display_label, wavelength_nm)
lyman_series = [(2, 1, "Ly-α<br>121.6 nm", 121.6), (3, 1, "Ly-β<br>102.6 nm", 102.6), (4, 1, "Ly-γ<br>97.2 nm", 97.2)]
balmer_series = [
    (3, 2, "Hα<br>656.3 nm", 656.3),
    (4, 2, "Hβ<br>486.1 nm", 486.1),
    (5, 2, "Hγ<br>434.0 nm", 434.0),
    (6, 2, "Hδ<br>410.2 nm", 410.2),
]
paschen_series = [(4, 3, "Pa-α  1875 nm", 1875.1), (5, 3, "Pa-β  1282 nm", 1281.8)]

# Colors - well-differentiated within each series
lyman_colors = ["#7B1FA2", "#C2185B", "#303F9F"]  # Purple, magenta, indigo
balmer_colors = ["#D32F2F", "#0288D1", "#00897B", "#F9A825"]  # Red, blue, teal, amber
paschen_colors = ["#E65100", "#BF360C"]  # Deep orange, dark red-brown

# Create figure
fig = go.Figure()

# Energy level lines as go.Scatter traces (idiomatic Plotly, enables hover)
line_left = 0.12
line_right = 0.88
for n in quantum_numbers:
    energy = energies[n]
    fig.add_trace(
        go.Scatter(
            x=[line_left, line_right],
            y=[energy, energy],
            mode="lines",
            line={"color": "#306998", "width": 3},
            showlegend=False,
            hovertemplate=f"<b>n = {n}</b><br>E = {energy:.2f} eV<extra></extra>",
        )
    )

# Ionization limit as a trace with hover
fig.add_trace(
    go.Scatter(
        x=[0.08, 0.92],
        y=[0, 0],
        mode="lines",
        line={"color": "#888", "width": 2, "dash": "dash"},
        showlegend=False,
        hovertemplate="<b>Ionization Limit</b><br>E = 0 eV  (n → ∞)<extra></extra>",
    )
)

# Quantum number labels - right side (well-separated: n=1,2,3)
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

# Upper level labels (n=4,5,6) with yshift to avoid overlap with each other and ionization
for n, shift in [(4, -18), (5, 0), (6, 14)]:
    fig.add_annotation(
        x=line_right + 0.02,
        y=energies[n],
        text=f"<b>n = {n}</b>",
        showarrow=False,
        font={"size": 16, "color": "#306998"},
        xanchor="left",
        yanchor="middle",
        yshift=shift,
    )

# Left-side energy values for well-separated levels
for n in [1, 2, 3]:
    fig.add_annotation(
        x=line_left - 0.02,
        y=energies[n],
        text=f"<b>{energies[n]:.2f}</b> eV",
        showarrow=False,
        font={"size": 16, "color": "#555"},
        xanchor="right",
        yanchor="middle",
    )

# Ionization label on left side, positioned just above the dashed line
fig.add_annotation(
    x=line_left - 0.02,
    y=0,
    text="<b>0</b> eV  <i>Ionization</i>",
    showarrow=False,
    font={"size": 16, "color": "#888"},
    xanchor="right",
    yanchor="bottom",
    yshift=3,
)

# --- Lyman Series (UV) - left portion ---
lyman_x = [0.21, 0.27, 0.33]
for i, (n_up, n_low, label, _wl) in enumerate(lyman_series):
    e_up, e_low = energies[n_up], energies[n_low]
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
        font={"size": 16, "color": lyman_colors[i]},
        xanchor="right",
    )

# --- Balmer Series (Visible) - center portion ---
balmer_x = [0.43, 0.49, 0.55, 0.61]
for i, (n_up, n_low, label, _wl) in enumerate(balmer_series):
    e_up, e_low = energies[n_up], energies[n_low]
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
        font={"size": 16, "color": balmer_colors[i]},
        xanchor="left",
    )

# --- Paschen Series (Infrared) - right portion ---
paschen_x = [0.73, 0.80]
paschen_label_y = [-2.2, -2.7]  # Clear gap between n=2 (-3.40) and n=3 (-1.51)
for i, (n_up, n_low, label, _wl) in enumerate(paschen_series):
    e_up, e_low = energies[n_up], energies[n_low]
    fig.add_annotation(
        x=paschen_x[i],
        y=e_low + 0.06,
        ax=paschen_x[i],
        ay=e_up - 0.06,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.5,
        arrowwidth=2.5,
        arrowcolor=paschen_colors[i],
        text="",
    )
    fig.add_annotation(
        x=paschen_x[i],
        y=paschen_label_y[i],
        text=label,
        showarrow=False,
        font={"size": 16, "color": paschen_colors[i]},
        xanchor="center",
    )

# Invisible hover targets at transition midpoints for HTML interactivity
for series, _colors, x_pos, name in [
    (lyman_series, lyman_colors, lyman_x, "Lyman"),
    (balmer_series, balmer_colors, balmer_x, "Balmer"),
    (paschen_series, paschen_colors, paschen_x, "Paschen"),
]:
    hover_x, hover_y, hover_labels = [], [], []
    for i, (n_up, n_low, _lbl, wl) in enumerate(series):
        e_up, e_low = energies[n_up], energies[n_low]
        hover_x.append(x_pos[i])
        hover_y.append((e_up + e_low) / 2)
        hover_labels.append(
            f"<b>{name} Series</b><br>n={n_up} → n={n_low}<br>λ = {wl} nm<br>ΔE = {abs(e_up - e_low):.2f} eV"
        )
    fig.add_trace(
        go.Scatter(
            x=hover_x,
            y=hover_y,
            mode="markers",
            marker={"size": 30, "opacity": 0},
            showlegend=False,
            hovertext=hover_labels,
            hoverinfo="text",
        )
    )

# Series group labels
fig.add_annotation(
    x=0.27,
    y=1.6,
    text="<b>Lyman Series</b><br><i>Ultraviolet</i>",
    showarrow=False,
    font={"size": 17, "color": "#7B1FA2"},
)
fig.add_annotation(
    x=0.52, y=1.6, text="<b>Balmer Series</b><br><i>Visible</i>", showarrow=False, font={"size": 17, "color": "#D32F2F"}
)
fig.add_annotation(
    x=0.77,
    y=1.6,
    text="<b>Paschen Series</b><br><i>Infrared</i>",
    showarrow=False,
    font={"size": 17, "color": "#E65100"},
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

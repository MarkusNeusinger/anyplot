"""anyplot.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: plotly 7.1.0 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-27
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import sample_colorscale


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome (Imprint palette)
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint continuous ramp (marks stops) for colors on the page; arrows are colored by wavelength on it
SEQ_MARKS = (
    [[0.0, "#009E73"], [0.687, "#024582"], [1.0, "#351E45"]]
    if THEME == "light"
    else [[0.0, "#6F7E20"], [0.21, "#009E73"], [1.0, "#CDD9FF"]]
)

# Constants
HC_EV_NM = 1239.84  # photon energy times wavelength, eV·nm
IONIZATION = 0.0  # energy of the ionization limit (n → ∞), eV
CROWDED = 0.08  # levels within this share of the ground-state depth of the limit are labelled together
GREEK = "αβγδ"
# Spectral series of hydrogen: name, region, label prefix, lower level, upper levels,
# schematic x of the series center
SERIES = [
    ("Lyman", "Ultraviolet", "Ly-", 1, [2, 3, 4], 0.27),
    ("Balmer", "Visible", "H", 2, [3, 4, 5, 6], 0.52),
    ("Paschen", "Infrared", "Pa-", 3, [4, 5], 0.77),
]
ARROW_SPACING = 0.06  # schematic horizontal gap between neighboring arrows of a series
LINE_LEFT, LINE_RIGHT = 0.14, 0.88  # schematic extent of each level line

# Columns: set these to your table's column names
LEVEL = "Level"  # role: level
ENERGY = "Energy (eV)"  # role: energy

# Data: hydrogen levels, E_n = -13.6 / n² eV; replace with your own table, one row per level from the ground state up
df = pd.DataFrame({LEVEL: [f"n = {n}" for n in range(1, 7)], ENERGY: [-13.6 / n**2 for n in range(1, 7)]})

# Plot: reads only df and the constants above
energies = dict(zip(range(1, len(df) + 1), df[ENERGY], strict=True))
levels = dict(zip(range(1, len(df) + 1), df[LEVEL], strict=True))
depth = IONIZATION - df[ENERGY].min()  # ground-state depth sets all vertical offsets
# Wavelength range of all transitions, for the color ramp (log scale: the series span a factor of 20)
wavelengths = [
    HC_EV_NM / (energies[u] - energies[lo])
    for _n, _r, _p, lo, ups, _c in SERIES
    for u in ups
    if u in energies and lo in energies
]
log_wl = np.log(wavelengths)
log_min, log_span = np.nanmin(log_wl), max(np.nanmax(log_wl) - np.nanmin(log_wl), 1e-9)
crowded = [n for n, e in energies.items() if e > IONIZATION - CROWDED * depth]
crowded_label = ", ".join(str(n) for n in crowded)

fig = go.Figure()

# Energy level lines
for n, energy in energies.items():
    fig.add_trace(
        go.Scatter(
            x=[LINE_LEFT, LINE_RIGHT],
            y=[energy, energy],
            mode="lines",
            line={"color": INK_SOFT, "width": 3},
            showlegend=False,
            hovertemplate=f"<b>{levels[n]}</b><br>E = {energy:.2f} eV<extra></extra>",
        )
    )

# Ionization limit: dashed muted line
fig.add_trace(
    go.Scatter(
        x=[LINE_LEFT - 0.04, LINE_RIGHT + 0.04],
        y=[IONIZATION, IONIZATION],
        mode="lines",
        line={"color": INK_MUTED, "width": 2, "dash": "dash"},
        showlegend=False,
        hovertemplate=f"<b>Ionization Limit</b><br>E = {IONIZATION:g} eV  (n → ∞)<extra></extra>",
    )
)

# Separated levels get their own labels on both sides; the crowded ones share one label above the limit
for n, energy in energies.items():
    if n in crowded:
        continue
    fig.add_annotation(
        x=LINE_RIGHT + 0.02,
        y=energy,
        text=f"<b>{levels[n]}</b>",
        showarrow=False,
        font={"size": 12, "color": INK_SOFT},
        xanchor="left",
        yanchor="middle",
    )
    fig.add_annotation(
        x=LINE_LEFT - 0.02,
        y=energy,
        text=f"<b>{energy:.2f}</b> eV",
        showarrow=False,
        font={"size": 12, "color": INK_MUTED},
        xanchor="right",
        yanchor="middle",
    )
fig.add_annotation(
    x=LINE_RIGHT + 0.02,
    y=IONIZATION,
    yshift=8,
    text=f"<b>n = {crowded_label}</b>",
    showarrow=False,
    font={"size": 11, "color": INK_SOFT},
    xanchor="left",
    yanchor="bottom",
)
fig.add_annotation(
    x=LINE_LEFT - 0.05,
    y=IONIZATION,
    text=f"<b>{IONIZATION:g}</b> eV",
    showarrow=False,
    font={"size": 12, "color": INK_MUTED},
    xanchor="right",
    yanchor="middle",
)
fig.add_annotation(
    x=LINE_RIGHT + 0.02,
    y=IONIZATION,
    yshift=-3,
    text="<i>Ionization limit</i>",
    showarrow=False,
    font={"size": 11, "color": INK_MUTED},
    xanchor="left",
    yanchor="top",
)

# Transitions: one downward emission arrow per upper level, each series in its own column of the diagram
hover = []
for name, _region, prefix, lower, uppers, center in SERIES:
    for k, upper in enumerate(uppers):
        if upper not in energies or lower not in energies:
            continue  # a table without these levels has no such transition
        x = center + (k - (len(uppers) - 1) / 2) * ARROW_SPACING
        e_up, e_low = energies[upper], energies[lower]
        gap = e_up - e_low
        wavelength = HC_EV_NM / gap
        color = sample_colorscale(SEQ_MARKS, np.nan_to_num((np.log(wavelength) - log_min) / log_span))[0]
        label = f"{prefix}{GREEK[k]} {wavelength:.0f} nm"
        gap_pad = min(0.015 * depth, 0.1 * gap)
        fig.add_annotation(
            x=x,
            y=e_low + gap_pad,
            ax=x,
            ay=e_up - gap_pad,
            xref="x",
            yref="y",
            axref="x",
            ayref="y",
            showarrow=True,
            arrowhead=2,
            arrowsize=min(0.6, 0.5 * gap),  # short gaps get a small head so a shaft shows
            arrowwidth=2.5,
            arrowcolor=color,
            text="",
        )
        mid = (e_up + e_low) / 2
        # Vertical labels keep neighboring arrows apart: Lyman labels run beside their arrow, the shorter series
        # hang in the empty space below the n=2 line, in the color of their arrow
        if lower == 1:
            lx, ly, anchor = x - 0.016, mid, "middle"
        else:
            lx, ly, anchor = x, energies[2] - 0.03 * depth, "top"
        fig.add_annotation(
            x=lx, y=ly, text=label, textangle=-90, showarrow=False, font={"size": 11, "color": color}, yanchor=anchor
        )
        hover.append((x, mid, name, upper, lower, wavelength, gap))

# Invisible hover targets at transition midpoints for HTML interactivity
for name, *_ in SERIES:
    rows = [h for h in hover if h[2] == name]
    fig.add_trace(
        go.Scatter(
            x=[h[0] for h in rows],
            y=[h[1] for h in rows],
            mode="markers",
            marker={"size": 30, "opacity": 0},
            showlegend=False,
            hovertext=[
                f"<b>{name} Series</b><br>n={h[3]} → n={h[4]}<br>λ = {h[5]:.1f} nm<br>ΔE = {h[6]:.2f} eV" for h in rows
            ],
            hoverinfo="text",
        )
    )

# Series group headers above the limit
for name, region, _prefix, _lower, _uppers, center in SERIES:
    fig.add_annotation(
        x=center,
        y=0.115 * depth,
        text=f"<b>{name}</b><br><i>{region}</i>",
        showarrow=False,
        font={"size": 13, "color": INK},
    )

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "energy-level-atomic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"visible": False, "range": [0, 1], "fixedrange": True},
    yaxis={
        "title": {"text": ENERGY, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [IONIZATION - 1.04 * depth, IONIZATION + 0.18 * depth],
        "zeroline": False,
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 120, "r": 140, "t": 80, "b": 60},
    showlegend=False,
)

# Save: canonical 3200×1800 landscape canvas
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

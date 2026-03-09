""" pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: plotly 6.6.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-09
"""

import numpy as np
import plotly.graph_objects as go


# Data - synthetic 1H NMR spectrum of ethanol
np.random.seed(42)
chemical_shift = np.linspace(0, 12, 6000)


def _peak(center, width, height):
    return height * np.exp(-((chemical_shift - center) ** 2) / (2 * width**2))


# TMS reference peak at 0 ppm
intensity = _peak(0.0, 0.012, 0.4)

# CH3 triplet near 1.2 ppm (3 peaks, 1:2:1 ratio)
triplet_spacing = 0.07
intensity += _peak(1.18 - triplet_spacing, 0.012, 0.55)
intensity += _peak(1.18, 0.012, 1.1)
intensity += _peak(1.18 + triplet_spacing, 0.012, 0.55)

# OH singlet near 2.6 ppm
intensity += _peak(2.61, 0.015, 0.35)

# CH2 quartet near 3.7 ppm (4 peaks, 1:3:3:1 ratio)
quartet_spacing = 0.07
intensity += _peak(3.69 - 1.5 * quartet_spacing, 0.012, 0.25)
intensity += _peak(3.69 - 0.5 * quartet_spacing, 0.012, 0.75)
intensity += _peak(3.69 + 0.5 * quartet_spacing, 0.012, 0.75)
intensity += _peak(3.69 + 1.5 * quartet_spacing, 0.012, 0.25)

# Add subtle baseline noise
intensity += np.random.normal(0, 0.003, len(chemical_shift))
intensity = np.clip(intensity, 0, None)

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=chemical_shift,
        y=intensity,
        mode="lines",
        line={"color": "#306998", "width": 2},
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.08)",
        hovertemplate="δ %{x:.2f} ppm<br>Intensity: %{y:.3f}<extra></extra>",
    )
)

# Annotations for key peaks
annotations = [
    {"x": 0.0, "y": 0.42, "text": "TMS<br>0.00 ppm", "showarrow": True, "arrowhead": 2},
    {"x": 1.18, "y": 1.13, "text": "CH₃ (triplet)<br>1.18 ppm", "showarrow": True, "arrowhead": 2},
    {"x": 2.61, "y": 0.38, "text": "OH (singlet)<br>2.61 ppm", "showarrow": True, "arrowhead": 2},
    {"x": 3.69, "y": 0.78, "text": "CH₂ (quartet)<br>3.69 ppm", "showarrow": True, "arrowhead": 2},
]

for ann in annotations:
    ann.update(
        font={"size": 16, "color": "#333333"},
        arrowcolor="#666666",
        arrowwidth=1.5,
        ax=0,
        ay=-50,
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="#cccccc",
        borderwidth=1,
        borderpad=4,
    )

# Style
fig.update_layout(
    title={"text": "Ethanol ¹H NMR · spectrum-nmr · plotly · pyplots.ai", "font": {"size": 28}},
    xaxis={
        "title": {"text": "Chemical Shift δ (ppm)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "autorange": "reversed",
        "range": [12, -0.5],
        "showgrid": False,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Intensity (a.u.)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.08)",
        "gridwidth": 1,
        "zeroline": True,
        "zerolinecolor": "rgba(0,0,0,0.15)",
        "zerolinewidth": 1,
    },
    template="plotly_white",
    annotations=annotations,
    showlegend=False,
    plot_bgcolor="white",
    margin={"l": 80, "r": 40, "t": 80, "b": 80},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")

""" pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: plotly 6.6.0 | Python 3.14.3
Quality: 93/100 | Created: 2026-03-09
"""

import numpy as np
import plotly.graph_objects as go


# Data - synthetic 1H NMR spectrum of ethanol
np.random.seed(42)
chemical_shift = np.linspace(-0.5, 5.0, 6000)
w = 0.012  # peak width (standard deviation)

# TMS reference peak at 0 ppm
intensity = 0.4 * np.exp(-((chemical_shift - 0.0) ** 2) / (2 * w**2))

# CH3 triplet near 1.2 ppm (3 peaks, 1:2:1 ratio)
intensity += 0.55 * np.exp(-((chemical_shift - 1.11) ** 2) / (2 * w**2))
intensity += 1.10 * np.exp(-((chemical_shift - 1.18) ** 2) / (2 * w**2))
intensity += 0.55 * np.exp(-((chemical_shift - 1.25) ** 2) / (2 * w**2))

# OH singlet near 2.6 ppm
intensity += 0.35 * np.exp(-((chemical_shift - 2.61) ** 2) / (2 * 0.015**2))

# CH2 quartet near 3.7 ppm (4 peaks, 1:3:3:1 ratio)
intensity += 0.25 * np.exp(-((chemical_shift - 3.585) ** 2) / (2 * w**2))
intensity += 0.75 * np.exp(-((chemical_shift - 3.655) ** 2) / (2 * w**2))
intensity += 0.75 * np.exp(-((chemical_shift - 3.725) ** 2) / (2 * w**2))
intensity += 0.25 * np.exp(-((chemical_shift - 3.795) ** 2) / (2 * w**2))

# Add subtle baseline noise
intensity += np.random.normal(0, 0.003, len(chemical_shift))
intensity = np.clip(intensity, 0, None)

# Peak group regions for subtle colored shading (tight around peaks)
peak_regions = [
    {"x0": -0.05, "x1": 0.05, "color": "rgba(76, 175, 80, 0.06)"},
    {"x0": 1.05, "x1": 1.32, "color": "rgba(48, 105, 152, 0.06)"},
    {"x0": 2.53, "x1": 2.69, "color": "rgba(156, 39, 176, 0.06)"},
    {"x0": 3.55, "x1": 3.84, "color": "rgba(255, 152, 0, 0.06)"},
]

# Plot
fig = go.Figure()

# Main spectrum trace
fig.add_trace(
    go.Scatter(
        x=chemical_shift,
        y=intensity,
        mode="lines",
        line={"color": "#306998", "width": 2.5, "shape": "spline"},
        fill="tozeroy",
        fillcolor="rgba(48, 105, 152, 0.06)",
        hovertemplate="δ %{x:.2f} ppm<br>Intensity: %{y:.3f}<extra></extra>",
        name="¹H NMR",
    )
)

# Colored region shading using Plotly shapes
shapes = []
for region in peak_regions:
    shapes.append(
        {
            "type": "rect",
            "xref": "x",
            "yref": "paper",
            "x0": region["x0"],
            "x1": region["x1"],
            "y0": 0,
            "y1": 1,
            "fillcolor": region["color"],
            "line": {"width": 0},
            "layer": "below",
        }
    )

# Accent colors for annotations matching region shading
accent_colors = {
    "TMS": {"border": "#4CAF50", "arrow": "#4CAF50", "bg": "rgba(76, 175, 80, 0.12)"},
    "CH₃": {"border": "#306998", "arrow": "#306998", "bg": "rgba(48, 105, 152, 0.12)"},
    "OH": {"border": "#9C27B0", "arrow": "#9C27B0", "bg": "rgba(156, 39, 176, 0.12)"},
    "CH₂": {"border": "#FF9800", "arrow": "#FF9800", "bg": "rgba(255, 152, 0, 0.12)"},
}

# Annotations for key peaks with color-coded styling
annotations = [
    {"x": 0.0, "y": 0.42, "text": "<b>TMS</b><br><i>δ</i> 0.00", "key": "TMS", "ay": -55},
    {"x": 1.18, "y": 1.13, "text": "<b>CH₃</b> triplet<br><i>δ</i> 1.18", "key": "CH₃", "ay": -50},
    {"x": 2.61, "y": 0.38, "text": "<b>OH</b> singlet<br><i>δ</i> 2.61", "key": "OH", "ay": -55},
    {"x": 3.69, "y": 0.78, "text": "<b>CH₂</b> quartet<br><i>δ</i> 3.69", "key": "CH₂", "ay": -50},
]

styled_annotations = []
for ann in annotations:
    accent = accent_colors[ann["key"]]
    styled_annotations.append(
        {
            "x": ann["x"],
            "y": ann["y"],
            "text": ann["text"],
            "showarrow": True,
            "arrowhead": 3,
            "arrowsize": 1.2,
            "arrowwidth": 2,
            "arrowcolor": accent["arrow"],
            "font": {"size": 16, "color": "#1a1a1a", "family": "Arial, sans-serif"},
            "ax": 0,
            "ay": ann["ay"],
            "bgcolor": accent["bg"],
            "bordercolor": accent["border"],
            "borderwidth": 1.5,
            "borderpad": 5,
        }
    )

# Layout with refined styling
fig.update_layout(
    title={
        "text": "Ethanol ¹H NMR · spectrum-nmr · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#1a1a1a", "family": "Arial Black, Arial, sans-serif"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {
            "text": "Chemical Shift <i>δ</i> (ppm)",
            "font": {"size": 22, "family": "Arial, sans-serif"},
            "standoff": 12,
        },
        "tickfont": {"size": 18, "family": "Arial, sans-serif"},
        "autorange": "reversed",
        "range": [5.0, -0.5],
        "dtick": 0.5,
        "showgrid": False,
        "zeroline": False,
        "showline": True,
        "linecolor": "#333333",
        "linewidth": 1.5,
        "ticks": "outside",
        "ticklen": 8,
        "tickwidth": 1.5,
        "tickcolor": "#333333",
        "minor": {"dtick": 0.1, "ticks": "outside", "ticklen": 4, "tickcolor": "#999999"},
        "spikemode": "across",
        "spikethickness": 1,
        "spikecolor": "#999999",
        "spikedash": "dot",
    },
    yaxis={
        "title": {"text": "Intensity (a.u.)", "font": {"size": 22, "family": "Arial, sans-serif"}, "standoff": 8},
        "tickfont": {"size": 18, "family": "Arial, sans-serif"},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "griddash": "dot",
        "zeroline": True,
        "zerolinecolor": "#333333",
        "zerolinewidth": 1.5,
        "showline": True,
        "linecolor": "#333333",
        "linewidth": 1.5,
        "ticks": "outside",
        "ticklen": 8,
        "tickwidth": 1.5,
        "tickcolor": "#333333",
        "rangemode": "tozero",
    },
    template="plotly_white",
    annotations=styled_annotations,
    shapes=shapes,
    showlegend=False,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"l": 90, "r": 30, "t": 80, "b": 80},
    hoverlabel={"bgcolor": "white", "bordercolor": "#306998", "font": {"size": 14, "family": "Arial, sans-serif"}},
    hovermode="x unified",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")

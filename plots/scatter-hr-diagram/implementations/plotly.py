""" pyplots.ai
scatter-hr-diagram: Hertzsprung-Russell Diagram
Library: plotly 6.6.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-07
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)

# Spectral type temperature ranges and colors (distinct, accessible palette)
spectral_config = {
    "O": {"temp": (30000, 40000), "color": "#2B3990", "n": 15},
    "B": {"temp": (10000, 30000), "color": "#5B8BD6", "n": 40},
    "A": {"temp": (7500, 10000), "color": "#A8D8EA", "n": 45},
    "F": {"temp": (6000, 7500), "color": "#F5E66B", "n": 50},
    "G": {"temp": (5200, 6000), "color": "#F5C040", "n": 55},
    "K": {"temp": (3700, 5200), "color": "#E8872B", "n": 50},
    "M": {"temp": (2400, 3700), "color": "#C83C2C", "n": 45},
}

# Temperature thresholds for spectral classification lookup
temp_thresholds = [(30000, "O"), (10000, "B"), (7500, "A"), (6000, "F"), (5200, "G"), (3700, "K")]


def classify_temps(temps):
    """Classify temperatures into spectral types."""
    return [next((s for thresh, s in temp_thresholds if t > thresh), "M") for t in temps]


temperatures = []
luminosities = []
spectral_types = []
regions = []

# Main sequence stars (L ~ T^4 relationship with scatter)
for stype, cfg in spectral_config.items():
    n = cfg["n"]
    temp = np.random.uniform(cfg["temp"][0], cfg["temp"][1], n)
    log_lum_base = 4.0 * np.log10(temp / 5778)
    log_lum = log_lum_base + np.random.normal(0, 0.3, n)
    temperatures.extend(temp)
    luminosities.extend(10**log_lum)
    spectral_types.extend([stype] * n)
    regions.extend(["Main Sequence"] * n)

# Red giants (cool but bright)
n_rg = 35
rg_temp = np.random.uniform(3000, 5200, n_rg)
rg_lum = 10 ** np.random.uniform(1.5, 3.5, n_rg)
temperatures.extend(rg_temp)
luminosities.extend(rg_lum)
spectral_types.extend(np.where(rg_temp > 3700, "K", "M").tolist())
regions.extend(["Red Giants"] * n_rg)

# Supergiants (bright across temperatures)
n_sg = 20
sg_temp = np.random.uniform(3500, 30000, n_sg)
sg_lum = 10 ** np.random.uniform(4.0, 5.8, n_sg)
temperatures.extend(sg_temp)
luminosities.extend(sg_lum)
spectral_types.extend(classify_temps(sg_temp))
regions.extend(["Supergiants"] * n_sg)

# White dwarfs (hot but dim)
n_wd = 30
wd_temp = np.random.uniform(7000, 30000, n_wd)
wd_lum = 10 ** np.random.uniform(-4, -1.5, n_wd)
temperatures.extend(wd_temp)
luminosities.extend(wd_lum)
spectral_types.extend(classify_temps(wd_temp))
regions.extend(["White Dwarfs"] * n_wd)

temperatures = np.array(temperatures)
luminosities = np.array(luminosities)
spectral_types = np.array(spectral_types)
regions = np.array(regions)

# Derive color map from config
spectral_colors = {k: v["color"] for k, v in spectral_config.items()}

# Plot
fig = go.Figure()

spectral_order = ["O", "B", "A", "F", "G", "K", "M"]
for stype in spectral_order:
    mask = spectral_types == stype
    fig.add_trace(
        go.Scatter(
            x=temperatures[mask],
            y=luminosities[mask],
            mode="markers",
            name=stype,
            marker={
                "size": 11,
                "color": spectral_colors[stype],
                "line": {"width": 0.5, "color": "#333333"},
                "opacity": 0.75,
            },
            hovertemplate=(
                f"Spectral Type: {stype}<br>Temperature: %{{x:,.0f}} K<br>Luminosity: %{{y:.4g}} L☉<br><extra></extra>"
            ),
        )
    )

# Sun reference point
fig.add_trace(
    go.Scatter(
        x=[5778],
        y=[1.0],
        mode="markers",
        name="☉ Sun",
        marker={"size": 22, "color": "#FDB813", "line": {"width": 2, "color": "#B8860B"}, "symbol": "star"},
        hovertemplate="The Sun<br>Temperature: 5,778 K<br>Luminosity: 1.0 L☉<br><extra></extra>",
    )
)

# Sun label annotation with arrow
fig.add_annotation(
    x=np.log10(5778),
    y=np.log10(1.0),
    xref="x",
    yref="y",
    text="<b>☉ Sun</b>",
    showarrow=True,
    arrowhead=0,
    arrowwidth=1.5,
    arrowcolor="#B8860B",
    ax=-55,
    ay=-40,
    font={"size": 18, "color": "#B8860B"},
    bgcolor="rgba(255,255,255,0.9)",
    borderpad=4,
)

# Region annotations with styled labels
region_labels = {
    "Main Sequence": {"x": 15000, "y": 50, "ax": -80, "ay": -40},
    "Red Giants": {"x": 3800, "y": 800, "ax": -60, "ay": -40},
    "Supergiants": {"x": 10000, "y": 200000, "ax": 60, "ay": 40},
    "White Dwarfs": {"x": 15000, "y": 0.0003, "ax": 60, "ay": 40},
}

for label, pos in region_labels.items():
    fig.add_annotation(
        x=np.log10(pos["x"]),
        y=np.log10(pos["y"]),
        xref="x",
        yref="y",
        text=f"<b>{label}</b>",
        showarrow=False,
        font={"size": 18, "color": "#333333"},
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="rgba(0,0,0,0.1)",
        borderwidth=1,
        borderpad=6,
    )

# Secondary x-axis with spectral class labels
spectral_temps = {"O": 35000, "B": 20000, "A": 8750, "F": 6750, "G": 5600, "K": 4450, "M": 3050}

# Empty trace to activate xaxis2
fig.add_trace(go.Scatter(x=[], y=[], xaxis="x2", showlegend=False, hoverinfo="skip"))

# Layout
fig.update_layout(
    title={
        "text": "scatter-hr-diagram · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#222222"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Surface Temperature (K)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "type": "log",
        "autorange": "reversed",
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "#333333",
        "linewidth": 1,
        "tickvals": [2500, 5000, 10000, 20000, 40000],
        "ticktext": ["2,500", "5,000", "10,000", "20,000", "40,000"],
    },
    yaxis={
        "title": {"text": "Luminosity (L☉)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "type": "log",
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "showline": True,
        "linecolor": "#333333",
        "linewidth": 1,
    },
    xaxis2={
        "tickfont": {"size": 18, "color": "#444444"},
        "overlaying": "x",
        "side": "top",
        "type": "log",
        "range": [np.log10(45000), np.log10(2000)],
        "tickvals": list(spectral_temps.values()),
        "ticktext": list(spectral_temps.keys()),
        "showgrid": False,
        "showline": True,
        "linecolor": "#333333",
        "linewidth": 1,
        "matches": "x",
    },
    template="plotly_white",
    plot_bgcolor="#FAFAFA",
    paper_bgcolor="#FFFFFF",
    legend={
        "title": {"text": "Spectral Type", "font": {"size": 18}},
        "font": {"size": 16},
        "bgcolor": "rgba(255,255,255,0.92)",
        "bordercolor": "rgba(0,0,0,0.15)",
        "borderwidth": 1,
        "x": 0.98,
        "y": 0.02,
        "xanchor": "right",
        "yanchor": "bottom",
    },
    width=1600,
    height=900,
    margin={"l": 80, "r": 60, "t": 100, "b": 80},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")

""" pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: plotly 6.6.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-15
"""

import numpy as np
import plotly.graph_objects as go


# Data - synthetic annual hourly load profile for a mid-sized utility
np.random.seed(42)
hours = np.arange(8760)

# Build realistic load profile: base + daily cycle + seasonal + noise
hour_of_day = hours % 24
day_of_year = hours // 24

base_load = 400
seasonal = 200 * np.sin(2 * np.pi * (day_of_year - 30) / 365)
daily_cycle = 250 * np.sin(2 * np.pi * (hour_of_day - 6) / 24) + 150 * np.sin(4 * np.pi * (hour_of_day - 6) / 24)
peak_factor = np.where(
    (day_of_year > 150) & (day_of_year < 250) & (hour_of_day > 12) & (hour_of_day < 18),
    np.random.uniform(100, 300, 8760),
    0,
)
noise = np.random.normal(0, 30, 8760)

load_raw = base_load + seasonal + daily_cycle + peak_factor + noise + 400
load_mw = np.sort(load_raw)[::-1]
load_mw = np.clip(load_mw, 350, 1250)

# Capacity tier thresholds
base_capacity = 550
intermediate_capacity = 900
peak_capacity = 1150

# Find hour indices where load crosses thresholds
peak_hours = np.searchsorted(-load_mw, -peak_capacity)
intermediate_hours = np.searchsorted(-load_mw, -intermediate_capacity)
base_hours = np.searchsorted(-load_mw, -base_capacity)

# Total energy (area under curve) in GWh
total_energy_gwh = np.trapezoid(load_mw) / 1000

# Color palette (colorblind-safe: red→magenta, orange→teal for deuteranopia distinction)
color_peak = "#C44E93"
color_intermediate = "#2A9D8F"
color_base = "#306998"
color_line = "#1A3A5C"

# Plot
fig = go.Figure()

# Base load region (rightmost)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([hours, hours[::-1]]),
        y=np.concatenate([np.minimum(load_mw, base_capacity), np.zeros(8760)]),
        fill="toself",
        fillcolor="rgba(48, 105, 152, 0.3)",
        line={"width": 0},
        name="Base Load",
        showlegend=True,
        hoverinfo="skip",
    )
)

# Intermediate load region (middle, between base and intermediate capacity)
intermediate_top = np.clip(load_mw, base_capacity, intermediate_capacity)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([hours, hours[::-1]]),
        y=np.concatenate([intermediate_top, np.full(8760, base_capacity)]),
        fill="toself",
        fillcolor="rgba(42, 157, 143, 0.25)",
        line={"width": 0},
        name="Intermediate Load",
        showlegend=True,
        hoverinfo="skip",
    )
)

# Peak load region (leftmost, only where load exceeds intermediate capacity)
peak_top = np.maximum(load_mw, intermediate_capacity)
fig.add_trace(
    go.Scatter(
        x=np.concatenate([hours, hours[::-1]]),
        y=np.concatenate([peak_top, np.full(8760, intermediate_capacity)]),
        fill="toself",
        fillcolor="rgba(196, 78, 147, 0.25)",
        line={"width": 0},
        name="Peak Load",
        showlegend=True,
        hoverinfo="skip",
    )
)

# Main load duration curve
fig.add_trace(
    go.Scatter(
        x=hours,
        y=load_mw,
        mode="lines",
        line={"color": color_line, "width": 3},
        name="Load Duration Curve",
        hovertemplate="<b>Hour %{x:,}</b><br>Load: %{y:.0f} MW<extra></extra>",
    )
)

# Horizontal dashed lines for capacity tiers (annotations on left to avoid right-edge clipping)
for capacity, label, color in [
    (peak_capacity, f"Peak Capacity ({peak_capacity} MW)", color_peak),
    (intermediate_capacity, f"Intermediate Capacity ({intermediate_capacity} MW)", color_intermediate),
    (base_capacity, f"Base Capacity ({base_capacity} MW)", color_base),
]:
    fig.add_hline(
        y=capacity,
        line_dash="dash",
        line_color=color,
        line_width=2,
        annotation_text=label,
        annotation_position="top left",
        annotation_font={"size": 16, "color": color},
    )

# Region labels
fig.add_annotation(
    x=peak_hours // 2 + 200,
    y=(peak_capacity + intermediate_capacity) // 2 + 50,
    text="<b>Peak</b>",
    showarrow=False,
    font={"size": 18, "color": color_peak},
)

fig.add_annotation(
    x=(peak_hours + intermediate_hours) // 2,
    y=(intermediate_capacity + base_capacity) // 2 + 60,
    text="<b>Intermediate</b>",
    showarrow=False,
    font={"size": 18, "color": color_intermediate},
)

fig.add_annotation(
    x=6500, y=base_capacity // 2 + 50, text="<b>Base Load</b>", showarrow=False, font={"size": 18, "color": color_base}
)

# Total energy annotation (positioned in base load region to avoid overlap with capacity lines)
fig.add_annotation(
    x=6000,
    y=750,
    text=f"Total Energy: {total_energy_gwh:,.0f} GWh/year",
    showarrow=False,
    font={"size": 18, "color": "#333333"},
    bordercolor="#999999",
    borderwidth=1.5,
    borderpad=6,
    bgcolor="rgba(255, 255, 255, 0.85)",
)

# Layout
fig.update_layout(
    title={"text": "line-load-duration · plotly · pyplots.ai", "font": {"size": 28}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Hours (ranked by load, descending)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": False,
        "range": [0, 8760],
        "tickvals": [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 8760],
        "ticktext": ["0", "1,000", "2,000", "3,000", "4,000", "5,000", "6,000", "7,000", "8,000", "8,760"],
    },
    yaxis={
        "title": {"text": "Power Demand (MW)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0, 0, 0, 0.08)",
        "range": [0, 1350],
    },
    template="plotly_white",
    showlegend=True,
    legend={
        "x": 0.75,
        "y": 0.45,
        "font": {"size": 16},
        "bgcolor": "rgba(255, 255, 255, 0.85)",
        "bordercolor": "rgba(0, 0, 0, 0.1)",
        "borderwidth": 1,
    },
    margin={"l": 80, "r": 60, "t": 80, "b": 60},
    hovermode="x",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")

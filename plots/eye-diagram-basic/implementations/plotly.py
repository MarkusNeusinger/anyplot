"""pyplots.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: plotly 6.6.0 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-17
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)

n_traces = 400
samples_per_ui = 150
n_ui = 2
total_samples = n_ui * samples_per_ui

# Time axis normalized to unit intervals
time = np.linspace(0, n_ui, total_samples)

# Generate random NRZ bit sequences (4 bits to cover 2 UI with transitions)
n_bits = 4
bit_sequences = np.random.randint(0, 2, size=(n_traces, n_bits))

# Build smooth NRZ waveforms with raised-cosine transitions (vectorized)
rolloff = 0.15  # Transition sharpness (fraction of UI)
noise_sigma = 0.05  # 5% of amplitude
jitter_sigma = 0.03  # 3% of UI

# Vectorized signal generation across all traces
jitter = np.random.normal(0, jitter_sigma, (n_traces, n_bits))

# Broadcast time across traces: shape (n_traces, total_samples)
time_broadcast = np.broadcast_to(time, (n_traces, total_samples))

# Start from first bit level
voltage = np.full((n_traces, total_samples), bit_sequences[:, 0:1], dtype=float)

# Apply transitions for each bit boundary using vectorized tanh
for b in range(1, n_bits):
    transition_time = (b - 1.0) + jitter[:, b : b + 1]  # shape (n_traces, 1)
    transition = 0.5 * (1 + np.tanh((time_broadcast - transition_time) / rolloff))
    voltage = voltage * (1 - transition) + bit_sequences[:, b : b + 1] * transition

# Add Gaussian noise
voltage += np.random.normal(0, noise_sigma, voltage.shape)

# Flatten for histogram
all_time = np.tile(time, n_traces)
all_voltage = voltage.ravel()

# Compute eye measurements for annotation
# Eye center is around t=0.5 UI and t=1.5 UI, voltage between 0 and 1
center_mask_1 = (all_time > 0.35) & (all_time < 0.65)
high_at_center = all_voltage[center_mask_1 & (all_voltage > 0.5)]
low_at_center = all_voltage[center_mask_1 & (all_voltage < 0.5)]
eye_height = np.mean(high_at_center) - np.mean(low_at_center)

# Plot - density heatmap using Histogram2d with higher resolution
fig = go.Figure(
    data=go.Histogram2d(
        x=all_time,
        y=all_voltage,
        nbinsx=500,
        nbinsy=350,
        colorscale=[
            [0.0, "#0d0d2b"],
            [0.02, "#110940"],
            [0.06, "#1a0a5e"],
            [0.12, "#2e0e7e"],
            [0.22, "#5015a8"],
            [0.35, "#8a1fad"],
            [0.5, "#c23a6e"],
            [0.65, "#e05535"],
            [0.8, "#f5a623"],
            [0.92, "#fce034"],
            [1.0, "#fef200"],
        ],
        colorbar={
            "title": {"text": "Trace<br>Density", "font": {"size": 18, "color": "#cccccc"}},
            "tickfont": {"size": 16, "color": "#aaaaaa"},
            "thickness": 15,
            "len": 0.7,
            "outlinewidth": 0,
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "y": 0.5,
        },
        hovertemplate="Time: %{x:.2f} UI<br>Voltage: %{y:.3f} V<br>Density: %{z}<extra></extra>",
    )
)

# Eye height annotation
fig.add_annotation(
    x=0.5,
    y=0.5,
    text=f"Eye Height: {eye_height:.2f} V",
    showarrow=False,
    font={"size": 17, "color": "#66ffcc", "family": "monospace"},
    bgcolor="rgba(13,13,43,0.75)",
    bordercolor="#66ffcc",
    borderwidth=1,
    borderpad=6,
)

# Eye height bracket lines
fig.add_shape(
    type="line",
    x0=0.5,
    x1=0.5,
    y0=np.mean(low_at_center),
    y1=np.mean(high_at_center),
    line={"color": "#66ffcc", "width": 2, "dash": "dot"},
)

# Layout
fig.update_layout(
    title={
        "text": "eye-diagram-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#e0e0e0"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
        "yanchor": "top",
    },
    xaxis={
        "title": {"text": "Time (UI)", "font": {"size": 22, "color": "#cccccc"}},
        "tickfont": {"size": 18, "color": "#aaaaaa"},
        "tickvals": [0, 0.5, 1.0, 1.5, 2.0],
        "gridcolor": "rgba(255,255,255,0.06)",
        "gridwidth": 1,
        "zeroline": False,
        "showline": True,
        "linecolor": "rgba(255,255,255,0.15)",
        "linewidth": 1,
        "mirror": True,
    },
    yaxis={
        "title": {"text": "Voltage (V)", "font": {"size": 22, "color": "#cccccc"}},
        "tickfont": {"size": 18, "color": "#aaaaaa"},
        "gridcolor": "rgba(255,255,255,0.06)",
        "gridwidth": 1,
        "zeroline": False,
        "showline": True,
        "linecolor": "rgba(255,255,255,0.15)",
        "linewidth": 1,
        "mirror": True,
    },
    template="plotly_dark",
    paper_bgcolor="#0d0d2b",
    plot_bgcolor="#0d0d2b",
    margin={"l": 80, "r": 60, "t": 80, "b": 65},
    width=1600,
    height=900,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")

""" anyplot.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: plotly 6.8.0 | Python 3.13.14
Quality: 85/100 | Updated: 2026-06-18
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint sequential colorscale for density — page bg (zero density) → green → blue
imprint_seq = [[0.0, PAGE_BG], [0.35, "#009E73"], [1.0, "#4467A3"]]

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
rolloff = 0.15  # transition sharpness (fraction of UI)
noise_sigma = 0.05  # 5% of amplitude
jitter_sigma = 0.03  # 3% of UI

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

all_time = np.tile(time, n_traces)
all_voltage = voltage.ravel()

# Compute eye height at first eye center (t ≈ 0.5 UI)
center_mask = (all_time > 0.35) & (all_time < 0.65)
high_at_center = all_voltage[center_mask & (all_voltage > 0.5)]
low_at_center = all_voltage[center_mask & (all_voltage < 0.5)]
eye_height = np.mean(high_at_center) - np.mean(low_at_center)

# Plot — density heatmap with smoothing to reduce graininess
fig = go.Figure(
    data=go.Histogram2d(
        x=all_time,
        y=all_voltage,
        nbinsx=500,
        nbinsy=350,
        zsmooth="best",
        colorscale=imprint_seq,
        colorbar={
            "title": {"text": "Trace<br>Density", "font": {"size": 12, "color": INK_SOFT}},
            "tickfont": {"size": 10, "color": INK_SOFT},
            "thickness": 14,
            "len": 0.7,
            "outlinewidth": 0,
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "y": 0.5,
        },
        hovertemplate="Time: %{x:.2f} UI<br>Voltage: %{y:.3f} V<br>Density: %{z}<extra></extra>",
    )
)

# Eye height annotation — uses brand green for visibility on both themes
ACCENT = "#009E73"

fig.add_annotation(
    x=0.5,
    y=0.5,
    text=f"Eye Height: {eye_height:.2f} V",
    showarrow=False,
    font={"size": 11, "color": ACCENT, "family": "monospace"},
    bgcolor=ELEVATED_BG,
    bordercolor=ACCENT,
    borderwidth=1,
    borderpad=6,
)

# Bracket line marking the eye height span
fig.add_shape(
    type="line",
    x0=0.5,
    x1=0.5,
    y0=float(np.mean(low_at_center)),
    y1=float(np.mean(high_at_center)),
    line={"color": ACCENT, "width": 2, "dash": "dot"},
)

# Title — 48 chars, below 67-char baseline so no fontsize shrinkage needed
title = "eye-diagram-basic · python · plotly · anyplot.ai"

fig.update_layout(
    autosize=False,
    title={
        "text": title,
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
        "yanchor": "top",
    },
    xaxis={
        "title": {"text": "Time (UI)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickvals": [0, 0.5, 1.0, 1.5, 2.0],
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "linewidth": 1,
        "mirror": False,
    },
    yaxis={
        "title": {"text": "Voltage (V)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "zeroline": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "linewidth": 1,
        "mirror": False,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={"bgcolor": ELEVATED_BG, "bordercolor": INK_SOFT, "borderwidth": 1, "font": {"color": INK_SOFT}},
    margin={"l": 80, "r": 60, "t": 80, "b": 65},
)

# Save — landscape 3200×1800 (800×450 scale=4)
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")

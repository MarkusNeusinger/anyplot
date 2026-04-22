""" pyplots.ai
ecg-twelve-lead: ECG/EKG 12-Lead Waveform Display
Library: plotly 6.6.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-19
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data - Synthetic ECG generation using a simplified mathematical model
np.random.seed(42)

sampling_rate = 1000
duration = 2.5
t = np.linspace(0, duration, int(sampling_rate * duration))

# Generate Lead II base signal inline (KISS - no helper functions)
beat_interval = 0.8
lead_II_signal = np.zeros_like(t)
for beat_start in np.arange(0, duration, beat_interval):
    t_shifted = t - beat_start
    mask = (t_shifted >= 0) & (t_shifted < beat_interval)
    tb = t_shifted[mask]
    lead_II_signal[mask] += (
        0.15 * np.exp(-((tb - 0.12) ** 2) / (2 * 0.035**2))  # P wave
        + (-0.12) * np.exp(-((tb - 0.20) ** 2) / (2 * 0.012**2))  # Q wave
        + 1.2 * np.exp(-((tb - 0.23) ** 2) / (2 * 0.012**2))  # R wave
        + (-0.25) * np.exp(-((tb - 0.26) ** 2) / (2 * 0.012**2))  # S wave
        + 0.3 * np.exp(-((tb - 0.38) ** 2) / (2 * 0.045**2))  # T wave
    )

lead_II_signal += np.random.normal(0, 0.005, len(t))

# Lead transforms for deriving all 12 leads from Lead II
lead_transforms = {
    "I": {"scale": 0.65, "t_inv": False},
    "II": {"scale": 1.0, "t_inv": False},
    "III": {"scale": 0.45, "t_inv": False},
    "aVR": {"scale": 0.75, "t_inv": True},
    "aVL": {"scale": 0.35, "t_inv": False},
    "aVF": {"scale": 0.70, "t_inv": False},
    "V1": {"scale": 0.55, "r_ratio": -0.6},
    "V2": {"scale": 0.80, "r_ratio": -0.3},
    "V3": {"scale": 0.95, "r_ratio": 0.3},
    "V4": {"scale": 1.10, "r_ratio": 0.7},
    "V5": {"scale": 0.90, "r_ratio": 0.9},
    "V6": {"scale": 0.70, "r_ratio": 1.0},
}

leads = {}
for name, params in lead_transforms.items():
    signal = lead_II_signal * params["scale"]
    if params.get("t_inv"):
        signal = -signal
    if "r_ratio" in params:
        r_ratio = params["r_ratio"]
        for beat_start in np.arange(0, duration, beat_interval):
            t_shifted = t - beat_start
            mask = (t_shifted >= 0.19) & (t_shifted < 0.27)
            r_component = 1.2 * np.exp(-((t_shifted - 0.23) ** 2) / (2 * 0.012**2)) * params["scale"]
            if r_ratio < 0:
                signal[mask] += r_component[mask] * abs(r_ratio) * 0.5
                s_extra = (-0.8) * np.exp(-((t_shifted - 0.24) ** 2) / (2 * 0.015**2)) * params["scale"]
                signal[mask] += s_extra[mask] * abs(r_ratio)
    leads[name] = signal

# Clinical 3x4 grid layout + rhythm strip
grid_layout = [["I", "aVR", "V1", "V4"], ["II", "aVL", "V2", "V5"], ["III", "aVF", "V3", "V6"]]

# Plot
fig = make_subplots(
    rows=4,
    cols=4,
    specs=[[{}, {}, {}, {}], [{}, {}, {}, {}], [{}, {}, {}, {}], [{"colspan": 4}, None, None, None]],
    row_heights=[0.24, 0.24, 0.24, 0.28],
    vertical_spacing=0.06,
    horizontal_spacing=0.04,
    subplot_titles=[
        "I",
        "aVR",
        "V1",
        "V4",
        "II",
        "aVL",
        "V2",
        "V5",
        "III",
        "aVF",
        "V3",
        "V6",
        "Lead II (Rhythm Strip)",
    ],
)

ecg_paper_color = "#FFF5F0"
grid_color_light = "rgba(220, 160, 150, 0.25)"
grid_color_bold = "rgba(200, 120, 110, 0.45)"
signal_color = "#1A1A2E"

# Add ECG signal traces with custom hover data
for row_idx, row_leads in enumerate(grid_layout):
    for col_idx, lead_name in enumerate(row_leads):
        signal = leads[lead_name]
        fig.add_trace(
            go.Scatter(
                x=t,
                y=signal,
                mode="lines",
                line={"color": signal_color, "width": 2},
                showlegend=False,
                name=lead_name,
                hovertemplate=f"<b>{lead_name}</b><br>Time: %{{x:.3f}}s<br>Voltage: %{{y:.2f}}mV<extra></extra>",
            ),
            row=row_idx + 1,
            col=col_idx + 1,
        )

# Rhythm strip (Lead II, full length)
fig.add_trace(
    go.Scatter(
        x=t,
        y=leads["II"],
        mode="lines",
        line={"color": signal_color, "width": 2.5},
        showlegend=False,
        name="Lead II",
        hovertemplate="<b>Lead II</b><br>Time: %{x:.3f}s<br>Voltage: %{y:.2f}mV<extra></extra>",
    ),
    row=4,
    col=1,
)

# Calibration pulse (1mV) for each subplot
cal_t = np.array([0.0, 0.0, 0.02, 0.02, 0.04, 0.04])
cal_v = np.array([0.0, 1.0, 1.0, 0.0, 0.0, 0.0])
cal_t_offset = -0.08

for row_idx in range(3):
    for col_idx in range(4):
        fig.add_trace(
            go.Scatter(
                x=cal_t + cal_t_offset,
                y=cal_v,
                mode="lines",
                line={"color": signal_color, "width": 1.5},
                showlegend=False,
                hoverinfo="skip",
            ),
            row=row_idx + 1,
            col=col_idx + 1,
        )

fig.add_trace(
    go.Scatter(
        x=cal_t + cal_t_offset,
        y=cal_v,
        mode="lines",
        line={"color": signal_color, "width": 1.5},
        showlegend=False,
        hoverinfo="skip",
    ),
    row=4,
    col=1,
)

# Style - ECG paper grid and axes
for row_idx in range(1, 5):
    cols = [1, 2, 3, 4] if row_idx <= 3 else [1]
    for col_idx in cols:
        fig.update_xaxes(
            range=[-0.12, duration],
            dtick=0.2,
            minor={"dtick": 0.04, "gridcolor": grid_color_light, "gridwidth": 1, "showgrid": True},
            gridcolor=grid_color_bold,
            gridwidth=1,
            showgrid=True,
            zeroline=False,
            showticklabels=(row_idx == 4),
            tickfont={"size": 16},
            spikemode="across",
            spikethickness=1,
            spikecolor="rgba(100, 100, 100, 0.5)",
            row=row_idx,
            col=col_idx,
        )
        fig.update_yaxes(
            range=[-1.2, 1.8],
            dtick=0.5,
            minor={"dtick": 0.1, "gridcolor": grid_color_light, "gridwidth": 1, "showgrid": True},
            gridcolor=grid_color_bold,
            gridwidth=1,
            showgrid=True,
            zeroline=True,
            zerolinecolor="rgba(180, 100, 90, 0.4)",
            zerolinewidth=1,
            showticklabels=False,
            row=row_idx,
            col=col_idx,
        )

# Axis labels with proper font sizes
fig.update_yaxes(showticklabels=True, tickfont={"size": 16}, title_text="mV", title_font={"size": 22}, row=1, col=1)
fig.update_yaxes(showticklabels=True, tickfont={"size": 16}, title_text="mV", title_font={"size": 22}, row=4, col=1)
fig.update_xaxes(title_text="Time (s)", title_font={"size": 22}, tickfont={"size": 16}, row=4, col=1)

fig.update_layout(
    title={
        "text": "ecg-twelve-lead · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#333"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.98,
    },
    template="plotly_white",
    plot_bgcolor=ecg_paper_color,
    paper_bgcolor="#FFFFFF",
    showlegend=False,
    margin={"l": 80, "r": 40, "t": 110, "b": 60},
    height=900,
    width=1600,
    hoverlabel={"bgcolor": "white", "font_size": 16, "font_family": "Arial"},
    hovermode="closest",
)

# Subplot title styling
fig.update_annotations(font_size=20, font_color="#306998", font_family="Arial Black")

# Add heart rate annotation for clinical context
fig.add_annotation(
    text="<b>HR: 75 bpm</b>  |  Normal Sinus Rhythm",
    xref="paper",
    yref="paper",
    x=0.5,
    y=1.06,
    showarrow=False,
    font={"size": 16, "color": "#555", "family": "Arial"},
    xanchor="center",
    yanchor="bottom",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)

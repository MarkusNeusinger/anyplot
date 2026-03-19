"""pyplots.ai
ecg-twelve-lead: ECG/EKG 12-Lead Waveform Display
Library: plotly | Python 3.13
Quality: pending | Created: 2026-03-19
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Data - Synthetic ECG generation using a simplified mathematical model
np.random.seed(42)

sampling_rate = 1000
duration = 2.5
t = np.linspace(0, duration, int(sampling_rate * duration))


def _ecg_component(t_arr, center, width, amplitude):
    return amplitude * np.exp(-((t_arr - center) ** 2) / (2 * width**2))


def _generate_beat(t_beat):
    p_wave = _ecg_component(t_beat, 0.12, 0.035, 0.15)
    q_wave = _ecg_component(t_beat, 0.20, 0.012, -0.12)
    r_wave = _ecg_component(t_beat, 0.23, 0.012, 1.2)
    s_wave = _ecg_component(t_beat, 0.26, 0.012, -0.25)
    t_wave = _ecg_component(t_beat, 0.38, 0.045, 0.3)
    return p_wave + q_wave + r_wave + s_wave + t_wave


beat_interval = 0.8
lead_II_signal = np.zeros_like(t)
for beat_start in np.arange(0, duration, beat_interval):
    t_shifted = t - beat_start
    mask = (t_shifted >= 0) & (t_shifted < beat_interval)
    lead_II_signal[mask] += _generate_beat(t_shifted[mask])

lead_II_signal += np.random.normal(0, 0.005, len(t))

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
            r_component = _ecg_component(t_shifted, 0.23, 0.012, 1.2) * params["scale"]
            if r_ratio < 0:
                signal[mask] += r_component[mask] * abs(r_ratio) * 0.5
                s_extra = _ecg_component(t_shifted, 0.24, 0.015, -0.8) * params["scale"]
                signal[mask] += s_extra[mask] * abs(r_ratio)
    leads[name] = signal

# Clinical 3x4 grid layout + rhythm strip
grid_layout = [["I", "aVR", "V1", "V4"], ["II", "aVL", "V2", "V5"], ["III", "aVF", "V3", "V6"]]

# Plot
fig = make_subplots(
    rows=4,
    cols=4,
    specs=[[{}, {}, {}, {}], [{}, {}, {}, {}], [{}, {}, {}, {}], [{"colspan": 4}, None, None, None]],
    row_heights=[0.25, 0.25, 0.25, 0.25],
    vertical_spacing=0.04,
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
                hovertemplate=f"{lead_name}<br>Time: %{{x:.3f}}s<br>Voltage: %{{y:.2f}}mV<extra></extra>",
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
        line={"color": signal_color, "width": 2},
        showlegend=False,
        hovertemplate="Lead II<br>Time: %{x:.3f}s<br>Voltage: %{y:.2f}mV<extra></extra>",
    ),
    row=4,
    col=1,
)

# Add calibration pulse (1mV) to each subplot
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
        x_range = [-0.12, duration] if row_idx <= 3 else [-0.12, duration]
        fig.update_xaxes(
            range=x_range,
            dtick=0.2,
            minor={"dtick": 0.04, "gridcolor": grid_color_light, "gridwidth": 1, "showgrid": True},
            gridcolor=grid_color_bold,
            gridwidth=1,
            showgrid=True,
            zeroline=False,
            showticklabels=(row_idx == 4),
            tickfont={"size": 14},
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

fig.update_yaxes(showticklabels=True, tickfont={"size": 14}, title_text="mV", title_font={"size": 16}, row=1, col=1)
fig.update_yaxes(showticklabels=True, tickfont={"size": 14}, title_text="mV", title_font={"size": 16}, row=4, col=1)
fig.update_xaxes(title_text="Time (s)", title_font={"size": 16}, row=4, col=1)

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
    margin={"l": 70, "r": 40, "t": 80, "b": 60},
    height=1000,
    width=1600,
)

fig.update_annotations(font_size=18, font_color="#306998", font_family="Arial Black")

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)

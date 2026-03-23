""" pyplots.ai
ecg-twelve-lead: ECG/EKG 12-Lead Waveform Display
Library: altair 6.0.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-19
"""

import altair as alt
import numpy as np
import pandas as pd


# Data — Synthetic ECG using Gaussian-based waveform model
np.random.seed(42)
fs = 1000
duration = 2.5
t = np.linspace(0, duration, int(fs * duration))
heart_rate = 72
beat_interval = 60.0 / heart_rate
beat_t = np.linspace(0, beat_interval, int(fs * beat_interval))

# P wave, QRS complex (Q dip, R peak, S dip), T wave — each as Gaussian pulse
p_wave = 0.15 * np.exp(-((beat_t - 0.16) ** 2) / (2 * 0.025**2))
q_wave = -0.12 * np.exp(-((beat_t - 0.24) ** 2) / (2 * 0.008**2))
r_wave = 1.0 * np.exp(-((beat_t - 0.26) ** 2) / (2 * 0.012**2))
s_wave = -0.2 * np.exp(-((beat_t - 0.28) ** 2) / (2 * 0.010**2))
t_wave = 0.3 * np.exp(-((beat_t - 0.42) ** 2) / (2 * 0.040**2))
single_beat = p_wave + q_wave + r_wave + s_wave + t_wave

# Tile beats across full duration
n_beats = int(np.ceil(duration / beat_interval)) + 1
full_template = np.tile(single_beat, n_beats)[: len(t)]

# Lead-specific amplitude/polarity factors and precordial R-wave progression
lead_factors = {
    "I": 0.8,
    "II": 1.0,
    "III": 0.5,
    "aVR": -0.7,
    "aVL": 0.3,
    "aVF": 0.75,
    "V1": -0.4,
    "V2": 0.1,
    "V3": 0.6,
    "V4": 1.0,
    "V5": 0.9,
    "V6": 0.7,
}
precordial_r = {"V1": 0.3, "V2": 0.5, "V3": 0.8, "V4": 1.2, "V5": 1.1, "V6": 0.9}
precordial_s = {"V1": 1.5, "V2": 1.2, "V3": 0.8, "V4": 0.3, "V5": 0.2, "V6": 0.1}

lead_signals = {}
for lead_name, factor in lead_factors.items():
    signal = full_template * factor
    if lead_name in precordial_r:
        r_mod = (precordial_r[lead_name] - 1.0) * np.exp(-((beat_t - 0.26) ** 2) / (2 * 0.012**2))
        s_mod = -(precordial_s[lead_name] - 1.0) * 0.2 * np.exp(-((beat_t - 0.28) ** 2) / (2 * 0.010**2))
        signal = signal + np.tile(r_mod + s_mod, n_beats)[: len(t)]
    lead_signals[lead_name] = signal + np.random.normal(0, 0.008, len(t))

# Standard clinical 3x4 grid layout
grid_layout = [["I", "aVR", "V1", "V4"], ["II", "aVL", "V2", "V5"], ["III", "aVF", "V3", "V6"]]

# Build combined dataframe for all 12 leads with row/col position
all_leads = []
label_records = []
for row_idx, row_leads in enumerate(grid_layout):
    for col_idx, lead_name in enumerate(row_leads):
        df = pd.DataFrame({"time": t, "voltage": lead_signals[lead_name]})
        df["lead"] = lead_name
        df["row"] = row_idx
        df["col"] = col_idx
        all_leads.append(df)
        label_records.append({"lead": lead_name, "row": row_idx, "col": col_idx})
leads_df = pd.concat(all_leads, ignore_index=True)
labels_df = pd.DataFrame(label_records)

# ECG paper grid styling
grid_bg = "#FFF0EC"
grid_line_color = "#E8B4B4"
grid_bold_color = "#C87872"

# Grid line data
fine_h_lines = pd.DataFrame({"y": np.arange(-1.5, 1.61, 0.1)})
bold_h_lines = pd.DataFrame({"y": np.arange(-1.5, 1.61, 0.5)})
fine_v_lines = pd.DataFrame({"x": np.arange(0, duration + 0.01, 0.04)})
bold_v_lines = pd.DataFrame({"x": np.arange(0, duration + 0.01, 0.2)})

# Chart dimensions
panel_w = 380
panel_h = 200
x_domain = [0, duration]
y_domain = [-1.2, 1.5]

# Reusable grid layers — created once, used in all panels
grid_layers = (
    alt.Chart(fine_h_lines)
    .mark_rule(color=grid_line_color, strokeWidth=0.5, opacity=0.5)
    .encode(y=alt.Y("y:Q", scale=alt.Scale(domain=y_domain), axis=None))
    + alt.Chart(bold_h_lines)
    .mark_rule(color=grid_bold_color, strokeWidth=1.2, opacity=0.65)
    .encode(y=alt.Y("y:Q", scale=alt.Scale(domain=y_domain), axis=None))
    + alt.Chart(fine_v_lines)
    .mark_rule(color=grid_line_color, strokeWidth=0.5, opacity=0.5)
    .encode(x=alt.X("x:Q", scale=alt.Scale(domain=x_domain), axis=None))
    + alt.Chart(bold_v_lines)
    .mark_rule(color=grid_bold_color, strokeWidth=1.2, opacity=0.65)
    .encode(x=alt.X("x:Q", scale=alt.Scale(domain=x_domain), axis=None))
)

# Plot — Build 3x4 lead grid using facet-like data-driven approach
rows = []
for row_idx, row_leads in enumerate(grid_layout):
    show_x = row_idx == 2
    lead_charts = []
    for col_idx, lead_name in enumerate(row_leads):
        lead_df = leads_df[(leads_df["row"] == row_idx) & (leads_df["col"] == col_idx)]

        x_enc = (
            alt.X(
                "time:Q",
                scale=alt.Scale(domain=x_domain),
                axis=alt.Axis(title="Time (s)", titleFontSize=20, labelFontSize=18, tickCount=6),
            )
            if show_x
            else alt.X("time:Q", scale=alt.Scale(domain=x_domain), axis=None)
        )

        signal_layer = (
            alt.Chart(lead_df)
            .mark_line(strokeWidth=1.8, interpolate="monotone")
            .encode(
                x=x_enc, y=alt.Y("voltage:Q", scale=alt.Scale(domain=y_domain), axis=None), color=alt.value("#1a1a1a")
            )
        )

        label_df = pd.DataFrame({"x": [0.06], "y": [1.35], "text": [lead_name]})
        label_layer = (
            alt.Chart(label_df)
            .mark_text(fontSize=20, fontWeight="bold", align="left", baseline="top")
            .encode(
                x=alt.X("x:Q", scale=alt.Scale(domain=x_domain)),
                y=alt.Y("y:Q", scale=alt.Scale(domain=y_domain)),
                text="text:N",
                color=alt.value("#222222"),
            )
        )

        panel = (grid_layers + signal_layer + label_layer).properties(width=panel_w, height=panel_h)
        lead_charts.append(panel)
    rows.append(alt.hconcat(*lead_charts, spacing=4))

# Rhythm strip — full-length Lead II across bottom
rhythm_df = pd.DataFrame({"time": t, "voltage": lead_signals["II"]})
rhythm_signal = (
    alt.Chart(rhythm_df)
    .mark_line(strokeWidth=2.0, interpolate="monotone")
    .encode(
        x=alt.X(
            "time:Q",
            scale=alt.Scale(domain=x_domain),
            axis=alt.Axis(title="Time (s)", titleFontSize=20, labelFontSize=18, tickCount=10),
        ),
        y=alt.Y("voltage:Q", scale=alt.Scale(domain=y_domain), axis=None),
        color=alt.value("#1a1a1a"),
    )
)

rhythm_label_df = pd.DataFrame({"x": [0.12], "y": [1.35], "text": ["II (rhythm)"]})
rhythm_label = (
    alt.Chart(rhythm_label_df)
    .mark_text(fontSize=20, fontWeight="bold", align="left", baseline="top")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=x_domain)),
        y=alt.Y("y:Q", scale=alt.Scale(domain=y_domain)),
        text="text:N",
        color=alt.value("#222222"),
    )
)

# Calibration pulse (1mV square at start of rhythm strip)
cal_df = pd.DataFrame({"time": [0.0, 0.0, 0.04, 0.04, 0.08, 0.08], "voltage": [0.0, 1.0, 1.0, 0.0, 0.0, 0.0]})
cal_signal = (
    alt.Chart(cal_df)
    .mark_line(strokeWidth=2.0)
    .encode(
        x=alt.X("time:Q", scale=alt.Scale(domain=x_domain)),
        y=alt.Y("voltage:Q", scale=alt.Scale(domain=y_domain)),
        color=alt.value("#1a1a1a"),
    )
)
cal_label_df = pd.DataFrame({"x": [0.04], "y": [1.12], "text": ["1 mV"]})
cal_label = (
    alt.Chart(cal_label_df)
    .mark_text(fontSize=16, fontWeight="bold", align="center", baseline="bottom")
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=x_domain)),
        y=alt.Y("y:Q", scale=alt.Scale(domain=y_domain)),
        text="text:N",
        color=alt.value("#222222"),
    )
)

# Waveform annotation on Lead II panel — label P, QRS, T morphology
annot_data = pd.DataFrame({"x": [0.16, 0.26, 0.42], "y": [0.35, 1.25, 0.50], "text": ["P", "R", "T"]})
annot_layer = (
    alt.Chart(annot_data)
    .mark_text(fontSize=16, fontWeight="bold", fontStyle="italic", align="center", dy=-10)
    .encode(
        x=alt.X("x:Q", scale=alt.Scale(domain=x_domain)),
        y=alt.Y("y:Q", scale=alt.Scale(domain=y_domain)),
        text="text:N",
        color=alt.value("#B04040"),
    )
)

rhythm_strip = (grid_layers + rhythm_signal + rhythm_label + cal_signal + cal_label + annot_layer).properties(
    width=panel_w * 4 + 12, height=150
)

# Style — Combine all rows and rhythm strip
chart = (
    alt.vconcat(*rows, rhythm_strip, spacing=4)
    .properties(
        title=alt.Title(
            "ecg-twelve-lead · altair · pyplots.ai",
            fontSize=28,
            fontWeight="bold",
            anchor="middle",
            subtitle=["Normal Sinus Rhythm · 72 BPM · 12-Lead ECG", "25 mm/s · 10 mm/mV"],
            subtitleFontSize=18,
            subtitleColor="#666666",
            offset=10,
        )
    )
    .configure_view(strokeWidth=0.5, stroke="#D4908A", fill=grid_bg, cornerRadius=2)
    .configure_concat(spacing=4)
    .configure(background="#FFFFFF", padding={"left": 20, "right": 20, "top": 10, "bottom": 10})
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")

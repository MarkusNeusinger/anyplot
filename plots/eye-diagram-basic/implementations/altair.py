"""pyplots.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: altair 6.0.0 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-17
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)

n_traces = 300
samples_per_ui = 200
amplitude = 1.0
noise_sigma = 0.05 * amplitude
jitter_sigma = 0.03

n_bits = n_traces + 4
bits = np.random.randint(0, 2, n_bits)

samples_per_bit = samples_per_ui
total_signal_len = n_bits * samples_per_bit
t_full = np.arange(total_signal_len) / samples_per_bit

signal_full = np.zeros(total_signal_len)
for i in range(total_signal_len):
    bit_idx = int(t_full[i])
    if bit_idx >= n_bits:
        bit_idx = n_bits - 1
    frac = t_full[i] - bit_idx

    current_level = bits[bit_idx] * amplitude
    prev_level = bits[bit_idx - 1] * amplitude if bit_idx > 0 else bits[0] * amplitude

    transition_width = 0.12
    blend = 1.0 / (1.0 + np.exp(-14 * (frac - transition_width) / transition_width))
    signal_full[i] = prev_level + (current_level - prev_level) * blend

signal_full += np.random.normal(0, noise_sigma, total_signal_len)

all_time = []
all_voltage = []
window_samples = 2 * samples_per_ui

for trace in range(n_traces):
    start_bit = trace + 1
    start_sample = start_bit * samples_per_bit
    end_sample = start_sample + window_samples

    if end_sample > total_signal_len:
        break

    jitter_offset = np.random.normal(0, jitter_sigma)
    trace_time = np.linspace(0, 2, window_samples) + jitter_offset
    trace_voltage = signal_full[start_sample:end_sample]

    all_time.extend(trace_time.tolist())
    all_voltage.extend(trace_voltage.tolist())

# Pre-bin into 2D histogram for density heatmap
time_bins = 300
voltage_bins = 180
time_edges = np.linspace(-0.05, 2.05, time_bins + 1)
voltage_edges = np.linspace(-0.2, 1.2, voltage_bins + 1)

hist, _, _ = np.histogram2d(all_time, all_voltage, bins=[time_edges, voltage_edges])

time_centers = (time_edges[:-1] + time_edges[1:]) / 2
voltage_centers = (voltage_edges[:-1] + voltage_edges[1:]) / 2

# Compute pixel-aligned rect sizes that fully tile with no gaps
time_range = 2.1  # domain extent visible
voltage_range = 1.4  # domain extent visible
rect_width = (time_range / time_bins) * (1600 / time_range) + 1.5
rect_height = (voltage_range / voltage_bins) * (900 / voltage_range) + 1.5

rows = []
for i in range(time_bins):
    for j in range(voltage_bins):
        if hist[i, j] > 0:
            rows.append(
                {
                    "time_ui": round(float(time_centers[i]), 4),
                    "voltage_v": round(float(voltage_centers[j]), 4),
                    "density": float(hist[i, j]),
                }
            )

df = pd.DataFrame(rows)
df["log_density"] = np.log1p(df["density"])

# Compute eye measurements for annotations
mid_time = 1.0
eye_center_v = amplitude / 2
mid_mask = (np.array(all_time) > 0.9) & (np.array(all_time) < 1.1)
mid_voltages = np.array(all_voltage)[mid_mask]
high_voltages = mid_voltages[mid_voltages > eye_center_v]
low_voltages = mid_voltages[mid_voltages <= eye_center_v]
eye_top = float(np.percentile(high_voltages, 5)) if len(high_voltages) > 0 else 0.9
eye_bottom = float(np.percentile(low_voltages, 95)) if len(low_voltages) > 0 else 0.1
eye_height = eye_top - eye_bottom

mid_v_mask = (np.array(all_voltage) > 0.4) & (np.array(all_voltage) < 0.6)
transition_times = np.array(all_time)[mid_v_mask]
left_transitions = transition_times[transition_times < 1.0]
right_transitions = transition_times[transition_times >= 1.0]
eye_left = float(np.percentile(left_transitions, 95)) if len(left_transitions) > 0 else 0.3
eye_right = float(np.percentile(right_transitions, 5)) if len(right_transitions) > 0 else 1.7
eye_width = eye_right - eye_left

# Plot — dark theme for signal integrity visualization
bg_color = "#0a0a1a"
text_color = "#c8c8d4"
tick_color = "#666680"
annotation_color = "#00e5ff"

# Heatmap using mark_rect with precise sizing for seamless tiling
heatmap = (
    alt.Chart(df)
    .mark_rect(width=rect_width, height=rect_height)
    .encode(
        x=alt.X("time_ui:Q", title="Time (UI)", scale=alt.Scale(domain=[0, 2])),
        y=alt.Y("voltage_v:Q", title="Voltage (V)", scale=alt.Scale(domain=[-0.15, 1.15])),
        color=alt.Color(
            "log_density:Q",
            scale=alt.Scale(scheme="inferno"),
            legend=alt.Legend(
                title="Log Density",
                titleColor=text_color,
                labelColor=text_color,
                titleFontSize=14,
                labelFontSize=12,
                gradientLength=200,
                orient="right",
            ),
        ),
        tooltip=[
            alt.Tooltip("time_ui:Q", title="Time (UI)", format=".3f"),
            alt.Tooltip("voltage_v:Q", title="Voltage (V)", format=".3f"),
            alt.Tooltip("density:Q", title="Trace Count", format=".0f"),
        ],
    )
)

# Eye height annotation (vertical dashed line)
ann_height = pd.DataFrame([{"x": mid_time + 0.02, "y": eye_bottom, "y2": eye_top}])
height_rule = (
    alt.Chart(ann_height)
    .mark_rule(color=annotation_color, strokeWidth=2.5, strokeDash=[8, 4])
    .encode(x="x:Q", y="y:Q", y2="y2:Q")
)

# Eye width annotation (horizontal dashed line)
ann_width = pd.DataFrame([{"x": eye_left, "x2": eye_right, "y": eye_center_v}])
width_rule = (
    alt.Chart(ann_width)
    .mark_rule(color=annotation_color, strokeWidth=2.5, strokeDash=[8, 4])
    .encode(x="x:Q", x2="x2:Q", y="y:Q")
)

# Annotation labels — positioned inside eye opening, away from dense regions
ann_labels = pd.DataFrame(
    [
        {"x": mid_time + 0.15, "y": eye_center_v + 0.16, "text": f"Eye Height: {eye_height:.3f} V"},
        {"x": (eye_left + eye_right) / 2, "y": eye_center_v - 0.12, "text": f"Eye Width: {eye_width:.2f} UI"},
    ]
)
labels = (
    alt.Chart(ann_labels)
    .mark_text(color=annotation_color, fontSize=16, fontWeight="bold", align="center", baseline="middle")
    .encode(x="x:Q", y="y:Q", text="text:N")
)

# Diamond markers at eye opening corners for visual emphasis
eye_markers = pd.DataFrame(
    [
        {"x": mid_time, "y": eye_top},
        {"x": mid_time, "y": eye_bottom},
        {"x": eye_left, "y": eye_center_v},
        {"x": eye_right, "y": eye_center_v},
    ]
)
markers = (
    alt.Chart(eye_markers)
    .mark_point(shape="diamond", color=annotation_color, size=100, filled=True, opacity=0.9)
    .encode(x="x:Q", y="y:Q")
)

chart = (
    (heatmap + height_rule + width_rule + labels + markers)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "eye-diagram-basic · altair · pyplots.ai",
            fontSize=28,
            fontWeight=500,
            color=text_color,
            subtitle="NRZ signal eye diagram — 300 traces with 5% noise and 3% jitter",
            subtitleFontSize=16,
            subtitleColor="#8888a0",
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        labelColor=text_color,
        titleColor=text_color,
        tickColor=tick_color,
        domainColor=tick_color,
        grid=False,
    )
    .configure_view(stroke=None, fill=bg_color)
    .configure(background=bg_color)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")

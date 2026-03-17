"""pyplots.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-17
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import BoxAnnotation, ColorBar, ColumnDataSource, Label, LinearColorMapper, Span
from bokeh.palettes import Inferno256
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Simulate NRZ eye diagram
np.random.seed(42)

n_traces = 400
samples_per_ui = 150
n_bits = 3
total_samples = samples_per_ui * n_bits

noise_sigma = 0.05
jitter_sigma = 0.03

# Generate all traces
all_time = []
all_voltage = []

for _ in range(n_traces):
    bits = np.random.randint(0, 2, n_bits + 2)
    signal = np.zeros(total_samples)

    for i in range(n_bits):
        prev_bit = bits[i]
        curr_bit = bits[i + 1]

        t_local = np.linspace(0, 1, samples_per_ui)
        jitter = np.random.normal(0, jitter_sigma)

        if prev_bit != curr_bit:
            transition_point = 0.0 + jitter
            steepness = 12
            transition = 1 / (1 + np.exp(-steepness * (t_local - transition_point)))
            if prev_bit > curr_bit:
                segment = 1 - transition
            else:
                segment = transition
        else:
            segment = np.full(samples_per_ui, float(curr_bit))

        signal[i * samples_per_ui : (i + 1) * samples_per_ui] = segment

    signal += np.random.normal(0, noise_sigma, total_samples)

    # Extract 2-UI window centered on the middle bit
    start = samples_per_ui // 2
    end = start + 2 * samples_per_ui
    window_time = np.linspace(0, 2, end - start)
    window_voltage = signal[start:end]

    all_time.append(window_time)
    all_voltage.append(window_voltage)

all_time = np.array(all_time)
all_voltage = np.array(all_voltage)

# Build 2D histogram for density heatmap
time_bins = 300
voltage_bins = 200
time_edges = np.linspace(0, 2, time_bins + 1)
voltage_edges = np.linspace(-0.3, 1.3, voltage_bins + 1)

histogram, _, _ = np.histogram2d(all_time.ravel(), all_voltage.ravel(), bins=[time_edges, voltage_edges])

# Log-scale for better contrast
histogram = np.log1p(histogram).T

# Measure eye opening from the density data
voltage_centers = 0.5 * (voltage_edges[:-1] + voltage_edges[1:])
time_centers = 0.5 * (time_edges[:-1] + time_edges[1:])

# Eye height: vertical slice at time=1.0 UI (center of eye)
center_col = time_bins // 2
center_slice = histogram[:, center_col]
threshold = 0.3 * center_slice.max()

# Find contiguous low-density region containing the midpoint voltage (~0.5V)
mid_idx = voltage_bins // 2
low_mask = center_slice < threshold

# Walk outward from midpoint to find eye opening bounds
lower_eye_idx = mid_idx
while lower_eye_idx > 0 and low_mask[lower_eye_idx]:
    lower_eye_idx -= 1
upper_eye_idx = mid_idx
while upper_eye_idx < voltage_bins - 1 and low_mask[upper_eye_idx]:
    upper_eye_idx += 1

lower_eye = voltage_centers[lower_eye_idx]
upper_eye = voltage_centers[upper_eye_idx]
eye_height = upper_eye - lower_eye

# Eye width: horizontal slice at midpoint voltage
mid_v_idx = (lower_eye_idx + upper_eye_idx) // 2
mid_slice = histogram[mid_v_idx, :]
low_time_mask = mid_slice < threshold

# Walk outward from time center to find contiguous opening
center_time_idx = time_bins // 2
left_idx = center_time_idx
while left_idx > 0 and low_time_mask[left_idx]:
    left_idx -= 1
right_idx = center_time_idx
while right_idx < time_bins - 1 and low_time_mask[right_idx]:
    right_idx += 1

eye_left = time_centers[left_idx]
eye_right = time_centers[right_idx]
eye_width = eye_right - eye_left

# Plot
p = figure(
    width=4800,
    height=2700,
    title="eye-diagram-basic · bokeh · pyplots.ai",
    x_axis_label="Time (UI)",
    y_axis_label="Voltage (V)",
    x_range=(0, 2),
    y_range=(-0.3, 1.3),
    min_border_right=280,
    min_border_top=60,
)

color_mapper = LinearColorMapper(palette=Inferno256, low=0, high=float(histogram.max()))

p.image(image=[histogram], x=0, y=-0.3, dw=2, dh=1.6, color_mapper=color_mapper)

# Reference lines at 0V and 1V signal levels
p.add_layout(
    Span(location=0.0, dimension="width", line_color="#44aadd", line_width=3, line_alpha=0.5, line_dash="dashed")
)
p.add_layout(
    Span(location=1.0, dimension="width", line_color="#44aadd", line_width=3, line_alpha=0.5, line_dash="dashed")
)

# Eye opening highlight box
p.add_layout(
    BoxAnnotation(
        left=eye_left,
        right=eye_right,
        bottom=lower_eye,
        top=upper_eye,
        fill_color=None,
        line_color="#00ff88",
        line_width=3,
        line_alpha=0.8,
        line_dash="solid",
    )
)

# Eye height annotation (vertical line at center)
eye_h_source = ColumnDataSource(data={"x": [1.0, 1.0], "y": [lower_eye, upper_eye]})
p.line(x="x", y="y", source=eye_h_source, line_color="#00ff88", line_width=3, line_alpha=0.9)

# Eye width annotation (horizontal line at midpoint)
eye_mid_v = (upper_eye + lower_eye) / 2
eye_w_source = ColumnDataSource(data={"x": [eye_left, eye_right], "y": [eye_mid_v, eye_mid_v]})
p.line(x="x", y="y", source=eye_w_source, line_color="#00ff88", line_width=3, line_alpha=0.9)

# Labels for eye measurements
p.add_layout(
    Label(
        x=1.03,
        y=(upper_eye + lower_eye) / 2,
        text=f"Eye Height: {eye_height:.2f} V",
        text_color="#00ff88",
        text_font_size="18pt",
        text_font_style="bold",
        background_fill_color="#000000",
        background_fill_alpha=0.8,
    )
)
p.add_layout(
    Label(
        x=(eye_left + eye_right) / 2,
        y=lower_eye - 0.06,
        text=f"Eye Width: {eye_width:.2f} UI",
        text_color="#00ff88",
        text_font_size="18pt",
        text_font_style="bold",
        text_align="center",
        background_fill_color="#000000",
        background_fill_alpha=0.8,
    )
)

# Signal level labels
p.add_layout(
    Label(
        x=0.05,
        y=1.05,
        text="Logic 1 (1.0 V)",
        text_color="#44aadd",
        text_font_size="16pt",
        text_font_style="bold",
        text_alpha=0.7,
        background_fill_color="#000000",
        background_fill_alpha=0.6,
    )
)
p.add_layout(
    Label(
        x=0.05,
        y=-0.15,
        text="Logic 0 (0.0 V)",
        text_color="#44aadd",
        text_font_size="16pt",
        text_font_style="bold",
        text_alpha=0.7,
        background_fill_color="#000000",
        background_fill_alpha=0.6,
    )
)

color_bar = ColorBar(
    color_mapper=color_mapper,
    title="Log Density",
    title_text_font_size="18pt",
    title_text_color="#333333",
    title_standoff=20,
    label_standoff=16,
    width=45,
    location=(0, 0),
    major_label_text_font_size="16pt",
    padding=40,
)
p.add_layout(color_bar, "right")

# Style
p.title.text_font_size = "30pt"
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Remove grid lines for cleaner dark-background aesthetic
p.xgrid.grid_line_alpha = 0
p.ygrid.grid_line_alpha = 0

p.background_fill_color = "#000000"
p.border_fill_color = "#ffffff"

p.xaxis.axis_line_color = "#666666"
p.yaxis.axis_line_color = "#666666"
p.xaxis.major_tick_line_color = "#666666"
p.yaxis.major_tick_line_color = "#666666"
p.xaxis.major_label_text_color = "#333333"
p.yaxis.major_label_text_color = "#333333"
p.xaxis.axis_label_text_color = "#333333"
p.yaxis.axis_label_text_color = "#333333"
p.title.text_color = "#333333"

p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="eye-diagram-basic · bokeh · pyplots.ai")

"""pyplots.ai
eye-diagram-basic: Signal Integrity Eye Diagram
Library: bokeh 3.9.0 | Python 3.14.3
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import BoxAnnotation, ColorBar, ColumnDataSource, Label, LinearColorMapper, NumeralTickFormatter, Span
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

# Find eye opening bounds using numpy indexing
mid_idx = voltage_bins // 2
low_mask = center_slice < threshold

# Find contiguous low-density region around midpoint
low_indices = np.where(low_mask)[0]
eye_region = low_indices[(low_indices >= mid_idx - voltage_bins // 4) & (low_indices <= mid_idx + voltage_bins // 4)]
lower_eye = voltage_centers[eye_region[0]] if len(eye_region) > 0 else voltage_centers[mid_idx - 10]
upper_eye = voltage_centers[eye_region[-1]] if len(eye_region) > 0 else voltage_centers[mid_idx + 10]
eye_height = upper_eye - lower_eye

# Eye width: horizontal slice at midpoint voltage
mid_v_idx = np.searchsorted(voltage_centers, (lower_eye + upper_eye) / 2)
mid_slice = histogram[mid_v_idx, :]
low_time_mask = mid_slice < threshold

center_time_idx = time_bins // 2
low_time_indices = np.where(low_time_mask)[0]
eye_time_region = low_time_indices[
    (low_time_indices >= center_time_idx - time_bins // 4) & (low_time_indices <= center_time_idx + time_bins // 4)
]
eye_left = time_centers[eye_time_region[0]] if len(eye_time_region) > 0 else time_centers[center_time_idx - 20]
eye_right = time_centers[eye_time_region[-1]] if len(eye_time_region) > 0 else time_centers[center_time_idx + 20]
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
    min_border_left=120,
    min_border_right=160,
    min_border_top=60,
    min_border_bottom=100,
)

color_mapper = LinearColorMapper(palette=Inferno256, low=0, high=float(histogram.max()))

p.image(image=[histogram], x=0, y=-0.3, dw=2, dh=1.6, color_mapper=color_mapper)

# Reference lines at 0V and 1V signal levels - brighter and more visible
p.add_layout(
    Span(location=0.0, dimension="width", line_color="#66ccee", line_width=4, line_alpha=0.7, line_dash="dashed")
)
p.add_layout(
    Span(location=1.0, dimension="width", line_color="#66ccee", line_width=4, line_alpha=0.7, line_dash="dashed")
)

# Eye opening highlight box
p.add_layout(
    BoxAnnotation(
        left=eye_left,
        right=eye_right,
        bottom=lower_eye,
        top=upper_eye,
        fill_color="#00ff88",
        fill_alpha=0.04,
        line_color="#00ff88",
        line_width=3,
        line_alpha=0.9,
        line_dash="solid",
    )
)

# Eye height annotation (vertical line with end caps)
eye_h_source = ColumnDataSource(data={"x": [1.0, 1.0], "y": [lower_eye, upper_eye]})
p.line(x="x", y="y", source=eye_h_source, line_color="#00ff88", line_width=3, line_alpha=0.9)
# End caps for eye height
cap_w = 0.02
for cap_y in [lower_eye, upper_eye]:
    p.line(x=[1.0 - cap_w, 1.0 + cap_w], y=[cap_y, cap_y], line_color="#00ff88", line_width=3, line_alpha=0.9)

# Eye width annotation (horizontal line with end caps)
eye_mid_v = (upper_eye + lower_eye) / 2
eye_w_source = ColumnDataSource(data={"x": [eye_left, eye_right], "y": [eye_mid_v, eye_mid_v]})
p.line(x="x", y="y", source=eye_w_source, line_color="#00ff88", line_width=3, line_alpha=0.9)
# End caps for eye width
cap_h = 0.02
for cap_x in [eye_left, eye_right]:
    p.line(
        x=[cap_x, cap_x], y=[eye_mid_v - cap_h, eye_mid_v + cap_h], line_color="#00ff88", line_width=3, line_alpha=0.9
    )

# Labels for eye measurements
p.add_layout(
    Label(
        x=1.04,
        y=(upper_eye + lower_eye) / 2,
        text=f"Eye Height: {eye_height:.2f} V",
        text_color="#00ff88",
        text_font_size="20pt",
        text_font_style="bold",
        background_fill_color="#000000",
        background_fill_alpha=0.85,
    )
)
p.add_layout(
    Label(
        x=(eye_left + eye_right) / 2,
        y=lower_eye - 0.07,
        text=f"Eye Width: {eye_width:.2f} UI",
        text_color="#00ff88",
        text_font_size="20pt",
        text_font_style="bold",
        text_align="center",
        background_fill_color="#000000",
        background_fill_alpha=0.85,
    )
)

# Signal level labels - larger for readability
p.add_layout(
    Label(
        x=0.05,
        y=1.08,
        text="Logic 1 (1.0 V)",
        text_color="#66ccee",
        text_font_size="20pt",
        text_font_style="bold",
        background_fill_color="#000000",
        background_fill_alpha=0.7,
    )
)
p.add_layout(
    Label(
        x=0.05,
        y=-0.18,
        text="Logic 0 (0.0 V)",
        text_color="#66ccee",
        text_font_size="20pt",
        text_font_style="bold",
        background_fill_color="#000000",
        background_fill_alpha=0.7,
    )
)

color_bar = ColorBar(
    color_mapper=color_mapper,
    title="Log₁₀ Density",
    title_text_font_size="18pt",
    title_text_color="#444444",
    title_standoff=20,
    label_standoff=16,
    width=50,
    location=(0, 0),
    major_label_text_font_size="16pt",
    major_label_text_color="#444444",
    padding=30,
)
p.add_layout(color_bar, "right")

# Style
p.title.text_font_size = "30pt"
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Formatted tick labels
p.xaxis.formatter = NumeralTickFormatter(format="0.0")
p.yaxis.formatter = NumeralTickFormatter(format="0.0")

# Remove grid lines for cleaner dark-background aesthetic
p.xgrid.grid_line_alpha = 0
p.ygrid.grid_line_alpha = 0

p.background_fill_color = "#000000"
p.border_fill_color = "#f8f8f8"

p.xaxis.axis_line_color = "#555555"
p.yaxis.axis_line_color = "#555555"
p.xaxis.major_tick_line_color = "#555555"
p.yaxis.major_tick_line_color = "#555555"
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_label_text_color = "#444444"
p.yaxis.major_label_text_color = "#444444"
p.xaxis.axis_label_text_color = "#333333"
p.yaxis.axis_label_text_color = "#333333"
p.title.text_color = "#333333"

p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="eye-diagram-basic · bokeh · pyplots.ai")

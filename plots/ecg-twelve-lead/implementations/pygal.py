""" pyplots.ai
ecg-twelve-lead: ECG/EKG 12-Lead Waveform Display
Library: pygal 3.1.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-19
"""

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data — synthetic ECG generation using Gaussian pulse model
np.random.seed(42)
sampling_rate = 1000
duration = 2.5
num_samples = int(sampling_rate * duration)
t = np.linspace(0, duration, num_samples)
cycle_duration = 0.8


def ecg_component(t_local, amp, center, width):
    return amp * np.exp(-((t_local - center) ** 2) / (2 * width**2))


def generate_lead(t_arr, p_amp, q_amp, r_amp, s_amp, t_amp):
    signal = np.zeros_like(t_arr)
    dur = t_arr[-1] - t_arr[0] + (t_arr[1] - t_arr[0])
    for cycle_start in np.arange(t_arr[0], t_arr[0] + dur, cycle_duration):
        tc = t_arr - cycle_start
        mask = (tc >= 0) & (tc < cycle_duration)
        signal[mask] += ecg_component(tc[mask], p_amp, 0.16, 0.025)
        signal[mask] += ecg_component(tc[mask], q_amp, 0.28, 0.008)
        signal[mask] += ecg_component(tc[mask], r_amp, 0.30, 0.012)
        signal[mask] += ecg_component(tc[mask], s_amp, 0.33, 0.008)
        signal[mask] += ecg_component(tc[mask], t_amp, 0.48, 0.035)
    signal += np.random.normal(0, 0.012, len(t_arr))
    return signal


# 12 leads with realistic relative amplitudes
leads = {
    "I": generate_lead(t, 0.15, -0.08, 0.9, -0.15, 0.25),
    "II": generate_lead(t, 0.20, -0.10, 1.2, -0.20, 0.35),
    "III": generate_lead(t, 0.10, -0.05, 0.6, -0.10, 0.20),
    "aVR": generate_lead(t, -0.15, 0.05, -0.9, 0.10, -0.25),
    "aVL": generate_lead(t, 0.08, -0.06, 0.5, -0.08, 0.12),
    "aVF": generate_lead(t, 0.15, -0.08, 0.8, -0.15, 0.28),
    "V1": generate_lead(t, 0.10, -0.15, 0.3, -0.80, 0.15),
    "V2": generate_lead(t, 0.12, -0.20, 0.6, -1.00, 0.30),
    "V3": generate_lead(t, 0.15, -0.15, 1.0, -0.60, 0.35),
    "V4": generate_lead(t, 0.18, -0.10, 1.4, -0.30, 0.40),
    "V5": generate_lead(t, 0.18, -0.08, 1.2, -0.20, 0.35),
    "V6": generate_lead(t, 0.15, -0.06, 0.9, -0.15, 0.30),
}

# Clinical 3x4 grid layout
grid_layout = [["I", "aVR", "V1", "V4"], ["II", "aVL", "V2", "V5"], ["III", "aVF", "V3", "V6"]]

# Layout parameters — use larger row height for visibility
col_width = 2.5
col_gap = 0.3
col_offset = col_width + col_gap
row_height = 4.0
num_rows = 3
num_cols = 4
amp_scale = 1.5

# Chart dimensions
x_min = -0.6
x_max = num_cols * col_offset + 0.1
y_min = -num_rows * row_height - 2.5
y_max = row_height * 0.7

# Grid line colors (ECG paper: pink/red)
grid_major_color = "#D4A0A0"
grid_minor_color = "#E8C8C8"
waveform_color = "#1A1A1A"
bg_color = "#FFF5F0"
paper_color = "#FFF0E8"

# Build color tuple — need enough colors for all series
all_colors = (grid_major_color, grid_major_color, grid_minor_color, grid_minor_color) + (waveform_color,) * 40

ecg_style = Style(
    background=bg_color,
    plot_background=paper_color,
    foreground="#333333",
    foreground_strong="#1A1A1A",
    foreground_subtle="#E8D0D0",
    colors=all_colors,
    title_font_size=42,
    label_font_size=0,
    major_label_font_size=0,
    legend_font_size=0,
    value_font_size=0,
    stroke_width=2,
    font_family="monospace",
)

chart = pygal.XY(
    width=4800,
    height=2700,
    style=ecg_style,
    title="ecg-twelve-lead \u00b7 pygal \u00b7 pyplots.ai",
    show_dots=False,
    stroke=True,
    show_x_guides=False,
    show_y_guides=False,
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    allow_interruptions=True,
    js=[],
    print_values=False,
    margin_top=60,
    margin_bottom=20,
    margin_left=20,
    margin_right=20,
    range=(y_min, y_max),
    xrange=(x_min, x_max),
)

# Major grid lines (every 0.5 mV vertical, every 0.2s horizontal)
major_h = []
for y_val in np.arange(y_min, y_max + 0.01, 0.5):
    major_h.extend([(x_min, float(y_val)), (x_max, float(y_val)), None])
chart.add(None, major_h, show_dots=False, stroke_style={"width": 1.8})

major_v = []
for x_val in np.arange(x_min, x_max + 0.01, 0.2):
    major_v.extend([(float(x_val), y_min), (float(x_val), y_max), None])
chart.add(None, major_v, show_dots=False, stroke_style={"width": 1.8})

# Minor grid lines (every 0.1 mV vertical, every 0.04s horizontal)
minor_h = []
for y_val in np.arange(y_min, y_max + 0.01, 0.1):
    minor_h.extend([(x_min, float(y_val)), (x_max, float(y_val)), None])
chart.add(None, minor_h, show_dots=False, stroke_style={"width": 0.5})

minor_v = []
for x_val in np.arange(x_min, x_max + 0.01, 0.04):
    minor_v.extend([(float(x_val), y_min), (float(x_val), y_max), None])
chart.add(None, minor_v, show_dots=False, stroke_style={"width": 0.5})

# Calibration pulse (1mV) at start of each row
for row in range(num_rows):
    y_base = -row * row_height
    cal = [(-0.40, y_base), (-0.40, y_base + 1.0 * amp_scale), (-0.20, y_base + 1.0 * amp_scale), (-0.20, y_base)]
    chart.add(None, cal, show_dots=False, stroke_style={"width": 4, "linecap": "square", "linejoin": "miter"})

# ECG waveforms — downsample for performance
ds = 3
t_ds = t[::ds]

for row_idx, row_leads in enumerate(grid_layout):
    for col_idx, lead_name in enumerate(row_leads):
        signal = leads[lead_name][::ds] * amp_scale
        x_off = col_idx * col_offset
        y_off = -row_idx * row_height

        pts = list(zip((t_ds + x_off).tolist(), (signal + y_off).tolist(), strict=True))
        chart.add(None, pts, show_dots=False, stroke_style={"width": 4.5, "linecap": "round", "linejoin": "round"})

# Lead II rhythm strip across bottom
np.random.seed(99)
rhythm_duration = 10.0
rhythm_samples = int(rhythm_duration * sampling_rate)
rhythm_t = np.linspace(0, rhythm_duration, rhythm_samples)
rhythm_signal = generate_lead(rhythm_t, 0.20, -0.10, 1.2, -0.20, 0.35) * amp_scale

rhythm_x_scale = (x_max - x_min) / rhythm_duration
rhythm_ds = 4
rx = rhythm_t[::rhythm_ds] * rhythm_x_scale + x_min
ry = rhythm_signal[::rhythm_ds] + (-num_rows * row_height - 1.0)
rhythm_pts = list(zip(rx.tolist(), ry.tolist(), strict=True))
chart.add(None, rhythm_pts, show_dots=False, stroke_style={"width": 4.5, "linecap": "round", "linejoin": "round"})

# Render SVG
svg = chart.render(is_unicode=True)

# Inject lead labels via SVG text elements
label_style = 'font-family="monospace" font-size="36" font-weight="bold" fill="#1A1A1A"'
labels_svg = ""
for row_idx, row_leads in enumerate(grid_layout):
    for col_idx, lead_name in enumerate(row_leads):
        px = 65 + col_idx * 1110
        py = 130 + row_idx * 640
        labels_svg += f'<text x="{px}" y="{py}" {label_style}>{lead_name}</text>\n'

labels_svg += f'<text x="65" y="{130 + 3 * 640}" {label_style}>II (rhythm)</text>\n'

svg = svg.replace("</svg>", labels_svg + "</svg>")

# Save
with open("plot.html", "w") as f:
    f.write(svg)
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to="plot.png", dpi=96)

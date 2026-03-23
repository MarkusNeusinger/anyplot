""" pyplots.ai
ecg-twelve-lead: ECG/EKG 12-Lead Waveform Display
Library: pygal 3.1.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-19
"""

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data — synthetic ECG via Gaussian pulse model (flat script, no helper functions)
np.random.seed(42)
sampling_rate = 1000
duration = 2.5
num_samples = int(sampling_rate * duration)
t = np.linspace(0, duration, num_samples)
cycle_duration = 0.8

# Lead parameters: (p_amp, q_amp, r_amp, s_amp, t_amp)
lead_params = {
    "I": (0.15, -0.08, 0.9, -0.15, 0.25),
    "II": (0.20, -0.10, 1.2, -0.20, 0.35),
    "III": (0.10, -0.05, 0.6, -0.10, 0.20),
    "aVR": (-0.15, 0.05, -0.9, 0.10, -0.25),
    "aVL": (0.08, -0.06, 0.5, -0.08, 0.12),
    "aVF": (0.15, -0.08, 0.8, -0.15, 0.28),
    "V1": (0.10, -0.15, 0.3, -0.80, 0.15),
    "V2": (0.12, -0.20, 0.6, -1.00, 0.30),
    "V3": (0.15, -0.15, 1.0, -0.60, 0.35),
    "V4": (0.18, -0.10, 1.4, -0.30, 0.40),
    "V5": (0.18, -0.08, 1.2, -0.20, 0.35),
    "V6": (0.15, -0.06, 0.9, -0.15, 0.30),
}

# Generate all lead signals inline
leads = {}
for name, (p_a, q_a, r_a, s_a, t_a) in lead_params.items():
    signal = np.zeros_like(t)
    for cycle_start in np.arange(0, duration, cycle_duration):
        tc = t - cycle_start
        mask = (tc >= 0) & (tc < cycle_duration)
        signal[mask] += p_a * np.exp(-((tc[mask] - 0.16) ** 2) / (2 * 0.025**2))
        signal[mask] += q_a * np.exp(-((tc[mask] - 0.28) ** 2) / (2 * 0.008**2))
        signal[mask] += r_a * np.exp(-((tc[mask] - 0.30) ** 2) / (2 * 0.012**2))
        signal[mask] += s_a * np.exp(-((tc[mask] - 0.33) ** 2) / (2 * 0.008**2))
        signal[mask] += t_a * np.exp(-((tc[mask] - 0.48) ** 2) / (2 * 0.035**2))
    signal += np.random.normal(0, 0.012, len(t))
    leads[name] = signal

# Rhythm strip (Lead II, longer duration)
rhythm_duration = 10.0
rhythm_samples = int(rhythm_duration * sampling_rate)
rhythm_t = np.linspace(0, rhythm_duration, rhythm_samples)
rhythm_signal = np.zeros(rhythm_samples)
for cycle_start in np.arange(0, rhythm_duration, cycle_duration):
    tc = rhythm_t - cycle_start
    mask = (tc >= 0) & (tc < cycle_duration)
    rhythm_signal[mask] += 0.20 * np.exp(-((tc[mask] - 0.16) ** 2) / (2 * 0.025**2))
    rhythm_signal[mask] += -0.10 * np.exp(-((tc[mask] - 0.28) ** 2) / (2 * 0.008**2))
    rhythm_signal[mask] += 1.2 * np.exp(-((tc[mask] - 0.30) ** 2) / (2 * 0.012**2))
    rhythm_signal[mask] += -0.20 * np.exp(-((tc[mask] - 0.33) ** 2) / (2 * 0.008**2))
    rhythm_signal[mask] += 0.35 * np.exp(-((tc[mask] - 0.48) ** 2) / (2 * 0.035**2))
rhythm_signal += np.random.normal(0, 0.012, rhythm_samples)

# Clinical 3x4 grid layout
grid_layout = [["I", "aVR", "V1", "V4"], ["II", "aVL", "V2", "V5"], ["III", "aVF", "V3", "V6"]]

# Layout parameters
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

# Color scheme — ECG paper pink/red with precordial emphasis
grid_major_color = "#D4A0A0"
grid_minor_color = "#E8C8C8"
waveform_color = "#1A1A1A"
precordial_color = "#0D47A1"  # Deep blue for V1-V6 R-wave progression emphasis
bg_color = "#FFF5F0"
paper_color = "#FFF0E8"

# Build color tuple for all series
# 4 grid series + 3 calibration + 12 waveforms + 1 rhythm = 20 series
grid_colors = (grid_major_color,) * 2 + (grid_minor_color,) * 2
cal_colors = (waveform_color,) * 3
# Waveforms: limb leads black, precordial leads blue for storytelling
waveform_colors = ()
for row_leads in grid_layout:
    for lead_name in row_leads:
        if lead_name.startswith("V"):
            waveform_colors += (precordial_color,)
        else:
            waveform_colors += (waveform_color,)
rhythm_color = (waveform_color,)
all_colors = grid_colors + cal_colors + waveform_colors + rhythm_color

ecg_style = Style(
    background=bg_color,
    plot_background=paper_color,
    foreground="#333333",
    foreground_strong="#1A1A1A",
    foreground_subtle="#E8D0D0",
    colors=all_colors,
    title_font_size=48,
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
    x_title="25 mm/s  |  10 mm/mV",
    margin_top=60,
    margin_bottom=50,
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

# ECG waveforms — downsample for performance, use secondary_series for precordial emphasis
ds = 3
t_ds = t[::ds]

for row_idx, row_leads in enumerate(grid_layout):
    for col_idx, lead_name in enumerate(row_leads):
        signal = leads[lead_name][::ds] * amp_scale
        x_off = col_idx * col_offset
        y_off = -row_idx * row_height
        pts = list(zip((t_ds + x_off).tolist(), (signal + y_off).tolist(), strict=True))
        stroke_w = 5.0 if lead_name.startswith("V") else 4.0
        chart.add(None, pts, show_dots=False, stroke_style={"width": stroke_w, "linecap": "round", "linejoin": "round"})

# Lead II rhythm strip across bottom
rhythm_x_scale = (x_max - x_min) / rhythm_duration
rhythm_ds = 4
rx = rhythm_t[::rhythm_ds] * rhythm_x_scale + x_min
ry = rhythm_signal[::rhythm_ds] * amp_scale + (-num_rows * row_height - 1.0)
rhythm_pts = list(zip(rx.tolist(), ry.tolist(), strict=True))
chart.add(None, rhythm_pts, show_dots=False, stroke_style={"width": 4.5, "linecap": "round", "linejoin": "round"})

# Render SVG
svg = chart.render(is_unicode=True)

# Inject lead labels and scale annotations via SVG text elements
label_style = 'font-family="monospace" font-size="48" font-weight="bold"'
labels_svg = ""
for row_idx, row_leads in enumerate(grid_layout):
    for col_idx, lead_name in enumerate(row_leads):
        px = 65 + col_idx * 1110
        py = 130 + row_idx * 640
        fill = precordial_color if lead_name.startswith("V") else "#1A1A1A"
        labels_svg += f'<text x="{px}" y="{py}" {label_style} fill="{fill}">{lead_name}</text>\n'

# Rhythm strip label
labels_svg += f'<text x="65" y="{130 + 3 * 640}" {label_style} fill="#1A1A1A">II (rhythm)</text>\n'

# Scale calibration text near bottom-right
labels_svg += (
    '<text x="4500" y="2650" font-family="monospace" font-size="36" '
    'fill="#666666" text-anchor="end">25 mm/s  ·  10 mm/mV  ·  1 mV cal</text>\n'
)

svg = svg.replace("</svg>", labels_svg + "</svg>")

# Save
with open("plot.html", "w") as f:
    f.write(svg)
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to="plot.png", dpi=96)

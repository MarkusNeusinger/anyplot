""" pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: pygal 3.1.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-21
"""

import io
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Data — Second-order low-pass: G(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
# Natural frequency 5 Hz, damping ratio 0.2 (clear resonance peak)
frequency_hz = np.logspace(-1, 3, 500)
omega = 2 * np.pi * frequency_hz
wn = 2 * np.pi * 5.0
zeta = 0.2
s = 1j * omega
G = wn**2 / (s**2 + 2 * zeta * wn * s + wn**2)

magnitude_db = 20 * np.log10(np.abs(G))
phase_deg = np.degrees(np.unwrap(np.angle(G)))

# Log-transform x-axis (pygal logarithmic=True applies to both axes)
log_freq = np.log10(frequency_hz)

# Find gain crossover: where magnitude crosses 0 dB going downward (after peak)
peak_idx = np.argmax(magnitude_db)
zero_crossings_after_peak = np.where(np.diff(np.sign(magnitude_db[peak_idx:])))[0]
if len(zero_crossings_after_peak) > 0:
    gain_crossover_idx = peak_idx + zero_crossings_after_peak[0]
    gain_crossover_freq = frequency_hz[gain_crossover_idx]
    phase_at_gain_crossover = phase_deg[gain_crossover_idx]
    phase_margin = 180 + phase_at_gain_crossover
else:
    gain_crossover_freq = None
    phase_margin = None

# Find phase crossover: where phase crosses -180°
phase_crossover_indices = np.where(np.diff(np.sign(phase_deg + 180)))[0]
if len(phase_crossover_indices) > 0:
    phase_crossover_idx = phase_crossover_indices[0]
    phase_crossover_freq = frequency_hz[phase_crossover_idx]
    gain_margin = -magnitude_db[phase_crossover_idx]
else:
    gain_margin = None

# Style
highlight_color = "#306998"
ref_line_color = "#C0392B"
annotation_color = "#2E86AB"
bg_color = "#FAFAFA"
text_color = "#1A1A2E"
grid_color = "#E0E4E8"

custom_style = Style(
    background="white",
    plot_background=bg_color,
    foreground=text_color,
    foreground_strong=text_color,
    foreground_subtle=grid_color,
    colors=(highlight_color,),
    title_font_size=48,
    label_font_size=28,
    major_label_font_size=28,
    legend_font_size=24,
    value_font_size=18,
    stroke_width=4,
    font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    title_font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    label_font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    value_font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
)

# X-axis labels (log-spaced frequency ticks)
x_label_values = [0.1, 0.5, 1, 5, 10, 50, 100, 500, 1000]
x_label_positions = [np.log10(v) for v in x_label_values]

# Explicit y-ranges for precise reference line placement
mag_y_min = -100.0
mag_y_max = 20.0
phase_y_min = -200.0
phase_y_max = 10.0

# Common chart config
common_config = {
    "width": 4800,
    "height": 1300,
    "style": custom_style,
    "show_legend": False,
    "show_y_guides": True,
    "show_x_guides": True,
    "margin": 25,
    "margin_left": 140,
    "margin_right": 60,
    "dots_size": 0,
    "stroke": True,
    "truncate_label": -1,
    "print_values": False,
    "x_value_formatter": lambda x: f"{10**x:.4g}",
}

# Subsample data
step = 2
mag_data = [(float(log_freq[i]), float(magnitude_db[i])) for i in range(0, len(frequency_hz), step)]
phase_data = [(float(log_freq[i]), float(phase_deg[i])) for i in range(0, len(frequency_hz), step)]

# Magnitude chart
mag_chart = pygal.XY(
    **common_config,
    title="bode-basic · pygal · pyplots.ai",
    x_title="",
    y_title="Magnitude (dB)",
    margin_bottom=10,
    margin_top=30,
    range=(mag_y_min, mag_y_max),
)
mag_chart.x_labels = x_label_positions
mag_chart.x_labels_major = x_label_positions
mag_chart.add("Magnitude", mag_data, show_dots=False, stroke_style={"width": 5})

# Phase chart
phase_chart = pygal.XY(
    **common_config,
    title="",
    x_title="Frequency (Hz)",
    y_title="Phase (°)",
    margin_bottom=70,
    margin_top=5,
    range=(phase_y_min, phase_y_max),
)
phase_chart.x_labels = x_label_positions
phase_chart.x_labels_major = x_label_positions
phase_chart.add("Phase", phase_data, show_dots=False, stroke_style={"width": 5})

# Render SVGs and inject reference lines at known y positions
ns = "http://www.w3.org/2000/svg"
ET.register_namespace("", ns)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

ref_configs = [(mag_chart, mag_y_min, mag_y_max, 0.0), (phase_chart, phase_y_min, phase_y_max, -180.0)]

png_images = []
for chart_obj, y_lo, y_hi, ref_val in ref_configs:
    root = ET.fromstring(chart_obj.render())
    plot_group = next((g for g in root.iter(f"{{{ns}}}g") if g.get("class", "") == "plot"), None)
    if plot_group is not None:
        bg_rect = next((r for r in plot_group.iter(f"{{{ns}}}rect") if r.get("class", "") == "background"), None)
        if bg_rect is not None:
            pw = float(bg_rect.get("width"))
            ph = float(bg_rect.get("height"))
            y_range = y_hi - y_lo
            ly = (y_hi - ref_val) / y_range * ph
            if 0 <= ly <= ph:
                line = ET.SubElement(plot_group, f"{{{ns}}}line")
                line.set("x1", "0")
                line.set("y1", f"{ly:.1f}")
                line.set("x2", str(pw))
                line.set("y2", f"{ly:.1f}")
                line.set("stroke", ref_line_color)
                line.set("stroke-width", "3")
                line.set("stroke-dasharray", "18,10")
                line.set("opacity", "0.7")

    png_images.append(cairosvg.svg2png(bytestring=ET.tostring(root), output_width=4800, output_height=1300))

# Compose final image
mag_img = Image.open(io.BytesIO(png_images[0]))
phase_img = Image.open(io.BytesIO(png_images[1]))
combined = Image.new("RGB", (4800, 2700), "white")
combined.paste(mag_img, (0, 50))
combined.paste(phase_img, (0, 1350))

# Divider between panels
draw = ImageDraw.Draw(combined)
draw.line([(140, 1350), (4740, 1350)], fill="#DEE2E6", width=2)

# Margin annotations
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
except OSError:
    font = ImageFont.load_default()

parts = []
if phase_margin is not None:
    parts.append(f"Phase Margin: {phase_margin:.1f}°")
if gain_margin is not None:
    parts.append(f"Gain Margin: {gain_margin:.1f} dB")
if parts:
    draw.text((3500, 68), "  |  ".join(parts), fill=annotation_color, font=font)

combined.save("plot.png", dpi=(300, 300))

# HTML version
mag_svg = mag_chart.render(is_unicode=True).replace('<?xml version="1.0" encoding="utf-8"?>', "")
phase_svg = phase_chart.render(is_unicode=True).replace('<?xml version="1.0" encoding="utf-8"?>', "")

html_content = (
    "<!DOCTYPE html>\n<html>\n<head>\n"
    "    <title>bode-basic · pygal · pyplots.ai</title>\n"
    "    <style>\n"
    "        body { font-family: 'Helvetica Neue', sans-serif; background: white; margin: 0; padding: 20px; }\n"
    "        .container { max-width: 1200px; margin: 0 auto; }\n"
    "        .chart { width: 100%; margin: 10px 0; }\n"
    "    </style>\n</head>\n<body>\n"
    "    <div class='container'>\n"
    f"        <div class='chart'>{mag_svg}</div>\n"
    f"        <div class='chart'>{phase_svg}</div>\n"
    "    </div>\n</body>\n</html>"
)

with open("plot.html", "w") as f:
    f.write(html_content)

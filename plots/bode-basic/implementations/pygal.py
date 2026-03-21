"""pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: pygal 3.1.0 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-21
"""

import io

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

# Log-transform x-axis
log_freq = np.log10(frequency_hz)

# Find gain crossover: where magnitude crosses 0 dB (after resonance peak)
peak_idx = np.argmax(magnitude_db)
peak_db = magnitude_db[peak_idx]
peak_freq = frequency_hz[peak_idx]
zero_crossings = np.where(np.diff(np.sign(magnitude_db[peak_idx:])))[0]
if len(zero_crossings) > 0:
    gc_idx = peak_idx + zero_crossings[0]
    gc_freq = frequency_hz[gc_idx]
    gc_phase = phase_deg[gc_idx]
    phase_margin = 180 + gc_phase
else:
    gc_freq = None
    phase_margin = None

# Find phase crossover: where phase crosses -180°
pc_indices = np.where(np.diff(np.sign(phase_deg + 180)))[0]
gain_margin = -magnitude_db[pc_indices[0]] if len(pc_indices) > 0 else None

# Color palette
line_blue = "#306998"
line_blue_light = "#5B9BD5"
ref_red = "#C0392B"
accent_amber = "#E67E22"
bg_plot = "#F7F9FC"
text_dark = "#16213E"
grid_subtle = "#DDE1E7"
annotation_teal = "#0E6655"

# Style for magnitude panel
mag_style = Style(
    background="white",
    plot_background=bg_plot,
    foreground=text_dark,
    foreground_strong=text_dark,
    foreground_subtle=grid_subtle,
    colors=(line_blue, ref_red),
    title_font_size=52,
    label_font_size=28,
    major_label_font_size=26,
    legend_font_size=22,
    value_font_size=16,
    stroke_width=3,
    font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    title_font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    label_font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    value_font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
)

# Style for phase panel
phase_style = Style(
    background="white",
    plot_background=bg_plot,
    foreground=text_dark,
    foreground_strong=text_dark,
    foreground_subtle=grid_subtle,
    colors=(line_blue, ref_red, accent_amber),
    title_font_size=52,
    label_font_size=28,
    major_label_font_size=26,
    legend_font_size=22,
    value_font_size=16,
    stroke_width=3,
    font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    title_font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    label_font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    value_font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
)

# X-axis tick positions
x_ticks = [0.1, 0.5, 1, 5, 10, 50, 100, 500, 1000]
x_tick_log = [np.log10(v) for v in x_ticks]

# Subsample for performance
step = 2
mag_pts = [(float(log_freq[i]), float(magnitude_db[i])) for i in range(0, len(log_freq), step)]
phase_pts = [(float(log_freq[i]), float(phase_deg[i])) for i in range(0, len(log_freq), step)]

# Reference lines as pygal series (horizontal lines spanning the full x range)
x_lo, x_hi = float(log_freq[0]), float(log_freq[-1])
ref_0db = [(x_lo, 0.0), (x_hi, 0.0)]
ref_neg180 = [(x_lo, -180.0), (x_hi, -180.0)]

# Phase margin visual: vertical line segment at gain crossover frequency
phase_margin_line = None
if gc_freq is not None and phase_margin is not None:
    gc_log = np.log10(gc_freq)
    phase_margin_line = [(float(gc_log), float(gc_phase)), (float(gc_log), -180.0)]

# Magnitude chart
mag_chart = pygal.XY(
    width=4800,
    height=1300,
    style=mag_style,
    show_legend=True,
    legend_at_bottom=False,
    show_y_guides=True,
    show_x_guides=False,
    margin=25,
    margin_left=150,
    margin_right=80,
    margin_bottom=10,
    margin_top=40,
    dots_size=0,
    stroke=True,
    truncate_label=-1,
    print_values=False,
    x_value_formatter=lambda x: f"{10**x:.4g}",
    title="bode-basic \u00b7 pygal \u00b7 pyplots.ai",
    x_title="",
    y_title="Magnitude (dB)",
    range=(-100.0, 20.0),
    tooltip_border_radius=6,
)
mag_chart.x_labels = x_tick_log
mag_chart.x_labels_major = x_tick_log
mag_chart.add("Magnitude", mag_pts, show_dots=False, stroke_style={"width": 5, "linecap": "round", "linejoin": "round"})
mag_chart.add("0 dB Reference", ref_0db, show_dots=False, stroke_style={"width": 2, "dasharray": "16,8"})

# Phase chart
phase_chart = pygal.XY(
    width=4800,
    height=1300,
    style=phase_style,
    show_legend=True,
    legend_at_bottom=False,
    show_y_guides=True,
    show_x_guides=False,
    margin=25,
    margin_left=150,
    margin_right=80,
    margin_bottom=75,
    margin_top=5,
    dots_size=0,
    stroke=True,
    truncate_label=-1,
    print_values=False,
    x_value_formatter=lambda x: f"{10**x:.4g}",
    title="",
    x_title="Frequency (Hz)",
    y_title="Phase (\u00b0)",
    range=(-200.0, 10.0),
    tooltip_border_radius=6,
)
phase_chart.x_labels = x_tick_log
phase_chart.x_labels_major = x_tick_log
phase_chart.add("Phase", phase_pts, show_dots=False, stroke_style={"width": 5, "linecap": "round", "linejoin": "round"})
phase_chart.add(
    "\u2013180\u00b0 Reference", ref_neg180, show_dots=False, stroke_style={"width": 2, "dasharray": "16,8"}
)
if phase_margin_line:
    phase_chart.add(
        f"Phase Margin: {phase_margin:.1f}\u00b0",
        phase_margin_line,
        show_dots=True,
        dots_size=6,
        stroke_style={"width": 3, "dasharray": "6,4"},
    )

# Render to PNG via cairosvg
mag_png = cairosvg.svg2png(bytestring=mag_chart.render(), output_width=4800, output_height=1300)
phase_png = cairosvg.svg2png(bytestring=phase_chart.render(), output_width=4800, output_height=1300)

# Compose dual-panel image
mag_img = Image.open(io.BytesIO(mag_png))
phase_img = Image.open(io.BytesIO(phase_png))
combined = Image.new("RGB", (4800, 2700), "white")
combined.paste(mag_img, (0, 50))
combined.paste(phase_img, (0, 1350))

# Draw panel divider
draw = ImageDraw.Draw(combined)
draw.line([(150, 1355), (4720, 1355)], fill="#CFD8DC", width=2)

# Prominent annotation block
try:
    font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
    font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
except OSError:
    font_lg = ImageFont.load_default()
    font_sm = font_lg

# Resonance peak annotation on magnitude panel
draw.text((3800, 80), f"Resonance: {peak_db:.1f} dB @ {peak_freq:.1f} Hz", fill=line_blue, font=font_sm)

# Phase margin annotation
if phase_margin is not None:
    draw.text(
        (3800, 1380), f"Phase Margin: {phase_margin:.1f}\u00b0 @ {gc_freq:.1f} Hz", fill=annotation_teal, font=font_lg
    )

combined.save("plot.png", dpi=(300, 300))

# HTML version leveraging pygal's native SVG interactivity
mag_svg = mag_chart.render(is_unicode=True).replace('<?xml version="1.0" encoding="utf-8"?>', "")
phase_svg = phase_chart.render(is_unicode=True).replace('<?xml version="1.0" encoding="utf-8"?>', "")

html_content = (
    "<!DOCTYPE html>\n<html>\n<head>\n"
    "    <title>bode-basic \u00b7 pygal \u00b7 pyplots.ai</title>\n"
    "    <style>\n"
    "        body { font-family: 'Helvetica Neue', sans-serif; background: #F7F9FC;"
    " margin: 0; padding: 40px 20px; }\n"
    "        .container { max-width: 1200px; margin: 0 auto; }\n"
    "        .chart { width: 100%; margin: 8px 0; }\n"
    "        .divider { border: none; border-top: 1px solid #CFD8DC; margin: 0; }\n"
    "    </style>\n</head>\n<body>\n"
    "    <div class='container'>\n"
    f"        <div class='chart'>{mag_svg}</div>\n"
    "        <hr class='divider'/>\n"
    f"        <div class='chart'>{phase_svg}</div>\n"
    "    </div>\n</body>\n</html>"
)

with open("plot.html", "w") as f:
    f.write(html_content)

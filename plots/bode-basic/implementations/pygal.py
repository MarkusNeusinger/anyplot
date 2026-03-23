""" pyplots.ai
bode-basic: Bode Plot for Frequency Response
Library: pygal 3.1.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-21
"""

import io

import cairosvg
import numpy as np
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Data — Third-order system with resonance: G(s) = K*wn^2 / ((s + p)*(s^2 + 2*zeta*wn*s + wn^2))
# Natural frequency 5 Hz, damping 0.2 (clear resonance), extra pole at 50 Hz
# This gives finite gain margin AND phase margin for a complete Bode demonstration
frequency_hz = np.logspace(-1, 3, 500)
omega = 2 * np.pi * frequency_hz
wn = 2 * np.pi * 5.0
zeta = 0.2
p = 2 * np.pi * 50.0
s = 1j * omega
G = (wn**2 * p) / ((s + p) * (s**2 + 2 * zeta * wn * s + wn**2))

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

# Color palette — refined for publication quality
line_blue = "#306998"
ref_red = "#B03A2E"
margin_purple = "#6C3483"
margin_teal = "#117A65"
bg_canvas = "#FAFCFF"
bg_plot = "#F0F4F8"
text_dark = "#1A1F36"
grid_subtle = "#D5DAE2"
accent_gold = "#D4A017"

# Shared style settings with larger legend for readability
_style_common = {
    "background": bg_canvas,
    "plot_background": bg_plot,
    "foreground": text_dark,
    "foreground_strong": text_dark,
    "foreground_subtle": grid_subtle,
    "title_font_size": 56,
    "label_font_size": 30,
    "major_label_font_size": 28,
    "legend_font_size": 30,
    "value_font_size": 18,
    "stroke_width": 3,
    "font_family": "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    "title_font_family": "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    "label_font_family": "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    "value_font_family": "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    "legend_font_family": "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    "opacity": 1.0,
    "opacity_hover": 0.85,
    "transition": "200ms ease-in",
}

mag_style = Style(**_style_common, colors=(line_blue, ref_red, margin_purple, "#7F8C8D"))
phase_style = Style(**_style_common, colors=(line_blue, ref_red, margin_teal, "#7F8C8D"))

# X-axis tick positions — major decade labels only for clean look
x_ticks_major = [0.1, 1, 10, 100, 1000]
x_ticks_minor = [0.5, 5, 50, 500]
x_tick_major_log = [np.log10(v) for v in x_ticks_major]
x_tick_all_log = sorted([np.log10(v) for v in x_ticks_major + x_ticks_minor])

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

# Gain margin visual: vertical line segment at phase crossover frequency
gain_margin_line = None
pc_freq = None
if len(pc_indices) > 0 and gain_margin is not None:
    pc_freq = frequency_hz[pc_indices[0]]
    pc_log = np.log10(pc_freq)
    pc_mag = magnitude_db[pc_indices[0]]
    gain_margin_line = [(float(pc_log), float(pc_mag)), (float(pc_log), 0.0)]


# Custom tooltip formatter for engineering context
def mag_formatter(x, y):
    freq = 10**x
    return f"{freq:.2g} Hz → {y:.1f} dB"


def phase_formatter(x, y):
    freq = 10**x
    return f"{freq:.2g} Hz → {y:.1f}°"


# Magnitude chart — secondary y-guides for the -3dB bandwidth line
mag_chart = pygal.XY(
    width=4800,
    height=1350,
    style=mag_style,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    show_y_guides=True,
    show_x_guides=False,
    margin=25,
    margin_left=160,
    margin_right=90,
    margin_bottom=100,
    margin_top=45,
    dots_size=0,
    stroke=True,
    truncate_label=-1,
    print_values=False,
    x_value_formatter=lambda x: f"{10**x:.4g}",
    tooltip_fancy_mode=True,
    tooltip_border_radius=8,
    title="bode-basic · pygal · pyplots.ai",
    x_title="",
    y_title="Magnitude (dB)",
    range=(-100.0, 20.0),
    interpolate="cubic",
    show_minor_x_labels=True,
)
mag_chart.x_labels = x_tick_all_log
mag_chart.x_labels_major = x_tick_major_log
mag_chart.add(
    "Magnitude",
    mag_pts,
    show_dots=False,
    formatter=mag_formatter,
    stroke_style={"width": 5, "linecap": "round", "linejoin": "round"},
)
mag_chart.add("0 dB Reference", ref_0db, show_dots=False, stroke_style={"width": 2, "dasharray": "18,10"})
if gain_margin_line:
    mag_chart.add(
        f"Gain Margin: {gain_margin:.1f} dB @ {pc_freq:.1f} Hz",
        gain_margin_line,
        show_dots=True,
        dots_size=8,
        stroke_style={"width": 3, "dasharray": "8,5"},
    )

# -3 dB bandwidth line for additional engineering context
bw_3db = [(x_lo, -3.0), (x_hi, -3.0)]
mag_chart.add("−3 dB Bandwidth", bw_3db, show_dots=False, stroke_style={"width": 1.5, "dasharray": "4,6"})

# Phase chart
phase_chart = pygal.XY(
    width=4800,
    height=1350,
    style=phase_style,
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    show_y_guides=True,
    show_x_guides=False,
    margin=25,
    margin_left=160,
    margin_right=90,
    margin_bottom=100,
    margin_top=10,
    dots_size=0,
    stroke=True,
    truncate_label=-1,
    print_values=False,
    x_value_formatter=lambda x: f"{10**x:.4g}",
    tooltip_fancy_mode=True,
    tooltip_border_radius=8,
    title="",
    x_title="Frequency (Hz)",
    y_title="Phase (°)",
    range=(-280.0, 10.0),
    interpolate="cubic",
    show_minor_x_labels=True,
)
phase_chart.x_labels = x_tick_all_log
phase_chart.x_labels_major = x_tick_major_log
phase_chart.add(
    "Phase",
    phase_pts,
    show_dots=False,
    formatter=phase_formatter,
    stroke_style={"width": 5, "linecap": "round", "linejoin": "round"},
)
phase_chart.add("–180° Reference", ref_neg180, show_dots=False, stroke_style={"width": 2, "dasharray": "18,10"})
if phase_margin_line:
    phase_chart.add(
        f"Phase Margin: {phase_margin:.1f}° @ {gc_freq:.1f} Hz",
        phase_margin_line,
        show_dots=True,
        dots_size=8,
        stroke_style={"width": 3, "dasharray": "8,5"},
    )

# -90° reference for additional context
ref_neg90 = [(x_lo, -90.0), (x_hi, -90.0)]
phase_chart.add("–90° Reference", ref_neg90, show_dots=False, stroke_style={"width": 1.5, "dasharray": "4,6"})

# Render to PNG via cairosvg
mag_png = cairosvg.svg2png(bytestring=mag_chart.render(), output_width=4800, output_height=1350)
phase_png = cairosvg.svg2png(bytestring=phase_chart.render(), output_width=4800, output_height=1350)

# Compose dual-panel image
mag_img = Image.open(io.BytesIO(mag_png))
phase_img = Image.open(io.BytesIO(phase_png))
combined = Image.new("RGB", (4800, 2700), bg_canvas)
combined.paste(mag_img, (0, 0))
combined.paste(phase_img, (0, 1350))

# Draw refined panel divider with gradient effect
draw = ImageDraw.Draw(combined)
draw.line([(160, 1350), (4710, 1350)], fill="#B0BEC5", width=1)
draw.line([(160, 1351), (4710, 1351)], fill="#CFD8DC", width=1)

# Load fonts for annotation overlay
try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
    font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
    font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
except OSError:
    font_title = ImageFont.load_default()
    font_body = font_title
    font_label = font_title

# Draw annotation panel on magnitude chart — rounded rectangle background
ann_x, ann_y = 3200, 60
ann_w, ann_h = 1500, 200
draw.rounded_rectangle(
    [(ann_x, ann_y), (ann_x + ann_w, ann_y + ann_h)], radius=16, fill="#FFFFFF", outline="#D5DAE2", width=2
)

# Resonance peak annotation
draw.text(
    (ann_x + 24, ann_y + 16), f"▲ Resonance Peak: {peak_db:.1f} dB @ {peak_freq:.1f} Hz", fill=line_blue, font=font_body
)

# Gain margin annotation
if gain_margin is not None and pc_freq is not None:
    draw.text(
        (ann_x + 24, ann_y + 64),
        f"◆ Gain Margin: {gain_margin:.1f} dB @ {pc_freq:.1f} Hz",
        fill=margin_purple,
        font=font_title,
    )
else:
    draw.text((ann_x + 24, ann_y + 64), "◆ Gain Margin: ∞", fill=margin_purple, font=font_title)

# System description
draw.text((ann_x + 24, ann_y + 124), "H(s): 3rd-order, ωn=5 Hz, ζ=0.2", fill="#5D6D7E", font=font_label)

# Phase margin annotation panel
ann2_x, ann2_y = 3200, 1410
ann2_w, ann2_h = 1500, 130
draw.rounded_rectangle(
    [(ann2_x, ann2_y), (ann2_x + ann2_w, ann2_y + ann2_h)], radius=16, fill="#FFFFFF", outline="#D5DAE2", width=2
)

if phase_margin is not None:
    draw.text(
        (ann2_x + 24, ann2_y + 16),
        f"◆ Phase Margin: {phase_margin:.1f}° @ {gc_freq:.1f} Hz",
        fill=margin_teal,
        font=font_title,
    )
    stability = "Stable" if phase_margin > 0 else "Unstable"
    stability_color = "#1E8449" if phase_margin > 0 else "#C0392B"
    draw.text(
        (ann2_x + 24, ann2_y + 72), f"System Status: {stability} (PM > 0°)", fill=stability_color, font=font_label
    )

combined.save("plot.png", dpi=(300, 300))

# HTML version leveraging pygal's native SVG interactivity with tooltips
mag_svg = mag_chart.render(is_unicode=True).replace('<?xml version="1.0" encoding="utf-8"?>', "")
phase_svg = phase_chart.render(is_unicode=True).replace('<?xml version="1.0" encoding="utf-8"?>', "")

html_content = (
    "<!DOCTYPE html>\n<html>\n<head>\n"
    "    <title>bode-basic · pygal · pyplots.ai</title>\n"
    "    <style>\n"
    f"        body {{ font-family: 'Helvetica Neue', sans-serif; background: {bg_canvas};"
    " margin: 0; padding: 40px 20px; }\n"
    "        .container { max-width: 1200px; margin: 0 auto; }\n"
    "        .chart { width: 100%; margin: 8px 0; }\n"
    "        .divider { border: none; border-top: 1px solid #CFD8DC; margin: 0; }\n"
    "        .info { text-align: center; color: #5D6D7E; font-size: 14px; margin-top: 12px; }\n"
    "    </style>\n</head>\n<body>\n"
    "    <div class='container'>\n"
    f"        <div class='chart'>{mag_svg}</div>\n"
    "        <hr class='divider'/>\n"
    f"        <div class='chart'>{phase_svg}</div>\n"
    "        <p class='info'>Hover over data points for frequency/value details</p>\n"
    "    </div>\n</body>\n</html>"
)

with open("plot.html", "w") as f:
    f.write(html_content)

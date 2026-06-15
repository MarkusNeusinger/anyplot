""" anyplot.ai
audiogram-clinical: Clinical Audiogram
Library: pygal 3.1.0 | Python 3.13.13
Quality: 74/100 | Created: 2026-06-15
"""

import os
import sys


# Remove the script's own directory from sys.path to prevent shadowing the pygal package
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Semantic exception: audiology convention — right ear = red, left ear = blue
# Imprint matte red (#AE3030) for right ear; Imprint blue (#4467A3) for left ear
# Severity boundary lines reuse INK_MUTED so they sit behind the main data
PALETTE = ("#AE3030", "#4467A3", INK_MUTED, INK_MUTED, INK_MUTED, INK_MUTED, INK_MUTED, INK_MUTED)

title_str = "audiogram-clinical · python · pygal · anyplot.ai"
n_chars = len(title_str)
ratio = 67 / n_chars if n_chars > 67 else 1.0
title_font_size = max(44, round(66 * ratio))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=PALETTE,
    title_font_size=title_font_size,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=3.0,
)

# Data: noise-induced sensorineural hearing loss with classic 4 kHz notch
freq_labels = ["125", "250", "500", "1k", "2k", "4k", "8k"]
n_freqs = len(freq_labels)

# Right ear thresholds (dB HL) — O marker, red
threshold_right = [10, 15, 20, 20, 25, 65, 55]
# Left ear thresholds (dB HL) — X marker, blue
threshold_left = [15, 20, 25, 25, 35, 55, 50]

# Negate for inverted y-axis: 0 dB HL (best) at top, 120 dB HL (worst) at bottom
right_neg = [-t for t in threshold_right]
left_neg = [-t for t in threshold_left]

# Severity band boundaries per the spec (negated chart values)
severity_boundaries = [
    ("Normal / Mild (25 dB HL)", -25),
    ("Mild / Moderate (40 dB HL)", -40),
    ("Moderate / Mod-Severe (55 dB HL)", -55),
    ("Mod-Severe / Severe (70 dB HL)", -70),
    ("Severe / Profound (90 dB HL)", -90),
]

# Y-axis labels every 10 dB HL (0 → 120), displayed as absolute values
y_label_items = [{"label": str(abs(v)), "value": v} for v in range(-120, 1, 10)]

chart = pygal.Line(
    width=2400,
    height=2400,
    style=custom_style,
    title=title_str,
    x_title="Frequency (Hz)",
    y_title="Hearing Level (dB HL)",
    show_dots=True,
    dots_size=7,
    show_x_guides=True,
    show_y_guides=True,
    range=(-120, 10),
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
)

chart.x_labels = freq_labels
chart.y_labels = y_label_items

# Main audiogram data
chart.add("Right Ear (O)", right_neg)
chart.add("Left Ear (X)", left_neg)

# Severity band boundary reference lines — thin dashed, muted color
dash_style = {"width": 1.5, "dasharray": "8 4"}
for label, value in severity_boundaries:
    chart.add(label, [value] * n_freqs, stroke_style=dash_style, dots_size=1)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())

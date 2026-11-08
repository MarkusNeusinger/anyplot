""" anyplot.ai
audiogram-clinical: Clinical Audiogram
Library: pygal 3.1.3 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-08
"""

import os
import sys


# Remove the script's own directory from sys.path to prevent shadowing the pygal package
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.18)" if THEME == "light" else "rgba(240,239,232,0.18)"

# Semantic exception: audiology convention overrides Imprint categorical order
RIGHT_COLOR = "#AE3030"  # Imprint matte red — right ear, circles (O)
LEFT_COLOR = "#4467A3"  # Imprint blue — left ear, crosses (X)

# Severity bands (upper edge in dB HL), an ordered scale: light tints of imprint_seq, green (normal) to blue (profound)
BANDS = [
    ("Normal (−10–25 dB)", 25),
    ("Mild (26–40 dB)", 40),
    ("Moderate (41–55 dB)", 55),
    ("Moderately severe (56–70 dB)", 70),
    ("Severe (71–90 dB)", 90),
    ("Profound (>90 dB)", 120),
]
AXIS_TOP = -10

# Data — noise-induced sensorineural hearing loss with a bilateral 4 kHz notch
frequencies = [125, 250, 500, 1000, 2000, 4000, 8000]
freq_labels = ["125", "250", "500", "1k", "2k", "4k", "8k"]
threshold_right = [10, 15, 20, 20, 25, 65, 55]
threshold_left = [15, 20, 25, 25, 35, 55, 50]

# Plot: frequency on a log2 axis, so the octave ticks are evenly spaced
octave = np.log2(frequencies)
x_lo, x_hi = octave.min() - 0.3, octave.max() + 0.3
y_lo, y_hi = AXIS_TOP, BANDS[-1][1]
# pygal pads the plot box by 2% of each range; fills and grid run to the padded edges
pad_x, pad_y = 0.02 * (x_hi - x_lo), 0.02 * (y_hi - y_lo)

# Band tints: imprint_seq steps blended into the page colour, deeper for worse hearing
seq_start = np.frombuffer(bytes.fromhex("009E73"), dtype=np.uint8).astype(float)
seq_end = np.frombuffer(bytes.fromhex("4467A3"), dtype=np.uint8).astype(float)
page = np.frombuffer(bytes.fromhex(PAGE_BG[1:]), dtype=np.uint8).astype(float)
depth = (0.10, 0.32) if THEME == "light" else (0.14, 0.44)  # a dark page needs more tint per step
band_fills = []
for i in range(len(BANDS)):
    step = i / (len(BANDS) - 1)
    tint = page + (depth[0] + depth[1] * step) * ((1 - step) * seq_start + step * seq_end - page)
    band_fills.append("#" + "".join(f"{round(c):02X}" for c in tint))

# Cross (X) glyphs as two strokes each; the plot area is about square, so this keeps them square
half_w = 0.07
half_h = half_w * (y_hi - y_lo) / (x_hi - x_lo)
crosses = []
for x, y in zip(octave, threshold_left, strict=True):
    crosses += [(x - half_w, y - half_h), (x + half_w, y + half_h), None]
    crosses += [(x - half_w, y + half_h), (x + half_w, y - half_h), None]

# Grid above the band fills, so it stays visible: every octave and every 10 dB
grid = []
for x in octave:
    grid += [(x, y_lo - pad_y), (x, y_hi + pad_y), None]
for y in range(y_lo, y_hi + 1, 10):
    grid += [(x_lo - pad_x, y), (x_hi + pad_x, y), None]

# Band names in each band's top left corner, where audiogram data rarely sits; symbol legend bottom right
band_labels = []
lower = y_lo
for name, upper in BANDS:
    band_labels.append({"value": (x_lo + 0.04, lower + 3.5), "label": name})
    lower = upper
key_x, key_rows = x_hi - 2.2, (y_hi - 14, y_hi - 6)
key_o = [(key_x, key_rows[0])]
key_x_glyph = [
    (key_x - half_w, key_rows[1] - half_h),
    (key_x + half_w, key_rows[1] + half_h),
    None,
    (key_x - half_w, key_rows[1] + half_h),
    (key_x + half_w, key_rows[1] - half_h),
]
key_labels = [
    {"value": (key_x + 0.12, key_rows[0]), "label": "Right ear (O)"},
    {"value": (key_x + 0.12, key_rows[1]), "label": "Left ear (X)"},
]

LABEL_FS = 40
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_SOFT,
    colors=(INK_SOFT, INK, *band_fills[::-1], RULE, RIGHT_COLOR, LEFT_COLOR, LEFT_COLOR, RIGHT_COLOR, LEFT_COLOR),
    value_colors=(INK_SOFT, INK, *[INK] * 12),
    opacity=1,
    opacity_hover=1,
    stroke_opacity=1,
    stroke_opacity_hover=1,
    stroke_width=5,
    title_font_size=66,
    label_font_size=44,
    major_label_font_size=44,
    # pygal prints a point's label value_font_size px right of it and 4/3 of that below it;
    # at 0.26 x the label size the text sits vertically centred on its point
    value_font_size=round(0.26 * LABEL_FS),
    value_label_font_size=LABEL_FS,
    tooltip_font_size=36,
)

band_series = [f".serie-{2 + i} .line" for i in range(len(BANDS))]
chart = pygal.XY(
    width=2400,
    height=2400,
    style=custom_style,
    title="audiogram-clinical · python · pygal · anyplot.ai",
    x_title="Frequency (Hz)",
    y_title="Hearing Level (dB HL)",
    show_legend=False,
    show_x_guides=False,
    show_y_guides=False,
    inverse_y_axis=True,
    xrange=(x_lo, x_hi),
    range=(y_lo, y_hi),
    zero=y_lo - pad_y,  # band fills reach up to the top of the plot box
    margin=40,
    spacing=30,
    print_labels=True,
    print_values=False,
    css=(
        "file://style.css",
        "file://graph.css",
        f"inline:{', '.join(band_series)} {{ stroke-width: 0 !important; }}",
        "inline:.serie-8 .line { stroke-width: 2px !important; }",
        f"inline:.serie-9 .dot, .serie-12 .dot {{ fill: {PAGE_BG} !important; stroke-width: 5px !important; }}",
        "inline:.plot_title { font-weight: bold; }",
    ),
)
chart.x_labels = [{"value": x, "label": label} for x, label in zip(octave, freq_labels, strict=True)]
chart.y_labels = list(range(y_lo, y_hi + 1, 10))

# Labels first (their css indices are fixed above); text is always drawn above the marks
chart.add("Band names", band_labels, stroke=False, dots_size=0)
chart.add("Key", key_labels, stroke=False, dots_size=0)
# Each band fills from its lower edge up to the top of the axis; deepest first, so each later band covers the rest
for name, upper in BANDS[::-1]:
    edge = y_hi + pad_y if upper == y_hi else upper
    chart.add(name, [(x_lo - pad_x, edge), (x_hi + pad_x, edge)], fill=True, show_dots=False)
chart.add("Grid", grid, show_dots=False, allow_interruptions=True)
chart.add("Right ear", list(zip(octave, threshold_right, strict=True)), dots_size=16)
chart.add("Left ear", list(zip(octave, threshold_left, strict=True)), show_dots=False, stroke_style={"dasharray": "22, 12"})
chart.add("Left ear (X)", crosses, show_dots=False, allow_interruptions=True)
chart.add("Key O", key_o, stroke=False, dots_size=16)
chart.add("Key X", key_x_glyph, show_dots=False, allow_interruptions=True)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())

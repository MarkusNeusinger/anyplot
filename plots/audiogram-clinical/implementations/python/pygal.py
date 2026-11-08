""" anyplot.ai
audiogram-clinical: Clinical Audiogram
Library: pygal 3.1.3 | Python 3.14.10
Quality: 87/100 | Updated: 2026-11-08
"""

import os
import sys


# Remove the script's own directory from sys.path to prevent shadowing the pygal package
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir in sys.path:
    sys.path.remove(_script_dir)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
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

# Columns: set these to your table's column names
FREQUENCY = "Frequency (Hz)"  # role: frequency
THRESHOLD_RIGHT = "Right ear (dB HL)"  # role: threshold_right
THRESHOLD_LEFT = "Left ear (dB HL)"  # role: threshold_left

# Data: noise-induced sensorineural hearing loss with a bilateral 4 kHz notch; replace with your own table
df = pd.DataFrame(
    {
        FREQUENCY: [125, 250, 500, 1000, 2000, 4000, 8000],
        THRESHOLD_RIGHT: [10, 15, 20, 20, 25, 65, 55],
        THRESHOLD_LEFT: [15, 20, 25, 25, 35, 55, 50],
    }
)

# Plot: frequency on a log2 axis, so the octave ticks are evenly spaced
df = df.dropna(subset=[FREQUENCY]).sort_values(FREQUENCY)
frequencies = df[FREQUENCY].to_numpy(dtype=float)
octave = np.log2(frequencies)
freq_labels = [f"{f / 1000:g}k" if f >= 1000 else f"{f:g}" for f in frequencies]
right = df[[FREQUENCY, THRESHOLD_RIGHT]].dropna()
left = df[[FREQUENCY, THRESHOLD_LEFT]].dropna()
right_points = list(
    zip(np.log2(right[FREQUENCY].to_numpy(dtype=float)).tolist(), right[THRESHOLD_RIGHT].tolist(), strict=True)
)
left_points = list(
    zip(np.log2(left[FREQUENCY].to_numpy(dtype=float)).tolist(), left[THRESHOLD_LEFT].tolist(), strict=True)
)

x_lo, x_hi = octave.min() - 0.3, octave.max() + 0.3
levels = df[[THRESHOLD_RIGHT, THRESHOLD_LEFT]].to_numpy(dtype=float)
y_lo = int(min(AXIS_TOP, 10 * np.floor(np.nanmin(levels) / 10)))
y_hi = int(max(BANDS[-1][1], 10 * np.ceil(np.nanmax(levels) / 10)))
# pygal pads the plot box by 2% of each range; fills and grid run to the padded edges
pad_x, pad_y = 0.02 * (x_hi - x_lo), 0.02 * (y_hi - y_lo)

# Band tints: imprint_seq steps blended into the page colour, deeper for worse hearing
seq_start = np.frombuffer(bytes.fromhex("009E73"), dtype=np.uint8).astype(float)
seq_end = np.frombuffer(bytes.fromhex("4467A3"), dtype=np.uint8).astype(float)
page = np.frombuffer(bytes.fromhex(PAGE_BG[1:]), dtype=np.uint8).astype(float)
# A dark page needs a stronger first tint and larger steps to tell adjacent bands apart
depth = (0.10, 0.32) if THEME == "light" else (0.20, 0.46)
band_fills = []
for i in range(len(BANDS)):
    step = i / (len(BANDS) - 1)
    strength = depth[0] + depth[1] * (step if THEME == "light" else np.sqrt(step))
    tint = page + strength * ((1 - step) * seq_start + step * seq_end - page)
    band_fills.append("#" + "".join(f"{round(c):02X}" for c in tint))

# Cross (X) glyphs as two strokes each; the plot area is about square, so this keeps them square
half_w = 0.07
half_h = half_w * (y_hi - y_lo) / (x_hi - x_lo)
crosses = []
for x, y in left_points:
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
    x_title=FREQUENCY,
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
chart.x_labels = [{"value": x, "label": label} for x, label in zip(octave.tolist(), freq_labels, strict=True)]
chart.y_labels = list(range(y_lo, y_hi + 1, 10))

# Labels first (their css indices are fixed above); text is always drawn above the marks
chart.add("Band names", band_labels, stroke=False, dots_size=0)
chart.add("Key", key_labels, stroke=False, dots_size=0)
# Each band fills from its lower edge up to the top of the axis; deepest first, so each later band covers the rest
for name, upper in BANDS[::-1]:
    edge = y_hi + pad_y if upper == BANDS[-1][1] else upper
    chart.add(name, [(x_lo - pad_x, edge), (x_hi + pad_x, edge)], fill=True, show_dots=False)
chart.add("Grid", grid, show_dots=False, allow_interruptions=True)
chart.add("Right ear", right_points, dots_size=16)
chart.add("Left ear", left_points, show_dots=False, stroke_style={"dasharray": "22, 12"})
chart.add("Left ear (X)", crosses, show_dots=False, allow_interruptions=True)
chart.add("Key O", key_o, stroke=False, dots_size=16)
chart.add("Key X", key_x_glyph, show_dots=False, allow_interruptions=True)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())

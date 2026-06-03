"""anyplot.ai
piano-roll-midi: MIDI Piano Roll Visualization
Library: pygal | Python 3.13
Quality: pending | Created: 2026-06-03
"""

import os
import re
import sys


# This file is named pygal.py; remove its directory from sys.path so the
# import below resolves to the installed pygal package, not this file.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if p not in ("", _here)]

import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
ROW_SHADE = "#E5E0D0" if THEME == "light" else "#252521"  # black-key row tint

# Velocity colormap: Imprint soft(blue)→loud(red) matches spec "piano→forte" semantic
VELOCITY_COLORS = ("#4467A3", "#2ABCCD", "#009E73", "#BD8233", "#AE3030")

# Data: D-minor jazz ii–V–I–vi (Dm7–G7–Cmaj7–Am7), 8 measures, 4/4 time
# Three layers: bass (bottom), chord voicings (middle), melody (top)
notes = [
    # M1-2: Dm7 — bass D3, chord D4/F4/A4, melody D5→F5
    {"start": 0, "duration": 4, "pitch": 50, "velocity": 70},
    {"start": 4, "duration": 4, "pitch": 50, "velocity": 65},
    {"start": 0, "duration": 2, "pitch": 62, "velocity": 75},
    {"start": 0, "duration": 2, "pitch": 65, "velocity": 72},
    {"start": 0, "duration": 2, "pitch": 69, "velocity": 72},
    {"start": 2, "duration": 2, "pitch": 62, "velocity": 70},
    {"start": 2, "duration": 2, "pitch": 65, "velocity": 68},
    {"start": 4, "duration": 2, "pitch": 62, "velocity": 73},
    {"start": 4, "duration": 2, "pitch": 65, "velocity": 70},
    {"start": 6, "duration": 2, "pitch": 62, "velocity": 68},
    {"start": 6, "duration": 2, "pitch": 65, "velocity": 65},
    {"start": 0, "duration": 1, "pitch": 74, "velocity": 95},
    {"start": 1, "duration": 1, "pitch": 72, "velocity": 88},
    {"start": 2, "duration": 2, "pitch": 69, "velocity": 100},
    {"start": 4, "duration": 1.5, "pitch": 72, "velocity": 105},
    {"start": 5.5, "duration": 0.5, "pitch": 74, "velocity": 88},
    {"start": 6, "duration": 2, "pitch": 77, "velocity": 110},
    # M3-4: G7 — bass G3, chord B3/D4/F4, melody climbs to F5 (dominant tension)
    {"start": 8, "duration": 4, "pitch": 55, "velocity": 72},
    {"start": 12, "duration": 4, "pitch": 55, "velocity": 67},
    {"start": 8, "duration": 2, "pitch": 59, "velocity": 78},
    {"start": 8, "duration": 2, "pitch": 62, "velocity": 75},
    {"start": 8, "duration": 2, "pitch": 65, "velocity": 73},
    {"start": 10, "duration": 2, "pitch": 59, "velocity": 73},
    {"start": 10, "duration": 2, "pitch": 62, "velocity": 70},
    {"start": 12, "duration": 2, "pitch": 59, "velocity": 76},
    {"start": 12, "duration": 2, "pitch": 62, "velocity": 73},
    {"start": 14, "duration": 2, "pitch": 59, "velocity": 70},
    {"start": 14, "duration": 2, "pitch": 62, "velocity": 68},
    {"start": 8, "duration": 1, "pitch": 77, "velocity": 105},
    {"start": 9, "duration": 0.5, "pitch": 76, "velocity": 92},
    {"start": 9.5, "duration": 0.5, "pitch": 74, "velocity": 87},
    {"start": 10, "duration": 2, "pitch": 72, "velocity": 100},
    {"start": 12, "duration": 1, "pitch": 74, "velocity": 108},
    {"start": 13, "duration": 1, "pitch": 76, "velocity": 95},
    {"start": 14, "duration": 2, "pitch": 77, "velocity": 112},
    # M5-6: Cmaj7 — bass C3, chord C4/E4/G4, melody resolves E5→B4
    {"start": 16, "duration": 4, "pitch": 48, "velocity": 75},
    {"start": 20, "duration": 4, "pitch": 48, "velocity": 70},
    {"start": 16, "duration": 2, "pitch": 60, "velocity": 80},
    {"start": 16, "duration": 2, "pitch": 64, "velocity": 77},
    {"start": 16, "duration": 2, "pitch": 67, "velocity": 77},
    {"start": 18, "duration": 2, "pitch": 60, "velocity": 75},
    {"start": 18, "duration": 2, "pitch": 64, "velocity": 73},
    {"start": 20, "duration": 2, "pitch": 60, "velocity": 78},
    {"start": 20, "duration": 2, "pitch": 64, "velocity": 75},
    {"start": 22, "duration": 2, "pitch": 60, "velocity": 72},
    {"start": 22, "duration": 2, "pitch": 64, "velocity": 70},
    {"start": 16, "duration": 2, "pitch": 76, "velocity": 100},
    {"start": 18, "duration": 1, "pitch": 74, "velocity": 92},
    {"start": 19, "duration": 1, "pitch": 72, "velocity": 88},
    {"start": 20, "duration": 2, "pitch": 71, "velocity": 95},
    {"start": 22, "duration": 1, "pitch": 72, "velocity": 90},
    {"start": 23, "duration": 1, "pitch": 74, "velocity": 87},
    # M7-8: Am7 — bass A2, chord A3/C4/E4, melody winds down to D4
    {"start": 24, "duration": 4, "pitch": 45, "velocity": 72},
    {"start": 28, "duration": 4, "pitch": 45, "velocity": 68},
    {"start": 24, "duration": 2, "pitch": 57, "velocity": 78},
    {"start": 24, "duration": 2, "pitch": 60, "velocity": 75},
    {"start": 24, "duration": 2, "pitch": 64, "velocity": 75},
    {"start": 26, "duration": 2, "pitch": 57, "velocity": 73},
    {"start": 26, "duration": 2, "pitch": 60, "velocity": 72},
    {"start": 28, "duration": 2, "pitch": 57, "velocity": 76},
    {"start": 28, "duration": 2, "pitch": 60, "velocity": 73},
    {"start": 30, "duration": 2, "pitch": 57, "velocity": 70},
    {"start": 30, "duration": 2, "pitch": 60, "velocity": 68},
    {"start": 24, "duration": 1.5, "pitch": 72, "velocity": 95},
    {"start": 25.5, "duration": 0.5, "pitch": 71, "velocity": 83},
    {"start": 26, "duration": 1, "pitch": 69, "velocity": 88},
    {"start": 27, "duration": 1, "pitch": 67, "velocity": 82},
    {"start": 28, "duration": 2, "pitch": 65, "velocity": 78},
    {"start": 30, "duration": 2, "pitch": 62, "velocity": 75},
]

CHROMATIC = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
BLACK_KEYS = {1, 3, 6, 8, 10}

min_pitch = min(n["pitch"] for n in notes)
max_pitch = max(n["pitch"] for n in notes)
pitch_range = list(range(min_pitch, max_pitch + 1))
pitch_names = {p: f"{CHROMATIC[p % 12]}{p // 12 - 1}" for p in pitch_range}
total_beats = max(n["start"] + n["duration"] for n in notes)

velocity_bands = [
    ("pp (65-74)", 65, 74),
    ("p (75-84)", 75, 84),
    ("mp (85-94)", 85, 94),
    ("f (95-104)", 95, 104),
    ("ff (105-115)", 105, 115),
]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=VELOCITY_COLORS,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=38,
    font_family="'DejaVu Sans', Arial, sans-serif",
)

chart = pygal.XY(
    width=3200,
    height=1800,
    style=custom_style,
    title="piano-roll-midi · python · pygal · anyplot.ai",
    x_title="Time (beats)",
    y_title="Pitch",
    show_x_guides=True,
    show_y_guides=True,
    show_dots=False,
    stroke=True,
    fill=False,
    allow_interruptions=True,
    margin_left=140,
    margin_right=60,
    margin_top=80,
    margin_bottom=130,
    legend_at_bottom=True,
    legend_box_size=36,
    x_labels=list(range(0, int(total_beats) + 1, 4)),
    truncate_legend=-1,
)

chart.y_labels = [{"value": p, "label": pitch_names[p]} for p in pitch_range]

for band_name, v_lo, v_hi in velocity_bands:
    pts = []
    for n in notes:
        if v_lo <= n["velocity"] <= v_hi:
            pts.append((n["start"], n["pitch"]))
            pts.append((n["start"] + n["duration"], n["pitch"]))
            pts.append(None)
    chart.add(band_name, pts if pts else [])

# SVG post-processing: inject alternating black-key row shading behind the data
svg_bytes = chart.render()
svg_str = svg_bytes.decode("utf-8")

try:
    # pygal renders guide lines as <path d="M0 {y} h{width}" class="guide line">
    # (horizontal = y-axis guides; vertical guides use "v" not "h")
    h_guides = []
    for m in re.finditer(r"<path\b([^>]+)>", svg_str):
        tag = m.group(1)
        if "guide" not in tag:
            continue
        d_m = re.search(r'\bd="M[\d.]+\s+([\d.]+)\s+h([\d.]+)"', tag)
        if d_m:
            y, w = float(d_m.group(1)), float(d_m.group(2))
            if w > 200:
                h_guides.append((y, 0.0, w))

    h_guides = sorted({(round(y, 3), x1, w) for y, x1, w in h_guides}, key=lambda t: t[0])

    if len(h_guides) == len(pitch_range):
        pitch_sorted = sorted(pitch_range)
        # SVG y increases downward; smallest y = top = highest pitch
        y_map = {pitch_sorted[-(i + 1)]: h_guides[i][0] for i in range(len(pitch_sorted))}
        plot_w = h_guides[0][2]
        row_h = abs(h_guides[1][0] - h_guides[0][0]) if len(h_guides) > 1 else 36.0

        rects = "".join(
            f'<rect x="0" y="{y_map[p] - row_h / 2:.3f}" '
            f'width="{plot_w:.1f}" height="{row_h:.3f}" '
            f'fill="{ROW_SHADE}"/>\n'
            for p in pitch_range
            if p % 12 in BLACK_KEYS and p in y_map
        )

        # Inject shading before first series group (inside the plot transform group)
        svg_str = re.sub(r'(<g\b[^>]*\bclass="[^"]*\bserie\b[^"]*"[^>]*>)', rects + r"\1", svg_str, count=1)
except Exception:
    pass  # graceful degradation: render without black-key shading

import cairosvg


cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), write_to=f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(svg_str)

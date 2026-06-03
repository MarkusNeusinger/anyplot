"""anyplot.ai
piano-roll-midi: MIDI Piano Roll Visualization
Library: pygal 3.1.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-06-03
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

# SVG post-processing: inject grid layers and row shading behind the data
svg_bytes = chart.render()
svg_str = svg_bytes.decode("utf-8")

try:
    h_guides = []  # (y, width) — horizontal pitch-row guides
    v_guides = []  # (x, y0, height) — vertical measure guides

    for m in re.finditer(r"<path\b([^>]+)>", svg_str):
        tag = m.group(1)
        if "guide" not in tag:
            continue
        # Horizontal guide: M{x} {y} h{w}
        hm = re.search(r'\bd="M[\d.]+\s+([\d.]+)\s+h([\d.]+)"', tag)
        if hm:
            y, w = float(hm.group(1)), float(hm.group(2))
            if w > 200:
                h_guides.append((y, w))
        # Vertical guide: M{x} {y0} v{h}  OR  M{x} {y0} L{x} {y1}
        vm = re.search(r'\bd="M([\d.]+)\s+([\d.]+)\s+(?:v([\d.]+)|L[\d.]+\s+([\d.]+))"', tag)
        if vm:
            x, y0 = float(vm.group(1)), float(vm.group(2))
            h = float(vm.group(3)) if vm.group(3) else float(vm.group(4)) - y0
            if h > 200:
                v_guides.append((x, y0, h))

    h_guides = sorted({(round(y, 3), w) for y, w in h_guides}, key=lambda t: t[0])
    v_guides = sorted({(round(x, 1), round(y0, 1), round(h, 1)) for x, y0, h in v_guides}, key=lambda t: t[0])

    inject_parts = []

    # 1. Black-key row shading
    if len(h_guides) == len(pitch_range) and len(h_guides) > 1:
        pitch_sorted = sorted(pitch_range)
        y_map = {pitch_sorted[-(i + 1)]: h_guides[i][0] for i in range(len(pitch_sorted))}
        plot_w = h_guides[0][1]
        row_h = abs(h_guides[1][0] - h_guides[0][0])
        for p in pitch_range:
            if p % 12 in BLACK_KEYS and p in y_map:
                inject_parts.append(
                    f'<rect x="0" y="{y_map[p] - row_h / 2:.3f}" '
                    f'width="{plot_w:.1f}" height="{row_h:.3f}" '
                    f'fill="{ROW_SHADE}"/>'
                )

    # 2. G7 dominant climax highlight (measures 3-4, beats 8-16): amber wash
    # Emphasizes the harmonic tension peak of the ii-V-I-vi progression
    if len(v_guides) >= 5:
        gy0, gh = v_guides[0][1], v_guides[0][2]
        cx1, cx2 = v_guides[2][0], v_guides[4][0]
        climax_fill = "rgba(221,204,119,0.10)" if THEME == "light" else "rgba(221,204,119,0.07)"
        inject_parts.append(
            f'<rect x="{cx1:.2f}" y="{gy0:.2f}" width="{cx2 - cx1:.2f}" height="{gh:.2f}" fill="{climax_fill}"/>'
        )

    # 3. Beat subdivision lines (quarter-note grid, thinner/muted vs measure lines)
    BEAT_COLOR = "#C0B8A8" if THEME == "light" else "#3C3C37"
    if len(v_guides) >= 2:
        dx_per_measure = v_guides[1][0] - v_guides[0][0]
        dx_per_beat = dx_per_measure / 4
        gy0, gh = v_guides[0][1], v_guides[0][2]
        for i, (mx, _, _) in enumerate(v_guides):
            if i < len(v_guides) - 1:
                for b in range(1, 4):
                    bx = mx + b * dx_per_beat
                    inject_parts.append(
                        f'<line x1="{bx:.2f}" y1="{gy0:.2f}" x2="{bx:.2f}" y2="{gy0 + gh:.2f}" '
                        f'stroke="{BEAT_COLOR}" stroke-width="1.5" stroke-dasharray="6,4"/>'
                    )

    # 4. Measure boundary lines re-injected above row shading (stronger than beat lines)
    if len(v_guides) >= 1:
        gy0, gh = v_guides[0][1], v_guides[0][2]
        for mx, _, _ in v_guides:
            inject_parts.append(
                f'<line x1="{mx:.2f}" y1="{gy0:.2f}" x2="{mx:.2f}" y2="{gy0 + gh:.2f}" '
                f'stroke="{INK_MUTED}" stroke-width="2.5"/>'
            )

    if inject_parts:
        inject_svg = "\n".join(inject_parts) + "\n"
        svg_str = re.sub(
            r'(<g\b[^>]*\bclass="[^"]*\bserie\b[^"]*"[^>]*>)', lambda mo: inject_svg + mo.group(1), svg_str, count=1
        )

except Exception:
    pass  # graceful degradation: render without custom grid/shading

import cairosvg


cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), write_to=f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(svg_str)

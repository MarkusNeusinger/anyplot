""" pyplots.ai
piano-roll-midi: MIDI Piano Roll Visualization
Library: pygal 3.1.0 | Python 3.14.3
Quality: 78/100 | Created: 2026-03-07
"""

import importlib
import re
import sys


# Prevent self-import (script name shadows pygal package)
sys.path = [p for p in sys.path if p not in ("", ".") and not p.endswith("/implementations")]
cairosvg = importlib.import_module("cairosvg")
pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style

# Data - I-V-vi-IV chord progression with melody, chords, and bass (8 measures, 4/4 time)
notes = [
    # Measure 1-2: C major
    {"start": 0, "duration": 4, "pitch": 48, "velocity": 70},
    {"start": 4, "duration": 4, "pitch": 48, "velocity": 65},
    {"start": 0, "duration": 2, "pitch": 60, "velocity": 80},
    {"start": 0, "duration": 2, "pitch": 64, "velocity": 75},
    {"start": 0, "duration": 2, "pitch": 67, "velocity": 75},
    {"start": 2, "duration": 2, "pitch": 60, "velocity": 72},
    {"start": 2, "duration": 2, "pitch": 64, "velocity": 70},
    {"start": 2, "duration": 2, "pitch": 67, "velocity": 70},
    {"start": 4, "duration": 2, "pitch": 60, "velocity": 78},
    {"start": 4, "duration": 2, "pitch": 64, "velocity": 73},
    {"start": 4, "duration": 2, "pitch": 67, "velocity": 73},
    {"start": 6, "duration": 2, "pitch": 60, "velocity": 70},
    {"start": 6, "duration": 2, "pitch": 64, "velocity": 68},
    {"start": 0, "duration": 1, "pitch": 72, "velocity": 100},
    {"start": 1, "duration": 1, "pitch": 74, "velocity": 95},
    {"start": 2, "duration": 2, "pitch": 76, "velocity": 105},
    {"start": 4, "duration": 1.5, "pitch": 79, "velocity": 110},
    {"start": 5.5, "duration": 0.5, "pitch": 77, "velocity": 85},
    {"start": 6, "duration": 2, "pitch": 76, "velocity": 100},
    # Measure 3-4: G major
    {"start": 8, "duration": 4, "pitch": 55, "velocity": 70},
    {"start": 12, "duration": 4, "pitch": 55, "velocity": 65},
    {"start": 8, "duration": 2, "pitch": 59, "velocity": 80},
    {"start": 8, "duration": 2, "pitch": 62, "velocity": 75},
    {"start": 8, "duration": 2, "pitch": 67, "velocity": 75},
    {"start": 10, "duration": 2, "pitch": 59, "velocity": 70},
    {"start": 10, "duration": 2, "pitch": 62, "velocity": 70},
    {"start": 10, "duration": 2, "pitch": 67, "velocity": 68},
    {"start": 12, "duration": 2, "pitch": 59, "velocity": 75},
    {"start": 12, "duration": 2, "pitch": 62, "velocity": 72},
    {"start": 14, "duration": 2, "pitch": 59, "velocity": 68},
    {"start": 14, "duration": 2, "pitch": 62, "velocity": 66},
    {"start": 8, "duration": 1, "pitch": 74, "velocity": 100},
    {"start": 9, "duration": 0.5, "pitch": 76, "velocity": 90},
    {"start": 9.5, "duration": 0.5, "pitch": 74, "velocity": 85},
    {"start": 10, "duration": 2, "pitch": 71, "velocity": 105},
    {"start": 12, "duration": 2, "pitch": 72, "velocity": 95},
    {"start": 14, "duration": 1, "pitch": 74, "velocity": 100},
    {"start": 15, "duration": 1, "pitch": 71, "velocity": 90},
    # Measure 5-6: A minor
    {"start": 16, "duration": 4, "pitch": 57, "velocity": 70},
    {"start": 20, "duration": 4, "pitch": 57, "velocity": 65},
    {"start": 16, "duration": 2, "pitch": 60, "velocity": 80},
    {"start": 16, "duration": 2, "pitch": 64, "velocity": 75},
    {"start": 16, "duration": 2, "pitch": 69, "velocity": 75},
    {"start": 18, "duration": 2, "pitch": 60, "velocity": 70},
    {"start": 18, "duration": 2, "pitch": 64, "velocity": 70},
    {"start": 18, "duration": 2, "pitch": 69, "velocity": 68},
    {"start": 20, "duration": 2, "pitch": 60, "velocity": 75},
    {"start": 20, "duration": 2, "pitch": 64, "velocity": 72},
    {"start": 20, "duration": 2, "pitch": 69, "velocity": 72},
    {"start": 22, "duration": 2, "pitch": 60, "velocity": 68},
    {"start": 22, "duration": 2, "pitch": 64, "velocity": 66},
    {"start": 16, "duration": 1.5, "pitch": 72, "velocity": 100},
    {"start": 17.5, "duration": 0.5, "pitch": 71, "velocity": 85},
    {"start": 18, "duration": 1, "pitch": 69, "velocity": 95},
    {"start": 19, "duration": 1, "pitch": 72, "velocity": 100},
    {"start": 20, "duration": 2, "pitch": 76, "velocity": 110},
    {"start": 22, "duration": 1, "pitch": 74, "velocity": 95},
    {"start": 23, "duration": 1, "pitch": 72, "velocity": 90},
    # Measure 7-8: F major
    {"start": 24, "duration": 4, "pitch": 53, "velocity": 70},
    {"start": 28, "duration": 4, "pitch": 53, "velocity": 65},
    {"start": 24, "duration": 2, "pitch": 60, "velocity": 80},
    {"start": 24, "duration": 2, "pitch": 65, "velocity": 75},
    {"start": 24, "duration": 2, "pitch": 69, "velocity": 75},
    {"start": 26, "duration": 2, "pitch": 60, "velocity": 70},
    {"start": 26, "duration": 2, "pitch": 65, "velocity": 70},
    {"start": 26, "duration": 2, "pitch": 69, "velocity": 68},
    {"start": 28, "duration": 2, "pitch": 60, "velocity": 75},
    {"start": 28, "duration": 2, "pitch": 65, "velocity": 72},
    {"start": 28, "duration": 2, "pitch": 69, "velocity": 72},
    {"start": 30, "duration": 2, "pitch": 60, "velocity": 68},
    {"start": 30, "duration": 2, "pitch": 65, "velocity": 66},
    {"start": 24, "duration": 1, "pitch": 77, "velocity": 105},
    {"start": 25, "duration": 1, "pitch": 76, "velocity": 95},
    {"start": 26, "duration": 2, "pitch": 74, "velocity": 100},
    {"start": 28, "duration": 1, "pitch": 72, "velocity": 110},
    {"start": 29, "duration": 0.5, "pitch": 74, "velocity": 90},
    {"start": 29.5, "duration": 0.5, "pitch": 72, "velocity": 85},
    {"start": 30, "duration": 2, "pitch": 72, "velocity": 115},
]

# Pitch helpers
chromatic = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
black_keys = {1, 3, 6, 8, 10}
min_pitch = min(n["pitch"] for n in notes)
max_pitch = max(n["pitch"] for n in notes)
num_pitches = max_pitch - min_pitch + 1
pitch_names = {p: f"{chromatic[p % 12]}{p // 12 - 1}" for p in range(min_pitch, max_pitch + 1)}
total_beats = 32

# Velocity to color (cool blue=soft to warm red=loud)
vel_min = min(n["velocity"] for n in notes)
vel_max = max(n["velocity"] for n in notes)


def vel_color(v):
    t = (v - vel_min) / (vel_max - vel_min)
    r = int(50 + 195 * t)
    g = int(90 + 70 * (1 - abs(2 * t - 1)))
    b = int(210 - 180 * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),
    title_font_size=56,
    label_font_size=24,
    major_label_font_size=24,
    legend_font_size=24,
    value_font_size=20,
    tooltip_font_size=20,
)

# Base chart - HorizontalBar for the structural framework
chart = pygal.HorizontalBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="piano-roll-midi \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=False,
    print_values=False,
    show_y_guides=False,
    show_x_guides=False,
    show_x_labels=False,
    show_y_labels=True,
    margin=50,
    spacing=12,
    range=(0, 100),
)

# Pitch names as y-labels (HorizontalBar: index 0 at bottom, last at top)
pitch_labels = [pitch_names[p] for p in range(min_pitch, max_pitch + 1)]
chart.x_labels = pitch_labels
chart.add("", [None] * num_pitches)

# Render base SVG
svg_string = chart.render().decode("utf-8")

# Extract plot area coordinates from SVG
transform_match = re.search(r'class="plot\s[^"]*"[^>]*transform="translate\(([\d.]+),\s*([\d.]+)\)"', svg_string)
if not transform_match:
    transform_match = re.search(r'transform="translate\(([\d.]+),\s*([\d.]+)\)"', svg_string)

PLOT_X = float(transform_match.group(1))
PLOT_Y = float(transform_match.group(2))

# Find plot overlay rect for dimensions
overlay_match = re.search(
    r'class="plot\s[^"]*"[^>]*>.*?<rect[^>]*class="background"[^>]*'
    r'width="([\d.]+)"[^>]*height="([\d.]+)"',
    svg_string,
    re.DOTALL,
)
if overlay_match:
    PLOT_W = float(overlay_match.group(1))
    PLOT_H = float(overlay_match.group(2))
else:
    PLOT_W = 4800 - 2 * PLOT_X
    PLOT_H = 2700 - 2 * PLOT_Y

row_height = PLOT_H / num_pitches
bar_height = row_height * 0.7

# Build SVG elements
elements = []

# Background shading for black keys
for p in range(min_pitch, max_pitch + 1):
    if (p % 12) in black_keys:
        row_idx = max_pitch - p
        y_top = PLOT_Y + row_idx * row_height
        elements.append(
            f'<rect x="{PLOT_X}" y="{y_top:.1f}" width="{PLOT_W}" '
            f'height="{row_height:.1f}" fill="#e8e8e0" opacity="0.6"/>'
        )

# Beat grid lines
for beat in range(total_beats + 1):
    x_pos = PLOT_X + (beat / total_beats) * PLOT_W
    is_measure = beat % 4 == 0
    stroke_w = 2.5 if is_measure else 1
    stroke_color = "#999" if is_measure else "#ccc"
    dash = "" if is_measure else ' stroke-dasharray="6,4"'
    elements.append(
        f'<line x1="{x_pos:.1f}" y1="{PLOT_Y}" x2="{x_pos:.1f}" '
        f'y2="{PLOT_Y + PLOT_H:.1f}" stroke="{stroke_color}" '
        f'stroke-width="{stroke_w}"{dash}/>'
    )

# Measure number labels
for measure in range(1, 9):
    beat = (measure - 1) * 4
    x_pos = PLOT_X + (beat / total_beats) * PLOT_W
    elements.append(
        f'<text x="{x_pos + 8:.1f}" y="{PLOT_Y - 10:.1f}" '
        f'font-family="Consolas, monospace" font-size="22" fill="#666" '
        f'text-anchor="start">M{measure}</text>'
    )

# X-axis beat labels
for beat in range(0, total_beats + 1, 4):
    x_pos = PLOT_X + (beat / total_beats) * PLOT_W
    elements.append(
        f'<text x="{x_pos:.1f}" y="{PLOT_Y + PLOT_H + 35:.1f}" '
        f'font-family="Consolas, monospace" font-size="24" fill="#333" '
        f'text-anchor="middle">{beat}</text>'
    )

# X-axis title
elements.append(
    f'<text x="{PLOT_X + PLOT_W / 2:.1f}" y="{PLOT_Y + PLOT_H + 75:.1f}" '
    f'font-family="Consolas, monospace" font-size="28" fill="#333" '
    f'text-anchor="middle">Time (beats)</text>'
)

# Note rectangles
for n in notes:
    row_idx = max_pitch - n["pitch"]
    y_center = PLOT_Y + (row_idx + 0.5) * row_height
    y_top = y_center - bar_height / 2
    x_start = PLOT_X + (n["start"] / total_beats) * PLOT_W
    x_end = PLOT_X + ((n["start"] + n["duration"]) / total_beats) * PLOT_W
    width = x_end - x_start
    color = vel_color(n["velocity"])
    label = f"{pitch_names[n['pitch']]} vel:{n['velocity']}"
    elements.append(
        f'<rect x="{x_start:.1f}" y="{y_top:.1f}" width="{width:.1f}" '
        f'height="{bar_height:.1f}" fill="{color}" rx="4" ry="4" opacity="0.9">'
        f"<title>{label}</title></rect>"
    )

# Velocity legend (color bar)
legend_x = PLOT_X + PLOT_W - 300
legend_y = PLOT_Y - 50
legend_w = 200
legend_h = 16
num_stops = 20
for i in range(num_stops):
    t_val = vel_min + (vel_max - vel_min) * i / num_stops
    seg_x = legend_x + (i / num_stops) * legend_w
    seg_w = legend_w / num_stops + 1
    elements.append(
        f'<rect x="{seg_x:.1f}" y="{legend_y:.1f}" width="{seg_w:.1f}" height="{legend_h}" fill="{vel_color(t_val)}" />'
    )
elements.append(
    f'<text x="{legend_x - 8:.1f}" y="{legend_y + 13:.1f}" '
    f'font-family="Consolas, monospace" font-size="18" fill="#666" '
    f'text-anchor="end">pp</text>'
)
elements.append(
    f'<text x="{legend_x + legend_w + 8:.1f}" y="{legend_y + 13:.1f}" '
    f'font-family="Consolas, monospace" font-size="18" fill="#666" '
    f'text-anchor="start">ff</text>'
)
elements.append(
    f'<text x="{legend_x + legend_w / 2:.1f}" y="{legend_y - 6:.1f}" '
    f'font-family="Consolas, monospace" font-size="18" fill="#666" '
    f'text-anchor="middle">Velocity</text>'
)

# Inject elements and clean up
all_elements = "\n".join(elements)
svg_output = svg_string.replace("</svg>", f"{all_elements}\n</svg>")
svg_output = svg_output.replace(">No data<", "><")

# Save
with open("plot.html", "w") as f:
    f.write(svg_output)

cairosvg.svg2png(bytestring=svg_output.encode(), write_to="plot.png")

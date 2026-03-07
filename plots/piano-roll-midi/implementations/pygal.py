""" pyplots.ai
piano-roll-midi: MIDI Piano Roll Visualization
Library: pygal 3.1.0 | Python 3.14.3
Quality: 77/100 | Created: 2026-03-07
"""

import os
import sys


# Script name shadows pygal package - temporarily adjust path
_script_dir = os.path.dirname(os.path.abspath(__file__))
_original_path = sys.path[:]
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir]
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


sys.path = _original_path

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
min_pitch = min(n["pitch"] for n in notes)
max_pitch = max(n["pitch"] for n in notes)
pitch_names = {p: f"{chromatic[p % 12]}{p // 12 - 1}" for p in range(min_pitch, max_pitch + 1)}

# Velocity bands with viridis-like colorblind-safe palette
velocity_bands = [
    ("pp (65-74)", 65, 74),
    ("p (75-84)", 75, 84),
    ("mp (85-94)", 85, 94),
    ("f (95-104)", 95, 104),
    ("ff (105-115)", 105, 115),
]
band_colors = ("#440154", "#31688e", "#35b779", "#90d743", "#fde725")

# Style
custom_style = Style(
    background="white",
    plot_background="#f8f8f6",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#dddddd",
    colors=band_colors,
    title_font_size=56,
    label_font_size=22,
    major_label_font_size=22,
    legend_font_size=24,
    value_font_size=18,
    tooltip_font_size=18,
    stroke_width=38,
    font_family="Consolas, 'Courier New', monospace",
)

# Create XY chart with allow_interruptions for None-separated note segments
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="piano-roll-midi \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Time (beats)",
    y_title="Pitch",
    show_x_guides=True,
    show_y_guides=True,
    show_dots=False,
    stroke=True,
    fill=False,
    allow_interruptions=True,
    margin_left=120,
    margin_bottom=120,
    legend_at_bottom=True,
    legend_box_size=24,
    x_labels=[0, 4, 8, 12, 16, 20, 24, 28, 32],
    truncate_legend=-1,
)

# Y-axis: pitch labels at each MIDI note value
chart.y_labels = [{"value": p, "label": pitch_names[p]} for p in range(min_pitch, max_pitch + 1)]

# Add notes grouped by velocity band as XY series
# Each note = horizontal line segment: (start, pitch) -> (end, pitch)
# None values create breaks between notes (via allow_interruptions)
for band_name, v_lo, v_hi in velocity_bands:
    points = []
    for n in notes:
        if v_lo <= n["velocity"] <= v_hi:
            points.append((n["start"], n["pitch"]))
            points.append((n["start"] + n["duration"], n["pitch"]))
            points.append(None)
    chart.add(band_name, points if points else [])

# Render using pygal's native output methods
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")

"""anyplot.ai
heatmap-chromagram: Music Chromagram (Pitch Class Distribution over Time)
Library: pygal 3.1.3 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-28
"""

import math
import os
import sys
from itertools import pairwise
from xml.etree import ElementTree as etree

import cairosvg
import numpy as np
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Imprint sequential ramp for fields (colored cells that fill the plot), per theme
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.369, "#009E73"), (0.803, "#024582"), (1.0, "#351E45")]
    if THEME == "light"
    else [(0.0, "#404C02"), (0.487, "#009E73"), (1.0, "#CDD9FF")]
)

# This file is named pygal.py: drop its own folder from the import path so the package wins
sys.path = [p for p in sys.path if not p.endswith("/implementations/python")]
from pygal import Line  # noqa: E402
from pygal.style import Style  # noqa: E402


# Constants
ENERGY_RANGE = (0.0, 1.0)  # chroma energy is normalised to 0..1


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Columns: set these to your table's column names
TIME = "Time (seconds)"  # role: time
PITCH = "Pitch Class"  # role: pitch_class
ENERGY = "Energy"  # role: energy
CHORD = "Chord"  # role: extra
NUMERAL = "Roman numeral"  # role: extra

# Data: C major → G major → A minor → F major chord progression
# Replace this block with your own long table, for example df = pd.read_csv("chromagram.csv")
np.random.seed(42)
pitch_classes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
n_frames = 80
chroma = np.random.uniform(0.02, 0.12, (len(pitch_classes), n_frames))
for f in range(0, 20):
    chroma[0, f] += np.random.uniform(0.7, 0.95)
    chroma[4, f] += np.random.uniform(0.5, 0.75)
    chroma[7, f] += np.random.uniform(0.55, 0.8)
for f in range(20, 40):
    chroma[7, f] += np.random.uniform(0.7, 0.95)
    chroma[11, f] += np.random.uniform(0.5, 0.75)
    chroma[2, f] += np.random.uniform(0.55, 0.8)
for f in range(40, 60):
    chroma[9, f] += np.random.uniform(0.7, 0.95)
    chroma[0, f] += np.random.uniform(0.5, 0.75)
    chroma[4, f] += np.random.uniform(0.55, 0.8)
for f in range(60, 80):
    chroma[5, f] += np.random.uniform(0.7, 0.95)
    chroma[9, f] += np.random.uniform(0.5, 0.75)
    chroma[0, f] += np.random.uniform(0.55, 0.8)
for f in range(n_frames - 1):
    chroma[:, f + 1] = 0.3 * chroma[:, f] + 0.7 * chroma[:, f + 1]
chroma = np.clip(chroma, 0, 1)

chords = [("C major", "I"), ("G major", "V"), ("A minor", "vi"), ("F major", "IV")]
frame_chord = [chords[f // 20] for f in range(n_frames)]
df = pd.DataFrame(
    {
        TIME: np.tile(np.arange(n_frames) * 0.1, len(pitch_classes)),
        PITCH: np.repeat(pitch_classes, n_frames),
        ENERGY: chroma.ravel(),
        CHORD: [frame_chord[f][0] for _ in pitch_classes for f in range(n_frames)],
        NUMERAL: [frame_chord[f][1] for _ in pitch_classes for f in range(n_frames)],
    }
)

# Plot
table = df.pivot_table(index=PITCH, columns=TIME, values=ENERGY, sort=False, dropna=False)
table = table.iloc[::-1]  # first pitch class at the bottom
frames = df.drop_duplicates(TIME).reset_index(drop=True)
runs = (frames[CHORD] != frames[CHORD].shift()).cumsum()
chord_regions = [
    {"start": int(g.index[0]), "end": int(g.index[-1]) + 1, "label": g[CHORD].iloc[0]}
    for _, g in frames.groupby(runs, sort=False)
]
subtitle = "Chord progression: " + " – ".join(frames.drop_duplicates(CHORD)[NUMERAL])
n_rows, n_cols = table.shape
time_labels = [f"{t:.1f}" for t in table.columns]

WIDTH, HEIGHT = 3200, 1800
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    font_family="sans-serif",
)

# pygal supplies the page, style and title; the heatmap is laid into its SVG tree
chart = Line(
    width=WIDTH,
    height=HEIGHT,
    style=custom_style,
    title="heatmap-chromagram · python · pygal · anyplot.ai",
    show_legend=False,
    show_x_labels=False,
    show_y_labels=False,
    show_x_guides=False,
    show_y_guides=False,
    show_dots=False,
)
chart.add("chromagram", [0])
root = chart.render_tree()


def svg_node(parent, tag, **attrs):
    """Append an SVG element to parent; a trailing underscore escapes reserved names (class_)."""
    return etree.SubElement(parent, tag, {k.rstrip("_"): str(v) for k, v in attrs.items()})


m_l, m_r, y0 = 245, 300, 290
cw = (WIDTH - m_l - m_r) / n_cols
gh = 1240
ch = gh / n_rows
gw = n_cols * cw
x0 = m_l
lo, hi = ENERGY_RANGE

node = svg_node(root, "g", class_="chroma-heatmap")

# Chord headers and dashed dividers
for reg in chord_regions:
    rx = x0 + reg["start"] * cw
    rw = (reg["end"] - reg["start"]) * cw
    t = svg_node(node, "text", x=rx + rw / 2, y=y0 - 20)
    t.set("text-anchor", "middle")
    t.set("fill", INK_MUTED)
    t.set("style", "font-size:42px;font-weight:bold;font-family:sans-serif;font-style:italic")
    t.text = reg["label"]
    if reg["start"] > 0:
        svg_node(node, "line", x1=rx, y1=y0 - 5, x2=rx, y2=y0 + gh + 5, stroke=INK_MUTED, fill="none").set(
            "style", "stroke-width:2;stroke-dasharray:8,6"
        )

# Subtitle below the x-axis title
st = svg_node(node, "text", x=x0 + gw / 2, y=y0 + gh + 200)
st.set("text-anchor", "middle")
st.set("fill", INK_MUTED)
st.set("style", "font-size:40px;font-family:sans-serif;font-style:italic")
st.text = subtitle

# Heatmap cells with SVG tooltip titles
for i in range(n_rows):
    row = svg_node(node, "g", class_=f"row-{i}")
    for j in range(n_cols):
        v = table.iloc[i, j]
        rect = svg_node(
            row,
            "rect",
            x=x0 + j * cw,
            y=y0 + i * ch,
            width=cw + 0.5,
            height=ch + 0.5,
            fill=ramp_color(SEQ_FIELDS, (v - lo) / (hi - lo)),
            stroke="none",
        )
        svg_node(rect, "title").text = f"{table.index[i]} @ {time_labels[j]}s — Energy: {v:.3f}"

# Thin horizontal pitch-row separators
for i in range(1, n_rows):
    svg_node(
        node, "line", x1=x0, y1=y0 + i * ch, x2=x0 + gw, y2=y0 + i * ch, stroke=PAGE_BG, fill="none", opacity="0.3"
    ).set("style", "stroke-width:1.5")

# Heatmap border
svg_node(node, "rect", x=x0, y=y0, width=gw, height=gh, fill="none", stroke=INK_MUTED, opacity="0.5")

# Y-axis: pitch class labels
row_font = min(44, int(ch * 0.6))
for i, label in enumerate(table.index):
    t = svg_node(node, "text", x=x0 - 18, y=y0 + i * ch + ch / 2 + row_font * 0.35)
    t.set("text-anchor", "end")
    t.set("fill", INK)
    t.set("style", f"font-size:{row_font}px;font-weight:600;font-family:sans-serif")
    t.text = str(label)

# Y-axis title (rotated)
yt_x, yt_y = x0 - 200, y0 + gh / 2
t = svg_node(node, "text", x=yt_x, y=yt_y)
t.set("text-anchor", "middle")
t.set("fill", INK)
t.set("style", "font-size:48px;font-weight:bold;font-family:sans-serif")
t.set("transform", f"rotate(-90, {yt_x}, {yt_y})")
t.text = PITCH

# X-axis: time tick labels
for j in range(0, n_cols, max(1, n_cols // 10)):
    t = svg_node(node, "text", x=x0 + j * cw + cw / 2, y=y0 + gh + 58)
    t.set("text-anchor", "middle")
    t.set("fill", INK)
    t.set("style", "font-size:44px;font-family:sans-serif")
    t.text = time_labels[j]

# X-axis title
t = svg_node(node, "text", x=x0 + gw / 2, y=y0 + gh + 135)
t.set("text-anchor", "middle")
t.set("fill", INK)
t.set("style", "font-size:48px;font-weight:bold;font-family:sans-serif")
t.text = TIME

# Colorbar gradient (high at top, low at bottom)
cb_w, n_seg = 50, 60
cb_h = gh * 0.85
cb_x, cb_y = x0 + gw + 50, y0 + (gh - cb_h) / 2
seg_h = cb_h / n_seg
for s in range(n_seg):
    svg_node(
        node,
        "rect",
        x=cb_x,
        y=cb_y + s * seg_h,
        width=cb_w,
        height=seg_h + 1,
        fill=ramp_color(SEQ_FIELDS, 1.0 - s / (n_seg - 1)),
    )
svg_node(node, "rect", x=cb_x, y=cb_y, width=cb_w, height=cb_h, fill="none", stroke=INK_MUTED, opacity="0.5")

for frac in (0.0, 0.5, 1.0):
    t = svg_node(node, "text", x=cb_x + cb_w + 15, y=cb_y + frac * cb_h + 36 * 0.35)
    t.set("fill", INK)
    t.set("style", "font-size:36px;font-family:sans-serif")
    t.text = f"{hi - frac * (hi - lo):.1f}"

t = svg_node(node, "text", x=cb_x + cb_w / 2, y=cb_y - 25)
t.set("text-anchor", "middle")
t.set("fill", INK)
t.set("style", "font-size:40px;font-weight:bold;font-family:sans-serif")
t.text = ENERGY

# Save
svg_bytes = etree.tostring(root, encoding="utf-8")
with open(f"plot-{THEME}.svg", "wb") as f:
    f.write(svg_bytes)
cairosvg.svg2png(bytestring=svg_bytes, write_to=f"plot-{THEME}.png", output_width=WIDTH, output_height=HEIGHT)

with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(
        "<!DOCTYPE html>\n<html>\n<head>\n"
        '    <meta charset="utf-8">\n'
        "    <title>heatmap-chromagram - python - pygal - anyplot.ai</title>\n"
        "    <style>\n"
        f"        body {{ margin: 0; display: flex; justify-content: center;"
        f" align-items: center; min-height: 100vh; background: {PAGE_BG}; }}\n"
        "        .chart { max-width: 100%; height: auto; }\n"
        "    </style>\n"
        "</head>\n<body>\n"
        '    <figure class="chart">\n' + svg_bytes.decode("utf-8") + "\n    </figure>\n</body>\n</html>\n"
    )

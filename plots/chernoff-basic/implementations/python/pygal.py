""" anyplot.ai
chernoff-basic: Chernoff Faces for Multivariate Data
Library: pygal 3.1.3 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-09
"""

import os
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: one face color per car, in canonical order
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")
EYE_WHITE, PUPIL = "#FAF8F1", "#1A1A17"  # same in both themes, so the eyes never invert

# Constants: facial features in the order the variables drive them
FEATURES = ["Face width", "Face height", "Eye size", "Eye spacing", "Mouth curve", "Nose length", "Eyebrow slant"]

# Columns: set these to your table's column names
CAR = "Car"  # role: observation_id
METRICS = [
    "Engine power (hp)",
    "Fuel efficiency (mpg)",
    "Safety rating (stars)",
    "Comfort (1-10)",
    "Reliability (%)",
    "Price value (1-10)",
    "Handling (lateral g)",
]  # role: variable_

# Data: replace this block with your own table, for example df = pd.read_csv("cars.csv")
df = pd.DataFrame(
    {
        CAR: ["Aurora Sedan", "Ridgeback SUV", "Vortex GT", "Pebble City", "Regent Luxe"],
        METRICS[0]: [190, 260, 420, 130, 330],
        METRICS[1]: [34, 24, 21, 40, 26],
        METRICS[2]: [4.5, 4.0, 3.5, 4.0, 5.0],
        METRICS[3]: [7.0, 7.5, 5.0, 6.0, 9.5],
        METRICS[4]: [88, 80, 72, 92, 84],
        METRICS[5]: [7.5, 6.0, 4.5, 9.0, 5.0],
        METRICS[6]: [0.85, 0.78, 1.05, 0.82, 0.90],
    }
)

# Plot: reads only df and the constants above
WIDTH, HEIGHT = 3200, 1800
mapping = list(zip(FEATURES, METRICS, strict=False))  # a table with fewer variables leaves features neutral
values = df[[metric for _, metric in mapping]].apply(pd.to_numeric, errors="coerce")
span = values.max() - values.min()
normalized = np.full((len(df), len(FEATURES)), 0.5)
normalized[:, : len(mapping)] = ((values - values.min()) / span.where(span > 0)).fillna(0.5).to_numpy()
names = [str(name) for name in df[CAR]]
n_faces = len(names)

title = "Car Performance Comparison · chernoff-basic · python · pygal · anyplot.ai"
title_size = round(66 * min(1.0, 67 / len(title)))

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_size,
    legend_font_size=44,
    font_family="DejaVu Sans, sans-serif",
)

# pygal draws the canvas, the title and the car legend; the faces go on top of it
chart = pygal.XY(
    width=WIDTH,
    height=HEIGHT,
    style=custom_style,
    title=title,
    legend_at_bottom=True,
    legend_at_bottom_columns=min(n_faces, 6),
    legend_box_size=40,
    show_x_guides=False,
    show_y_guides=False,
    show_x_labels=False,
    show_y_labels=False,
    show_dots=False,
    margin=40,
    margin_left=160,
    margin_right=160,
    no_data_text="",
)
for name in names:
    chart.add(name, [None])

svg_ns = "http://www.w3.org/2000/svg"
ET.register_namespace("", svg_ns)
svg_tree = ET.fromstring(chart.render())
faces_group = ET.SubElement(svg_tree, f"{{{svg_ns}}}g", {"id": "chernoff-faces"})

# Grid layout: one cell per face; the free height between title and legend is split into equal gaps
side_margin = 100
key_cols = 2
key_font, key_line = 52, 80
key_h = key_font * 0.8 + int(np.ceil(len(mapping) / key_cols)) * key_line + 12
cols = max(min(n_faces, 6), int(np.ceil(np.sqrt(n_faces * 16 / 9))))
rows = int(np.ceil(n_faces / cols))
cell_w = (WIDTH - 2 * side_margin) / cols
label_size = round(min(56, max(24, cell_w * 0.09)))
content_top, content_bottom = 85, 1705
face_size = min(cell_w * 0.92 / 0.9, ((content_bottom - content_top - key_h - 240) / rows - label_size * 2) / 1.1)
row_h = face_size * 1.1 + label_size * 2
gap = (content_bottom - content_top - rows * row_h - key_h) / 3
grid_top = content_top + gap
line_w = max(2.0, face_size / 60)

for i, (name, feature) in enumerate(zip(names, normalized, strict=True)):
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
    cx = side_margin + (i % cols + 0.5) * cell_w
    cy = grid_top + (i // cols) * row_h + face_size * 0.55

    # Facial feature parameters, each driven by one normalized variable and sized to its face
    face_rx = face_size * (0.6 + feature[0] * 0.4) * 0.45
    face_ry = face_size * (0.6 + feature[1] * 0.4) * 0.55
    eye_r = face_rx * (0.12 + feature[2] * 0.14)
    eye_dx = face_rx * (0.3 + feature[3] * 0.15)
    mouth_curve = face_ry * (-0.25 + feature[4] * 0.5)
    nose_length = face_ry * (0.15 + feature[5] * 0.25)
    brow_slant = -20 + feature[6] * 40

    face = ET.SubElement(faces_group, f"{{{svg_ns}}}g", {"id": f"face-{i}"})
    ET.SubElement(
        face,
        f"{{{svg_ns}}}ellipse",
        {
            "cx": f"{cx}",
            "cy": f"{cy}",
            "rx": f"{face_rx}",
            "ry": f"{face_ry}",
            "fill": color,
            "fill-opacity": "0.3",
            "stroke": color,
            "stroke-width": f"{line_w * 1.2}",
        },
    )

    eye_y = cy - face_ry * 0.2
    brow_len = eye_r * 2.2
    brow_y = eye_y - eye_r - face_ry * 0.08
    slant = np.tan(np.radians(brow_slant)) * brow_len * 0.5
    for side in (-1, 1):
        eye_x = cx + side * eye_dx
        ET.SubElement(
            face,
            f"{{{svg_ns}}}circle",
            {
                "cx": f"{eye_x}",
                "cy": f"{eye_y}",
                "r": f"{eye_r}",
                "fill": EYE_WHITE,
                "stroke": INK,
                "stroke-width": f"{line_w * 0.8}",
            },
        )
        ET.SubElement(
            face, f"{{{svg_ns}}}circle", {"cx": f"{eye_x}", "cy": f"{eye_y}", "r": f"{eye_r * 0.4}", "fill": PUPIL}
        )
        # Eyebrows mirror each other so the face stays symmetric
        ET.SubElement(
            face,
            f"{{{svg_ns}}}line",
            {
                "x1": f"{eye_x - brow_len * 0.5}",
                "y1": f"{brow_y + side * slant}",
                "x2": f"{eye_x + brow_len * 0.5}",
                "y2": f"{brow_y - side * slant}",
                "stroke": INK,
                "stroke-width": f"{line_w * 1.2}",
                "stroke-linecap": "round",
            },
        )

    ET.SubElement(
        face,
        f"{{{svg_ns}}}line",
        {
            "x1": f"{cx}",
            "y1": f"{cy - nose_length * 0.3}",
            "x2": f"{cx}",
            "y2": f"{cy + nose_length * 0.5}",
            "stroke": INK,
            "stroke-width": f"{line_w}",
            "stroke-linecap": "round",
        },
    )

    mouth_y = cy + face_ry * 0.45
    mouth_w = face_rx * 0.55
    ET.SubElement(
        face,
        f"{{{svg_ns}}}path",
        {
            "d": f"M {cx - mouth_w} {mouth_y} Q {cx} {mouth_y + mouth_curve} {cx + mouth_w} {mouth_y}",
            "fill": "none",
            "stroke": INK,
            "stroke-width": f"{line_w * 1.2}",
            "stroke-linecap": "round",
        },
    )

    label = ET.SubElement(
        face,
        f"{{{svg_ns}}}text",
        {
            "x": f"{cx}",
            "y": f"{cy + face_size * 0.55 + label_size * 1.3}",
            "text-anchor": "middle",
            "font-family": "DejaVu Sans, sans-serif",
            "font-size": f"{label_size}",
            "font-weight": "bold",
            "fill": INK,
        },
    )
    label.text = name

# Feature key: which variable drives which facial feature
key_top = grid_top + rows * row_h + gap + key_font * 0.8
key_title = ET.SubElement(
    svg_tree,
    f"{{{svg_ns}}}text",
    {
        "x": f"{side_margin}",
        "y": f"{key_top}",
        "font-family": "DejaVu Sans, sans-serif",
        "font-size": f"{key_font}",
        "font-weight": "bold",
        "fill": INK,
    },
)
key_title.text = "Feature key"
for i, (feature_name, metric) in enumerate(mapping):
    entry = ET.SubElement(
        svg_tree,
        f"{{{svg_ns}}}text",
        {
            "x": f"{side_margin + (i % key_cols) * (WIDTH - 2 * side_margin) / key_cols}",
            "y": f"{key_top + key_line + (i // key_cols) * key_line}",
            "font-family": "DejaVu Sans, sans-serif",
            "font-size": f"{key_font - 4}",
            "fill": INK_SOFT,
        },
    )
    entry.text = f"{feature_name} = {metric}"

# Save
final_svg = ET.tostring(svg_tree, encoding="unicode")
cairosvg.svg2png(bytestring=final_svg.encode(), write_to=f"plot-{THEME}.png", output_width=WIDTH, output_height=HEIGHT)
with open(f"plot-{THEME}.html", "w") as f:
    f.write(
        f"<!DOCTYPE html>\n<html>\n<head><meta charset='utf-8'><title>chernoff-basic · python · pygal · anyplot.ai</title></head>\n"
        f"<body style='margin:0;background:{PAGE_BG}'>\n{final_svg}\n</body>\n</html>\n"
    )

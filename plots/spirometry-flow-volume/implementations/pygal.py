"""pyplots.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: pygal 3.1.0 | Python 3.14.3
"""

import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data - Spirometry flow-volume loop for a healthy adult male
np.random.seed(42)

fvc = 4.8  # Forced Vital Capacity (L)
pef = 9.5  # Peak Expiratory Flow (L/s)
fev1 = 3.8  # Forced Expiratory Volume in 1 second (L)

# Expiratory limb: sharp rise to PEF then roughly linear decline
n_exp = 150
volume_exp = np.linspace(0, fvc, n_exp)
pef_volume = 0.15 * fvc
rise_mask = volume_exp <= pef_volume
decline_mask = ~rise_mask

flow_exp = np.zeros(n_exp)
flow_exp[rise_mask] = pef * (volume_exp[rise_mask] / pef_volume) ** 0.6
flow_exp[decline_mask] = pef * (1 - (volume_exp[decline_mask] - pef_volume) / (fvc - pef_volume)) ** 1.3
flow_exp += np.random.normal(0, 0.05, n_exp)
flow_exp = np.clip(flow_exp, 0, None)
flow_exp[0] = 0
flow_exp[-1] = 0

# Inspiratory limb: symmetric U-shaped curve (negative flow)
n_insp = 150
volume_insp = np.linspace(fvc, 0, n_insp)
pif = -6.0
flow_insp = pif * np.sin(np.pi * np.linspace(0, 1, n_insp)) ** 0.8
flow_insp += np.random.normal(0, 0.04, n_insp)
flow_insp[0] = 0
flow_insp[-1] = 0

# Predicted normal values (slightly higher capacity)
fvc_pred = 5.2
pef_pred = 10.5

volume_pred_exp = np.linspace(0, fvc_pred, 100)
pef_vol_pred = 0.15 * fvc_pred
rise_pred = volume_pred_exp <= pef_vol_pred
decline_pred = ~rise_pred
flow_pred_exp = np.zeros(100)
flow_pred_exp[rise_pred] = pef_pred * (volume_pred_exp[rise_pred] / pef_vol_pred) ** 0.6
flow_pred_exp[decline_pred] = (
    pef_pred * (1 - (volume_pred_exp[decline_pred] - pef_vol_pred) / (fvc_pred - pef_vol_pred)) ** 1.3
)
flow_pred_exp[0] = 0
flow_pred_exp[-1] = 0

volume_pred_insp = np.linspace(fvc_pred, 0, 100)
pif_pred = -6.5
flow_pred_insp = pif_pred * np.sin(np.pi * np.linspace(0, 1, 100)) ** 0.8
flow_pred_insp[0] = 0
flow_pred_insp[-1] = 0

# Style - refined medical/clinical aesthetic
measured_blue = "#1a5276"
predicted_gray = "#7b8d9e"
accent_red = "#c0392b"
text_dark = "#1c2833"
text_muted = "#566573"

custom_style = Style(
    background="white",
    plot_background="#fafcfd",
    foreground=text_dark,
    foreground_strong=text_dark,
    foreground_subtle="#dce6ec",
    colors=(measured_blue, measured_blue, predicted_gray, predicted_gray, accent_red),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=46,
    label_font_size=34,
    major_label_font_size=32,
    value_font_size=26,
    legend_font_size=28,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    major_label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    opacity=1.0,
    opacity_hover=1.0,
    guide_stroke_color="#e4eaef",
    guide_stroke_dasharray="3,5",
    major_guide_stroke_color="#d5dde3",
    major_guide_stroke_dasharray="5,4",
    stroke_opacity=1.0,
    stroke_opacity_hover=1.0,
    tooltip_font_size=24,
    tooltip_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    tooltip_border_radius=8,
)

# Chart - tightened y-axis range to reduce wasted space
chart = pygal.XY(
    width=4800,
    height=2700,
    title="spirometry-flow-volume · pygal · pyplots.ai",
    x_title="Volume (L)",
    y_title="Flow (L/s)",
    style=custom_style,
    show_dots=False,
    stroke_style={"width": 4},
    show_y_guides=True,
    show_x_guides=False,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=22,
    value_formatter=lambda x: f"{x:.1f} L/s",
    x_value_formatter=lambda x: f"{x:.1f} L",
    min_scale=5,
    max_scale=10,
    margin_bottom=80,
    margin_left=100,
    margin_right=140,
    margin_top=60,
    spacing=12,
    tooltip_fancy_mode=True,
    xrange=(-0.2, 5.8),
    range=(-8, 11),
    show_minor_x_labels=False,
    show_minor_y_labels=False,
    truncate_legend=-1,
    print_values=False,
    show_x_labels=True,
    show_y_labels=True,
    x_labels_major_count=7,
    y_labels_major_count=8,
    explicit_size=True,
    js=[],
    secondary_series=True,
)


def xy_data(vols, flows, fmt="Vol: {:.2f} L, Flow: {:.2f} L/s"):
    return [{"value": (float(v), float(f)), "label": fmt.format(v, f)} for v, f in zip(vols, flows, strict=True)]


# Measured limbs (solid, thick)
chart.add("Measured (Expiratory)", xy_data(volume_exp, flow_exp), stroke_style={"width": 5})
chart.add("Measured (Inspiratory)", xy_data(volume_insp, flow_insp), stroke_style={"width": 5})

# Predicted limbs (will be dashed via SVG post-processing)
pred_fmt = "Predicted: {:.2f} L, {:.2f} L/s"
chart.add("Predicted (Expiratory)", xy_data(volume_pred_exp, flow_pred_exp, pred_fmt), stroke_style={"width": 3.5})
chart.add("Predicted (Inspiratory)", xy_data(volume_pred_insp, flow_pred_insp, pred_fmt), stroke_style={"width": 3.5})

# PEF marker
pef_idx = np.argmax(flow_exp)
chart.add(
    "PEF",
    [{"value": (float(volume_exp[pef_idx]), float(flow_exp[pef_idx])), "label": f"PEF: {flow_exp[pef_idx]:.1f} L/s"}],
    stroke=False,
    show_dots=True,
    dots_size=14,
)

# Save interactive HTML
chart.render_to_file("plot.html")

# SVG post-processing for dashed lines, PEF annotation, and clinical values box
svg_bytes = chart.render()
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
root = ET.fromstring(svg_bytes)
ns = f"{{{SVG_NS}}}"

# Make predicted series dashed and slightly thicker for visibility
for g in root.iter(f"{ns}g"):
    cls = g.get("class", "")
    if "serie-2" in cls or "serie-3" in cls:
        for path in g.iter(f"{ns}path"):
            path.set("stroke-dasharray", "18,10")
            path.set("stroke-width", "4")

# Find PEF circle and annotate
for g in root.iter(f"{ns}g"):
    cls = g.get("class", "")
    if "serie-4" not in cls:
        continue
    for circle in g.iter(f"{ns}circle"):
        if float(circle.get("r", "0")) <= 3:
            continue
        cx, cy = float(circle.get("cx", "0")), float(circle.get("cy", "0"))
        circle.set("fill", accent_red)
        circle.set("r", "13")
        circle.set("stroke", "white")
        circle.set("stroke-width", "3")
        # PEF label with background for readability
        parent = {child: par for par in root.iter() for child in par}.get(circle)
        if parent is not None:
            bg = ET.SubElement(parent, f"{ns}rect")
            bg.set("x", f"{cx + 16:.0f}")
            bg.set("y", f"{cy - 52:.0f}")
            bg.set("width", "310")
            bg.set("height", "42")
            bg.set("rx", "6")
            bg.set("fill", "white")
            bg.set("opacity", "0.85")
            label = ET.SubElement(parent, f"{ns}text")
            label.set("x", f"{cx + 22:.0f}")
            label.set("y", f"{cy - 20:.0f}")
            label.set("font-size", "34")
            label.set("font-family", "DejaVu Sans, Helvetica, Arial, sans-serif")
            label.set("fill", accent_red)
            label.set("font-weight", "bold")
            label.text = f"PEF = {flow_exp[pef_idx]:.1f} L/s"
        break

# Clinical values box - positioned in upper-right plot area
bx, by = 4050, 320
box_w, box_h = 620, 260

# Shadow effect
shadow = ET.SubElement(root, f"{ns}rect")
shadow.set("x", f"{bx - 16}")
shadow.set("y", f"{by - 46}")
shadow.set("width", f"{box_w}")
shadow.set("height", f"{box_h}")
shadow.set("rx", "12")
shadow.set("fill", "#d5dde3")
shadow.set("opacity", "0.5")

# Main box
box = ET.SubElement(root, f"{ns}rect")
box.set("x", f"{bx - 20}")
box.set("y", f"{by - 50}")
box.set("width", f"{box_w}")
box.set("height", f"{box_h}")
box.set("rx", "12")
box.set("fill", "white")
box.set("stroke", "#b0bec5")
box.set("stroke-width", "2")

# Header with accent line
line = ET.SubElement(root, f"{ns}rect")
line.set("x", f"{bx - 20}")
line.set("y", f"{by - 50}")
line.set("width", f"{box_w}")
line.set("height", "6")
line.set("rx", "3")
line.set("fill", measured_blue)

clinical_lines = [
    ("Clinical Values", text_dark, "bold", 32),
    (f"FEV\u2081: {fev1:.1f} L  ({fev1 / fvc * 100:.0f}% FVC)", measured_blue, "normal", 29),
    (f"FVC:  {fvc:.1f} L", measured_blue, "normal", 29),
    (f"PEF:  {pef:.1f} L/s", accent_red, "bold", 29),
]
for i, (txt, color, weight, size) in enumerate(clinical_lines):
    el = ET.SubElement(root, f"{ns}text")
    el.set("x", f"{bx}")
    el.set("y", f"{by + i * 48}")
    el.set("font-size", f"{size}")
    el.set("font-family", "DejaVu Sans, Helvetica, Arial, sans-serif")
    el.set("fill", color)
    el.set("font-weight", weight)
    el.text = txt

# Zero-flow reference line for clinical context
plot_area = root.find(f".//{ns}g[@class='plot overlay']")
if plot_area is not None:
    zero_line = ET.SubElement(plot_area, f"{ns}line")
    zero_line.set("x1", "0")
    zero_line.set("y1", "0")
    zero_line.set("x2", "4800")
    zero_line.set("y2", "0")
    zero_line.set("stroke", "#b0bec5")
    zero_line.set("stroke-width", "1.5")
    zero_line.set("stroke-dasharray", "8,6")

# Render to PNG
cairosvg.svg2png(bytestring=ET.tostring(root, encoding="unicode").encode("utf-8"), write_to="plot.png")

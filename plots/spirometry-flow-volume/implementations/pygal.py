"""pyplots.ai
spirometry-flow-volume: Spirometry Flow-Volume Loop
Library: pygal | Python 3.13
Quality: pending | Created: 2026-03-18
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
# PEF occurs at ~15% of FVC
pef_volume = 0.15 * fvc
rise_mask = volume_exp <= pef_volume
decline_mask = ~rise_mask

flow_exp = np.zeros(n_exp)
# Rising phase: rapid increase to PEF
flow_exp[rise_mask] = pef * (volume_exp[rise_mask] / pef_volume) ** 0.6
# Declining phase: roughly linear decline from PEF to zero
flow_exp[decline_mask] = pef * (1 - (volume_exp[decline_mask] - pef_volume) / (fvc - pef_volume)) ** 1.3

# Add slight noise for realism
flow_exp += np.random.normal(0, 0.05, n_exp)
flow_exp = np.clip(flow_exp, 0, None)
flow_exp[0] = 0
flow_exp[-1] = 0

# Inspiratory limb: symmetric U-shaped curve (negative flow)
n_insp = 150
volume_insp = np.linspace(fvc, 0, n_insp)
pif = -6.0  # Peak Inspiratory Flow
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

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2d2d2d",
    foreground_strong="#2d2d2d",
    foreground_subtle="#e8e8e8",
    colors=("#306998", "#306998", "#999999", "#999999"),
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    title_font_size=48,
    label_font_size=36,
    major_label_font_size=34,
    value_font_size=28,
    legend_font_size=30,
    legend_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    major_label_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    value_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    opacity=1.0,
    opacity_hover=1.0,
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="4,4",
    major_guide_stroke_color="#d0d0d0",
    major_guide_stroke_dasharray="6,4",
    stroke_opacity=1.0,
    stroke_opacity_hover=1.0,
    tooltip_font_size=26,
    tooltip_font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    tooltip_border_radius=8,
)

# Chart
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
    legend_box_size=24,
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
    xrange=(-0.3, 6.0),
    range=(-8, 12),
    show_minor_x_labels=False,
    show_minor_y_labels=False,
    truncate_legend=-1,
    print_values=False,
    show_x_labels=True,
    show_y_labels=True,
    x_labels_major_count=7,
    y_labels_major_count=8,
)

# Measured expiratory limb
measured_exp_data = [
    {"value": (float(v), float(f)), "label": f"Vol: {v:.2f} L, Flow: {f:.2f} L/s"}
    for v, f in zip(volume_exp, flow_exp, strict=True)
]
chart.add("Measured (Expiratory)", measured_exp_data, stroke_style={"width": 5})

# Measured inspiratory limb
measured_insp_data = [
    {"value": (float(v), float(f)), "label": f"Vol: {v:.2f} L, Flow: {f:.2f} L/s"}
    for v, f in zip(volume_insp, flow_insp, strict=True)
]
chart.add("Measured (Inspiratory)", measured_insp_data, stroke_style={"width": 5})

# Predicted expiratory limb (dashed via SVG post-processing)
pred_exp_data = [
    {"value": (float(v), float(f)), "label": f"Predicted: {v:.2f} L, {f:.2f} L/s"}
    for v, f in zip(volume_pred_exp, flow_pred_exp, strict=True)
]
chart.add("Predicted (Expiratory)", pred_exp_data, stroke_style={"width": 3})

# Predicted inspiratory limb
pred_insp_data = [
    {"value": (float(v), float(f)), "label": f"Predicted: {v:.2f} L, {f:.2f} L/s"}
    for v, f in zip(volume_pred_insp, flow_pred_insp, strict=True)
]
chart.add("Predicted (Inspiratory)", pred_insp_data, stroke_style={"width": 3})

# PEF marker point
pef_idx = np.argmax(flow_exp)
pef_point = [
    {"value": (float(volume_exp[pef_idx]), float(flow_exp[pef_idx])), "label": f"PEF: {flow_exp[pef_idx]:.1f} L/s"}
]
chart.add("PEF", pef_point, stroke=False, show_dots=True, dots_size=14)

# Save interactive HTML
chart.render_to_file("plot.html")

# Render SVG for annotation post-processing
svg_bytes = chart.render()
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
root = ET.fromstring(svg_bytes)

ns = f"{{{SVG_NS}}}"

# Make predicted series dashed by finding their path elements
all_paths = list(root.iter(f"{ns}path"))
series_groups = list(root.iter(f"{ns}g"))

# Find serie groups and make predicted ones dashed
for g in root.iter(f"{ns}g"):
    cls = g.get("class", "")
    if "serie-2" in cls or "serie-3" in cls:
        for path in g.iter(f"{ns}path"):
            path.set("stroke-dasharray", "16,8")

# Find PEF dot and add annotation
pef_circles = []
for g in root.iter(f"{ns}g"):
    cls = g.get("class", "")
    if "serie-4" in cls:
        for c in g.iter(f"{ns}circle"):
            if float(c.get("r", "0")) > 3:
                pef_circles.append(c)

parent_map = {child: parent for parent in root.iter() for child in parent}

if pef_circles:
    circle = pef_circles[0]
    cx = float(circle.get("cx", "0"))
    cy = float(circle.get("cy", "0"))
    circle.set("fill", "#b5342b")
    circle.set("r", "12")

    parent_elem = parent_map.get(circle)
    if parent_elem is not None:
        # PEF label
        label = ET.SubElement(parent_elem, f"{ns}text")
        label.set("x", f"{cx + 20:.1f}")
        label.set("y", f"{cy - 25:.1f}")
        label.set("text-anchor", "start")
        label.set("font-size", "34")
        label.set("font-family", "DejaVu Sans, Helvetica, Arial, sans-serif")
        label.set("fill", "#b5342b")
        label.set("font-weight", "bold")
        label.text = f"PEF = {flow_exp[pef_idx]:.1f} L/s"

# Add clinical values text box (FEV1, FVC, PEF)
# Position in the upper-right area of the plot
info_x = 4100
info_y = 350

# Background rectangle for clinical values
rect = ET.SubElement(root, f"{ns}rect")
rect.set("x", f"{info_x - 20}")
rect.set("y", f"{info_y - 50}")
rect.set("width", "580")
rect.set("height", "220")
rect.set("rx", "12")
rect.set("fill", "white")
rect.set("stroke", "#cccccc")
rect.set("stroke-width", "2")
rect.set("opacity", "0.95")

# Clinical values header
header = ET.SubElement(root, f"{ns}text")
header.set("x", f"{info_x}")
header.set("y", f"{info_y}")
header.set("font-size", "32")
header.set("font-family", "DejaVu Sans, Helvetica, Arial, sans-serif")
header.set("fill", "#2d2d2d")
header.set("font-weight", "bold")
header.text = "Clinical Values"

# FEV1
fev1_el = ET.SubElement(root, f"{ns}text")
fev1_el.set("x", f"{info_x}")
fev1_el.set("y", f"{info_y + 50}")
fev1_el.set("font-size", "30")
fev1_el.set("font-family", "DejaVu Sans, Helvetica, Arial, sans-serif")
fev1_el.set("fill", "#306998")
fev1_el.text = f"FEV1: {fev1:.1f} L  ({fev1 / fvc * 100:.0f}% FVC)"

# FVC
fvc_el = ET.SubElement(root, f"{ns}text")
fvc_el.set("x", f"{info_x}")
fvc_el.set("y", f"{info_y + 95}")
fvc_el.set("font-size", "30")
fvc_el.set("font-family", "DejaVu Sans, Helvetica, Arial, sans-serif")
fvc_el.set("fill", "#306998")
fvc_el.text = f"FVC: {fvc:.1f} L"

# PEF
pef_el = ET.SubElement(root, f"{ns}text")
pef_el.set("x", f"{info_x}")
pef_el.set("y", f"{info_y + 140}")
pef_el.set("font-size", "30")
pef_el.set("font-family", "DejaVu Sans, Helvetica, Arial, sans-serif")
pef_el.set("fill", "#306998")
pef_el.text = f"PEF: {pef:.1f} L/s"

# Convert to PNG
cairosvg.svg2png(bytestring=ET.tostring(root, encoding="unicode").encode("utf-8"), write_to="plot.png")

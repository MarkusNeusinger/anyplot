"""pyplots.ai
alluvial-opinion-flow: Opinion Flow Diagram
Library: pygal 3.1.0 | Python 3.14.3
Quality: 70/100 | Created: 2026-03-03
"""

import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


np.random.seed(42)

# Data
waves = ["Wave 1 (Q1)", "Wave 2 (Q2)", "Wave 3 (Q3)", "Wave 4 (Q4)"]
categories = ["Strongly Favor", "Favor", "Neutral", "Oppose", "Strongly Oppose"]

# Improved color palette - better contrast between Oppose/Strongly Oppose
cat_colors = ["#1a5276", "#5499c7", "#f4d03f", "#af601a", "#7b241c"]
# Respondent counts per category at each wave (1000 total respondents)
respondent_counts = np.array(
    [
        [180, 210, 250, 270],  # Strongly Favor
        [250, 230, 220, 240],  # Favor
        [280, 240, 180, 150],  # Neutral
        [190, 200, 210, 200],  # Oppose
        [100, 120, 140, 140],  # Strongly Oppose
    ]
)

# Flow transitions between consecutive waves
flows = [
    # Wave 1 -> Wave 2
    {
        ("Strongly Favor", "Strongly Favor"): 150,
        ("Strongly Favor", "Favor"): 25,
        ("Strongly Favor", "Neutral"): 5,
        ("Favor", "Strongly Favor"): 40,
        ("Favor", "Favor"): 170,
        ("Favor", "Neutral"): 30,
        ("Favor", "Oppose"): 10,
        ("Neutral", "Strongly Favor"): 10,
        ("Neutral", "Favor"): 25,
        ("Neutral", "Neutral"): 190,
        ("Neutral", "Oppose"): 45,
        ("Neutral", "Strongly Oppose"): 10,
        ("Oppose", "Favor"): 10,
        ("Oppose", "Neutral"): 15,
        ("Oppose", "Oppose"): 135,
        ("Oppose", "Strongly Oppose"): 30,
        ("Strongly Oppose", "Neutral"): 5,
        ("Strongly Oppose", "Oppose"): 10,
        ("Strongly Oppose", "Strongly Oppose"): 85,
    },
    # Wave 2 -> Wave 3
    {
        ("Strongly Favor", "Strongly Favor"): 180,
        ("Strongly Favor", "Favor"): 20,
        ("Strongly Favor", "Neutral"): 10,
        ("Favor", "Strongly Favor"): 50,
        ("Favor", "Favor"): 150,
        ("Favor", "Neutral"): 20,
        ("Favor", "Oppose"): 10,
        ("Neutral", "Strongly Favor"): 10,
        ("Neutral", "Favor"): 40,
        ("Neutral", "Neutral"): 140,
        ("Neutral", "Oppose"): 40,
        ("Neutral", "Strongly Oppose"): 10,
        ("Oppose", "Favor"): 10,
        ("Oppose", "Neutral"): 10,
        ("Oppose", "Oppose"): 150,
        ("Oppose", "Strongly Oppose"): 30,
        ("Strongly Oppose", "Oppose"): 10,
        ("Strongly Oppose", "Strongly Oppose"): 110,
    },
    # Wave 3 -> Wave 4
    {
        ("Strongly Favor", "Strongly Favor"): 220,
        ("Strongly Favor", "Favor"): 20,
        ("Strongly Favor", "Neutral"): 10,
        ("Favor", "Strongly Favor"): 30,
        ("Favor", "Favor"): 170,
        ("Favor", "Neutral"): 15,
        ("Favor", "Oppose"): 5,
        ("Neutral", "Strongly Favor"): 10,
        ("Neutral", "Favor"): 40,
        ("Neutral", "Neutral"): 110,
        ("Neutral", "Oppose"): 15,
        ("Neutral", "Strongly Oppose"): 5,
        ("Oppose", "Favor"): 10,
        ("Oppose", "Neutral"): 15,
        ("Oppose", "Oppose"): 165,
        ("Oppose", "Strongly Oppose"): 20,
        ("Strongly Oppose", "Neutral"): 5,
        ("Strongly Oppose", "Oppose"): 15,
        ("Strongly Oppose", "Strongly Oppose"): 120,
    },
]

# Compute top cross-category flows for polarization highlighting
cross_flows = []
for flow_dict in flows:
    for (src, tgt), count in flow_dict.items():
        if src != tgt:
            cross_flows.append(count)
cross_flows.sort(reverse=True)
highlight_threshold = cross_flows[7] if len(cross_flows) > 7 else 0

# Custom style - extensive use of pygal's Style system
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#222222",
    foreground_subtle="#999999",
    colors=tuple(cat_colors),
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=34,
    value_font_size=32,
    value_label_font_size=32,
    font_family="DejaVu Sans, sans-serif",
    label_font_family="DejaVu Sans, sans-serif",
    title_font_family="DejaVu Sans, sans-serif",
    legend_font_family="DejaVu Sans, sans-serif",
    value_font_family="DejaVu Sans, sans-serif",
)

# Create StackedBar chart using pygal's chart system for the node columns
chart = pygal.StackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="alluvial-opinion-flow \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Renewable Energy Policy Survey \u00b7 1,000 Respondents Tracked Quarterly",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=24,
    show_y_guides=False,
    show_x_guides=False,
    show_y_labels=False,
    print_values=True,
    print_values_position="center",
    value_formatter=lambda x: f"{int(x)}",
    x_label_rotation=0,
    rounded_bars=6,
    margin_bottom=10,
)
chart.x_labels = waves

# Add data series with descriptive tooltips using pygal's data API
for cat_idx, cat in enumerate(categories):
    chart.add(cat, [{"value": int(v), "label": f"{cat}: {int(v)} respondents"} for v in respondent_counts[cat_idx]])

# Render chart to SVG and parse with ElementTree for robust XML traversal
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
svg_str = chart.render().decode("utf-8")
root = ET.fromstring(svg_str)
SVG = "{http://www.w3.org/2000/svg}"

# Extract bar positions using proper XML parsing (replaces fragile regex)
# pygal SVG structure: <g class="series serie-N"> -> <g class="bars"> -> <g class="bar">
bar_info = []  # (series_idx, bar_idx, x, y, w, h, center_x, rect_elem)
for g in root.iter(f"{SVG}g"):
    cls = g.get("class", "")
    if "serie-" not in cls or "series" not in cls:
        continue
    series_idx = None
    for part in cls.split():
        if part.startswith("serie-"):
            series_idx = int(part[6:])
            break
    if series_idx is None:
        continue
    # Find the bars wrapper group, then iterate individual bar elements
    bars_group = None
    for child in g:
        if child.tag == f"{SVG}g" and child.get("class", "") == "bars":
            bars_group = child
            break
    if bars_group is None:
        continue
    bar_idx = 0
    for bar_g in bars_group:
        if bar_g.tag != f"{SVG}g":
            continue
        bar_cls = bar_g.get("class", "")
        if "bar" not in bar_cls:
            continue
        rect = bar_g.find(f"{SVG}rect")
        cx_desc = None
        for desc in bar_g.findall(f"{SVG}desc"):
            if desc.get("class") == "x centered":
                cx_desc = desc
                break
        if rect is not None and cx_desc is not None:
            x = float(rect.get("x"))
            y = float(rect.get("y"))
            w = float(rect.get("width"))
            h = float(rect.get("height"))
            cx = float(cx_desc.text)
            bar_info.append((series_idx, bar_idx, x, y, w, h, cx, rect))
        bar_idx += 1

# Narrow bars to alluvial node columns with white stroke separators
NODE_WIDTH = 160
for _si, _bi, _x, _y, _w, _h, cx, rect in bar_info:
    new_x = cx - NODE_WIDTH / 2
    rect.set("x", f"{new_x:.2f}")
    rect.set("width", str(NODE_WIDTH))
    rect.set("stroke", "white")
    rect.set("stroke-width", "3")

# Build position lookup: (series_idx, wave_idx) -> (y_top, y_bottom, center_x)
bar_positions = {}
for series_idx, bar_idx, _x, y, _w, h, cx, _rect in bar_info:
    bar_positions[(series_idx, bar_idx)] = (y, y + h, cx)

cat_to_series = {cat: idx for idx, cat in enumerate(categories)}

# Find the plot group (parent of series groups with actual bar data) for flow insertion
plot_group = None
first_series_pos = 0
for g in root.iter(f"{SVG}g"):
    cls = g.get("class", "")
    if cls == "plot":
        for idx, child in enumerate(g):
            if child.get("class", "").startswith("series serie-0"):
                plot_group = g
                first_series_pos = idx
                break
    if plot_group is not None:
        break

# Build alluvial flow paths
flow_group = ET.Element(f"{SVG}g")
flow_group.set("id", "alluvial-flows")

for flow_idx, flow_dict in enumerate(flows):
    source_offsets = {}
    target_offsets = {}
    for cat_idx in range(len(categories)):
        src_pos = bar_positions.get((cat_idx, flow_idx))
        if src_pos:
            source_offsets[cat_idx] = src_pos[0]
        tgt_pos = bar_positions.get((cat_idx, flow_idx + 1))
        if tgt_pos:
            target_offsets[cat_idx] = tgt_pos[0]

    for (src_cat, tgt_cat), count in sorted(flow_dict.items(), key=lambda x: -x[1]):
        if count <= 0:
            continue

        src_idx = cat_to_series[src_cat]
        tgt_idx = cat_to_series[tgt_cat]

        src_bar = bar_positions.get((src_idx, flow_idx))
        tgt_bar = bar_positions.get((tgt_idx, flow_idx + 1))
        if not src_bar or not tgt_bar:
            continue

        src_total = respondent_counts[src_idx, flow_idx]
        tgt_total = respondent_counts[tgt_idx, flow_idx + 1]
        src_bar_h = src_bar[1] - src_bar[0]
        tgt_bar_h = tgt_bar[1] - tgt_bar[0]

        src_frac_h = (count / src_total) * src_bar_h
        tgt_frac_h = (count / tgt_total) * tgt_bar_h

        y0_top = source_offsets[src_idx]
        y0_bottom = y0_top + src_frac_h
        y1_top = target_offsets[tgt_idx]
        y1_bottom = y1_top + tgt_frac_h

        band_x0 = src_bar[2] + NODE_WIDTH / 2
        band_x1 = tgt_bar[2] - NODE_WIDTH / 2
        cx0 = band_x0 + 0.4 * (band_x1 - band_x0)
        cx1 = band_x0 + 0.6 * (band_x1 - band_x0)

        is_stable = src_cat == tgt_cat
        if is_stable:
            opacity = 0.55
        elif count >= highlight_threshold:
            opacity = 0.45
        else:
            opacity = 0.30

        path_d = (
            f"M {band_x0:.1f},{y0_top:.1f} "
            f"C {cx0:.1f},{y0_top:.1f} {cx1:.1f},{y1_top:.1f} {band_x1:.1f},{y1_top:.1f} "
            f"L {band_x1:.1f},{y1_bottom:.1f} "
            f"C {cx1:.1f},{y1_bottom:.1f} {cx0:.1f},{y0_bottom:.1f} {band_x0:.1f},{y0_bottom:.1f} "
            f"Z"
        )

        path_elem = ET.SubElement(flow_group, f"{SVG}path")
        path_elem.set("d", path_d)
        path_elem.set("fill", cat_colors[src_idx])
        path_elem.set("fill-opacity", str(opacity))
        path_elem.set("stroke", "none")

        source_offsets[src_idx] = y0_bottom
        target_offsets[tgt_idx] = y1_bottom

# Insert flows before series groups so bars render on top
if plot_group is not None:
    plot_group.insert(first_series_pos, flow_group)

# Add polarization annotation with readable font size and contrast
annotation = ET.SubElement(root, f"{SVG}text")
annotation.set("x", "4720")
annotation.set("y", "130")
annotation.set("text-anchor", "end")
annotation.set("font-size", "44")
annotation.set("font-style", "italic")
annotation.set("font-family", "DejaVu Sans, sans-serif")
annotation.set("fill", "#555555")
annotation.text = "Solid = stable opinion \u00b7 Faded = changed \u00b7 Polarization: Neutral 280\u2192150"

# Serialize SVG
svg_str = ET.tostring(root, encoding="unicode")

# Save outputs
with open("plot.svg", "w") as f:
    f.write(svg_str)

cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), write_to="plot.png")

with open("plot.html", "w") as f:
    f.write(
        """<!DOCTYPE html>
<html>
<head>
    <title>alluvial-opinion-flow · pygal · pyplots.ai</title>
    <style>
        body { margin: 0; padding: 20px; background: #f5f5f5; font-family: sans-serif; }
        .container { max-width: 100%; margin: 0 auto; }
        object { width: 100%; height: auto; }
    </style>
</head>
<body>
    <div class="container">
        <object type="image/svg+xml" data="plot.svg">
            Opinion Flow Diagram not supported
        </object>
    </div>
</body>
</html>"""
    )

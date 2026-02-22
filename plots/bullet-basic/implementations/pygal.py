""" pyplots.ai
bullet-basic: Basic Bullet Chart
Library: pygal 3.1.0 | Python 3.14.3
Quality: 85/100 | Updated: 2026-02-22
"""

import xml.etree.ElementTree as ET

import cairosvg
import pygal
from pygal.style import Style


# Data - Sales KPIs showing actual vs target with qualitative ranges
metrics = [
    {"label": "Revenue", "actual": 275, "target": 250, "max": 300, "fmt": "${}K"},
    {"label": "Profit", "actual": 85, "target": 100, "max": 120, "fmt": "${}K"},
    {"label": "New Orders", "actual": 320, "target": 350, "max": 400, "fmt": "{}"},
    {"label": "Customers", "actual": 1450, "target": 1400, "max": 1600, "fmt": "{}"},
    {"label": "Satisfaction", "actual": 4.2, "target": 4.5, "max": 5.0, "fmt": "{}/5"},
    {"label": "Avg Deal Size", "actual": 42, "target": 50, "max": 60, "fmt": "${}K"},
    {"label": "Retention", "actual": 92, "target": 85, "max": 100, "fmt": "{}%"},
]

POOR_PCT = 50
SAT_PCT = 75

# Normalize to percentages and classify performance vs target
actual_pcts = [round((m["actual"] / m["max"]) * 100, 1) for m in metrics]
target_pcts = [round((m["target"] / m["max"]) * 100, 1) for m in metrics]
above_target = [m["actual"] >= m["target"] for m in metrics]
labels = [f"{m['label']} ({m['fmt'].format(m['actual'])})" for m in metrics]

# Performance-coded colors for data storytelling (colorblind-safe teal vs amber)
COLOR_ABOVE = "#2A9D8F"
COLOR_BELOW = "#D4770B"
COLOR_TARGET = "#1a1a1a"

# Style: grayscale range bands + performance-coded bars + black target
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#999999",
    font_family="DejaVu Sans, Helvetica, Arial, sans-serif",
    colors=("#E0E0E0", "#BFBFBF", "#969696", COLOR_ABOVE, COLOR_BELOW, COLOR_TARGET),
    title_font_size=64,
    label_font_size=40,
    major_label_font_size=36,
    legend_font_size=34,
    value_font_size=30,
    tooltip_font_size=30,
)

chart = pygal.HorizontalStackedBar(
    width=4800,
    height=2700,
    title="bullet-basic \u00b7 pygal \u00b7 pyplots.ai",
    style=custom_style,
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=26,
    print_values=False,
    print_zeroes=False,
    show_y_guides=False,
    show_x_guides=True,
    margin=40,
    spacing=0,
    rounded_bars=2,
    truncate_label=-1,
    x_title="Performance (% of Maximum)",
    range=(0, 100),
)
chart.x_labels = labels

# Qualitative range bands as stacked series with per-value config dicts
chart.add("Poor (0-50%)", [{"value": POOR_PCT, "label": labels[i]} for i in range(len(metrics))])
chart.add("Satisfactory (50-75%)", [{"value": SAT_PCT - POOR_PCT, "label": labels[i]} for i in range(len(metrics))])
chart.add("Good (75-100%)", [{"value": 100 - SAT_PCT, "label": labels[i]} for i in range(len(metrics))])

# Legend-only series for performance-coded actual bars and target marker
chart.add("Above Target", [None] * len(metrics))
chart.add("Below Target", [None] * len(metrics))
chart.add("Target", [None] * len(metrics))

# Render SVG and parse for programmatic element injection
ET.register_namespace("", "http://www.w3.org/2000/svg")
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
svg_bytes = chart.render()
root = ET.fromstring(svg_bytes)
NS = "http://www.w3.org/2000/svg"

parent_map = {child: parent for parent in root.iter() for child in parent}

# Remove dashed leader lines for cleaner appearance
for line in list(root.iter(f"{{{NS}}}line")):
    if line.get("stroke-dasharray"):
        p = parent_map.get(line)
        if p is not None:
            p.remove(line)

# Locate serie-0 (Poor range) bars as coordinate reference
serie_0 = next((g for g in root.iter(f"{{{NS}}}g") if "serie-0" in g.get("class", "")), None)

# Extract bar positions from Poor range (x, y, width, height per metric row)
poor_bars = []
if serie_0 is not None:
    for rect in serie_0.iter(f"{{{NS}}}rect"):
        w, h = float(rect.get("width", "0")), float(rect.get("height", "0"))
        if w > 1 and h > 1:
            poor_bars.append((float(rect.get("x")), float(rect.get("y")), w, h))

# Inject actual bars and target markers into the plot coordinate space
inject_parent = parent_map.get(serie_0, root)
for i, (bx, by, bw, bh) in enumerate(poor_bars):
    # Convert percentage to pixel width using Poor band as scale reference
    px_per_pct = bw / POOR_PCT
    cy = by + bh / 2  # vertical center of this metric row

    # Actual value bar (42% of band height for classic bullet chart layering)
    actual_w = actual_pcts[i] * px_per_pct
    bar_h = bh * 0.42
    bar_color = COLOR_ABOVE if above_target[i] else COLOR_BELOW
    a = ET.SubElement(inject_parent, f"{{{NS}}}rect")
    a.set("x", f"{bx:.1f}")
    a.set("y", f"{cy - bar_h / 2:.1f}")
    a.set("width", f"{actual_w:.1f}")
    a.set("height", f"{bar_h:.1f}")
    a.set("fill", bar_color)
    a.set("rx", "2")

    # Target marker (prominent vertical line at target percentage)
    tx = bx + target_pcts[i] * px_per_pct
    marker_h = bh * 0.75
    t = ET.SubElement(inject_parent, f"{{{NS}}}rect")
    t.set("x", f"{tx - 6:.1f}")
    t.set("y", f"{cy - marker_h / 2:.1f}")
    t.set("width", "12")
    t.set("height", f"{marker_h:.1f}")
    t.set("fill", COLOR_TARGET)

# Save as PNG at native 4800×2700 resolution
cairosvg.svg2png(bytestring=ET.tostring(root, encoding="utf-8"), write_to="plot.png")

""" pyplots.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: bokeh 3.8.2 | Python 3.13.11
Quality: 72/100 | Created: 2026-01-11
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.layouts import column, row
from bokeh.models import Button, ColumnDataSource, CustomJS, Div, Label, Legend, LegendItem
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - organizational budget hierarchy
np.random.seed(42)

hierarchy = [
    {"id": "company", "parent": "", "label": "Company", "value": 0},
    {"id": "engineering", "parent": "company", "label": "Engineering", "value": 0},
    {"id": "marketing", "parent": "company", "label": "Marketing", "value": 0},
    {"id": "operations", "parent": "company", "label": "Operations", "value": 0},
    {"id": "hr", "parent": "company", "label": "HR", "value": 0},
    {"id": "frontend", "parent": "engineering", "label": "Frontend", "value": 1200},
    {"id": "backend", "parent": "engineering", "label": "Backend", "value": 1500},
    {"id": "devops", "parent": "engineering", "label": "DevOps", "value": 800},
    {"id": "qa", "parent": "engineering", "label": "QA", "value": 600},
    {"id": "digital", "parent": "marketing", "label": "Digital", "value": 900},
    {"id": "content", "parent": "marketing", "label": "Content", "value": 700},
    {"id": "analytics", "parent": "marketing", "label": "Analytics", "value": 500},
    {"id": "logistics", "parent": "operations", "label": "Logistics", "value": 1100},
    {"id": "facilities", "parent": "operations", "label": "Facilities", "value": 600},
    {"id": "procurement", "parent": "operations", "label": "Procurement", "value": 450},
    {"id": "recruiting", "parent": "hr", "label": "Recruiting", "value": 400},
    {"id": "training", "parent": "hr", "label": "Training", "value": 350},
    {"id": "benefits", "parent": "hr", "label": "Benefits", "value": 300},
]

# Calculate parent values (sum of children)
id_to_node = {n["id"]: n for n in hierarchy}
for node in reversed(hierarchy):
    if node["value"] == 0:
        children_sum = sum(n["value"] for n in hierarchy if n["parent"] == node["id"])
        node["value"] = children_sum

# Color palette - distinct colors for ALL sub-departments (improved Marketing colors)
colors = {
    "company": "#306998",
    "engineering": "#FFD43B",
    "marketing": "#2ca02c",
    "operations": "#fc8d62",
    "hr": "#8da0cb",
    "frontend": "#e41a1c",
    "backend": "#377eb8",
    "devops": "#4daf4a",
    "qa": "#ff7f00",
    "digital": "#984ea3",
    "content": "#a65628",
    "analytics": "#f781bf",
    "logistics": "#fdae6b",
    "facilities": "#fd8d3c",
    "procurement": "#d62728",
    "recruiting": "#9467bd",
    "training": "#17becf",
    "benefits": "#bcbd22",
}

# Get leaf nodes for treemap
leaf_nodes = [n for n in hierarchy if not any(m["parent"] == n["id"] for m in hierarchy)]
leaf_values = [n["value"] for n in leaf_nodes]

# Inline squarify algorithm for treemap layout (left panel: x=100 to 2100, y=300 to 2100)
treemap_rects = []
remaining_nodes = list(enumerate(leaf_values))
total = sum(leaf_values)
tm_x, tm_y, tm_w, tm_h = 100, 300, 2000, 1800

while remaining_nodes:
    if tm_w >= tm_h:
        strip = []
        strip_sum = 0
        best_ratio = float("inf")
        strip_idx = 0
        for i, (idx, v) in enumerate(remaining_nodes):
            test_strip = strip + [(idx, v)]
            test_sum = strip_sum + v
            strip_w = (test_sum / total) * tm_w if total > 0 else tm_w
            ratios = []
            for _, sv in test_strip:
                strip_h = (sv / test_sum) * tm_h if test_sum > 0 else tm_h / len(test_strip)
                ratio = max(strip_w / strip_h, strip_h / strip_w) if strip_h > 0 else float("inf")
                ratios.append(ratio)
            worst_ratio = max(ratios) if ratios else float("inf")
            if worst_ratio <= best_ratio:
                strip = test_strip
                strip_sum = test_sum
                best_ratio = worst_ratio
                strip_idx = i + 1
            else:
                break
        strip_w = (strip_sum / total) * tm_w if total > 0 else tm_w
        strip_y = tm_y
        for idx, sv in strip:
            strip_h = (sv / strip_sum) * tm_h if strip_sum > 0 else tm_h / len(strip)
            treemap_rects.append((idx, tm_x, strip_y, strip_w, strip_h))
            strip_y += strip_h
        tm_x += strip_w
        tm_w -= strip_w
        total -= strip_sum
        remaining_nodes = remaining_nodes[strip_idx:]
    else:
        strip = []
        strip_sum = 0
        best_ratio = float("inf")
        strip_idx = 0
        for i, (idx, v) in enumerate(remaining_nodes):
            test_strip = strip + [(idx, v)]
            test_sum = strip_sum + v
            strip_h = (test_sum / total) * tm_h if total > 0 else tm_h
            ratios = []
            for _, sv in test_strip:
                strip_w = (sv / test_sum) * tm_w if test_sum > 0 else tm_w / len(test_strip)
                ratio = max(strip_w / strip_h, strip_h / strip_w) if strip_w > 0 else float("inf")
                ratios.append(ratio)
            worst_ratio = max(ratios) if ratios else float("inf")
            if worst_ratio <= best_ratio:
                strip = test_strip
                strip_sum = test_sum
                best_ratio = worst_ratio
                strip_idx = i + 1
            else:
                break
        strip_h = (strip_sum / total) * tm_h if total > 0 else tm_h
        strip_x = tm_x
        for idx, sv in strip:
            strip_w = (sv / strip_sum) * tm_w if strip_sum > 0 else tm_w / len(strip)
            treemap_rects.append((idx, strip_x, tm_y, strip_w, strip_h))
            strip_x += strip_w
        tm_y += strip_h
        tm_h -= strip_h
        total -= strip_sum
        remaining_nodes = remaining_nodes[strip_idx:]

# Build treemap data
treemap_xs = []
treemap_ys = []
treemap_widths = []
treemap_heights = []
treemap_colors = []
treemap_labels = []
treemap_text_labels = []
treemap_value_labels = []
treemap_label_xs = []
treemap_label_ys = []
treemap_value_xs = []
treemap_value_ys = []

for idx, rx, ry, rw, rh in treemap_rects:
    node = leaf_nodes[idx]
    cx = rx + rw / 2
    cy = ry + rh / 2
    treemap_xs.append(cx)
    treemap_ys.append(cy)
    treemap_widths.append(rw - 8)
    treemap_heights.append(rh - 8)
    treemap_colors.append(colors.get(node["id"], "#cccccc"))
    treemap_labels.append(f"{node['label']}: ${node['value']}K")
    treemap_text_labels.append(node["label"])
    treemap_value_labels.append(f"${node['value']}K")
    treemap_label_xs.append(cx)
    treemap_label_ys.append(cy + 30)
    treemap_value_xs.append(cx)
    treemap_value_ys.append(cy - 30)

# Generate sunburst wedges (right panel, centered at x=3300)
sunburst_inner = []
sunburst_outer = []
sunburst_start = []
sunburst_end = []
sunburst_colors = []
sunburst_labels = []

scx, scy = 3300, 1200
total_value = id_to_node["company"]["value"]

# Level 0: process company's children (departments)
level_0_start = 0.0
for dept in [n for n in hierarchy if n["parent"] == "company"]:
    angle_span = (dept["value"] / total_value) * 2 * np.pi
    sunburst_inner.append(150)
    sunburst_outer.append(400)
    sunburst_start.append(level_0_start)
    sunburst_end.append(level_0_start + angle_span)
    sunburst_colors.append(colors.get(dept["id"], "#cccccc"))
    sunburst_labels.append(f"{dept['label']}: ${dept['value']}K")

    # Level 1: process department's children (sub-departments)
    level_1_start = level_0_start
    for subdept in [n for n in hierarchy if n["parent"] == dept["id"]]:
        sub_angle_span = (subdept["value"] / total_value) * 2 * np.pi
        sunburst_inner.append(420)
        sunburst_outer.append(700)
        sunburst_start.append(level_1_start)
        sunburst_end.append(level_1_start + sub_angle_span)
        sunburst_colors.append(colors.get(subdept["id"], "#cccccc"))
        sunburst_labels.append(f"{subdept['label']}: ${subdept['value']}K")
        level_1_start += sub_angle_span

    level_0_start += angle_span

# Convert sunburst to x,y coordinates for patches
sunburst_xs_list = []
sunburst_ys_list = []

for i in range(len(sunburst_inner)):
    angles = np.linspace(sunburst_start[i], sunburst_end[i], 30)
    inner_x = scx + sunburst_inner[i] * np.cos(angles)
    inner_y = scy + sunburst_inner[i] * np.sin(angles)
    outer_x = scx + sunburst_outer[i] * np.cos(angles[::-1])
    outer_y = scy + sunburst_outer[i] * np.sin(angles[::-1])
    xs = list(inner_x) + list(outer_x)
    ys = list(inner_y) + list(outer_y)
    sunburst_xs_list.append(xs)
    sunburst_ys_list.append(ys)

# Create the figure - side by side layout showing BOTH views
p = figure(
    width=4800,
    height=2700,
    title="hierarchy-toggle-view · bokeh · pyplots.ai",
    x_range=(-100, 4700),
    y_range=(0, 2600),
    tools="hover",
    tooltips="@labels",
)

p.title.text_font_size = "36pt"
p.title.text_color = "#306998"
p.xaxis.visible = False
p.yaxis.visible = False
p.grid.visible = False
p.outline_line_color = None
p.background_fill_color = "#fafafa"

# Add panel labels
p.add_layout(
    Label(
        x=1100,
        y=2300,
        text="Treemap View",
        text_font_size="28pt",
        text_color="#333333",
        text_font_style="bold",
        text_align="center",
    )
)
p.add_layout(
    Label(
        x=3300,
        y=2300,
        text="Sunburst View",
        text_font_size="28pt",
        text_color="#333333",
        text_font_style="bold",
        text_align="center",
    )
)

# Add toggle indicator arrow
p.add_layout(Label(x=2250, y=1200, text="⟷", text_font_size="48pt", text_color="#306998", text_align="center"))

# Create data sources
treemap_source = ColumnDataSource(
    data={
        "x": treemap_xs,
        "y": treemap_ys,
        "width": treemap_widths,
        "height": treemap_heights,
        "color": treemap_colors,
        "labels": treemap_labels,
    }
)

sunburst_source = ColumnDataSource(
    data={"xs": sunburst_xs_list, "ys": sunburst_ys_list, "color": sunburst_colors, "labels": sunburst_labels}
)

# Draw treemap rectangles
treemap_renderer = p.rect(
    x="x",
    y="y",
    width="width",
    height="height",
    color="color",
    source=treemap_source,
    line_color="white",
    line_width=3,
    alpha=0.9,
)

# Add labels using text glyphs
treemap_labels_renderer = p.text(
    x=treemap_label_xs,
    y=treemap_label_ys,
    text=treemap_text_labels,
    text_font_size="18pt",
    text_color="#222222",
    text_align="center",
    text_baseline="middle",
    text_font_style="bold",
)

treemap_values_renderer = p.text(
    x=treemap_value_xs,
    y=treemap_value_ys,
    text=treemap_value_labels,
    text_font_size="14pt",
    text_color="#444444",
    text_align="center",
    text_baseline="middle",
)

# Draw sunburst (visible for PNG)
sunburst_renderer = p.patches(
    xs="xs", ys="ys", color="color", source=sunburst_source, line_color="white", line_width=2, alpha=0.9
)

# Add legend for ALL sub-departments (by parent department)
departments = ["engineering", "marketing", "operations", "hr"]
dept_labels = ["Engineering", "Marketing", "Operations", "HR"]
subdept_order = [
    ["backend", "frontend", "devops", "qa"],
    ["digital", "content", "analytics"],
    ["logistics", "facilities", "procurement"],
    ["recruiting", "training", "benefits"],
]

legend_items = []
for dept_id, dept_label, subdepts in zip(departments, dept_labels, subdept_order, strict=True):
    legend_rect = p.rect(x=[-1000], y=[-1000], width=1, height=1, color=colors[dept_id], alpha=0.9)
    legend_items.append(LegendItem(label=dept_label, renderers=[legend_rect]))
    for subdept_id in subdepts:
        subdept_node = id_to_node[subdept_id]
        legend_rect = p.rect(x=[-1000], y=[-1000], width=1, height=1, color=colors[subdept_id], alpha=0.9)
        legend_items.append(LegendItem(label=f"  {subdept_node['label']}", renderers=[legend_rect]))

legend = Legend(items=legend_items, location="top_right", title="Budget Hierarchy", title_text_font_size="20pt")
legend.label_text_font_size = "14pt"
legend.glyph_height = 24
legend.glyph_width = 24
legend.spacing = 5
legend.padding = 15
legend.background_fill_alpha = 0.9
p.add_layout(legend, "right")

# Save PNG with side-by-side view
export_png(p, filename="plot.png")

# --- Interactive HTML version with toggle buttons ---
p_html = figure(
    width=4800,
    height=2700,
    title="hierarchy-toggle-view · bokeh · pyplots.ai",
    x_range=(-100, 4500),
    y_range=(0, 2500),
    tools="hover",
    tooltips="@labels",
)

p_html.title.text_font_size = "36pt"
p_html.title.text_color = "#306998"
p_html.xaxis.visible = False
p_html.yaxis.visible = False
p_html.grid.visible = False
p_html.outline_line_color = None
p_html.background_fill_color = "#fafafa"

# HTML treemap (centered)
html_treemap_xs = [x + 1000 for x in treemap_xs]
html_treemap_label_xs = [x + 1000 for x in treemap_label_xs]
html_treemap_value_xs = [x + 1000 for x in treemap_value_xs]

html_treemap_source = ColumnDataSource(
    data={
        "x": html_treemap_xs,
        "y": treemap_ys,
        "width": treemap_widths,
        "height": treemap_heights,
        "color": treemap_colors,
        "labels": treemap_labels,
    }
)

# HTML sunburst (centered at canvas center)
html_scx, html_scy = 2200, 1200
html_sunburst_xs_list = []
html_sunburst_ys_list = []

for i in range(len(sunburst_inner)):
    angles = np.linspace(sunburst_start[i], sunburst_end[i], 30)
    inner_x = html_scx + sunburst_inner[i] * np.cos(angles)
    inner_y = html_scy + sunburst_inner[i] * np.sin(angles)
    outer_x = html_scx + sunburst_outer[i] * np.cos(angles[::-1])
    outer_y = html_scy + sunburst_outer[i] * np.sin(angles[::-1])
    xs = list(inner_x) + list(outer_x)
    ys = list(inner_y) + list(outer_y)
    html_sunburst_xs_list.append(xs)
    html_sunburst_ys_list.append(ys)

html_sunburst_source = ColumnDataSource(
    data={"xs": html_sunburst_xs_list, "ys": html_sunburst_ys_list, "color": sunburst_colors, "labels": sunburst_labels}
)

html_treemap_renderer = p_html.rect(
    x="x",
    y="y",
    width="width",
    height="height",
    color="color",
    source=html_treemap_source,
    line_color="white",
    line_width=3,
    alpha=0.9,
)

html_treemap_labels_renderer = p_html.text(
    x=html_treemap_label_xs,
    y=treemap_label_ys,
    text=treemap_text_labels,
    text_font_size="24pt",
    text_color="#222222",
    text_align="center",
    text_baseline="middle",
    text_font_style="bold",
)

html_treemap_values_renderer = p_html.text(
    x=html_treemap_value_xs,
    y=treemap_value_ys,
    text=treemap_value_labels,
    text_font_size="20pt",
    text_color="#444444",
    text_align="center",
    text_baseline="middle",
)

html_sunburst_renderer = p_html.patches(
    xs="xs", ys="ys", color="color", source=html_sunburst_source, line_color="white", line_width=2, alpha=0.9
)
html_sunburst_renderer.visible = False

# Add legend to HTML version too
html_legend_items = []
for dept_id, dept_label, subdepts in zip(departments, dept_labels, subdept_order, strict=True):
    legend_rect = p_html.rect(x=[-1000], y=[-1000], width=1, height=1, color=colors[dept_id], alpha=0.9)
    html_legend_items.append(LegendItem(label=dept_label, renderers=[legend_rect]))
    for subdept_id in subdepts:
        subdept_node = id_to_node[subdept_id]
        legend_rect = p_html.rect(x=[-1000], y=[-1000], width=1, height=1, color=colors[subdept_id], alpha=0.9)
        html_legend_items.append(LegendItem(label=f"  {subdept_node['label']}", renderers=[legend_rect]))

html_legend = Legend(
    items=html_legend_items, location="top_right", title="Budget Hierarchy", title_text_font_size="20pt"
)
html_legend.label_text_font_size = "14pt"
html_legend.glyph_height = 24
html_legend.glyph_width = 24
html_legend.spacing = 5
html_legend.padding = 15
html_legend.background_fill_alpha = 0.9
p_html.add_layout(html_legend, "right")

# Create toggle buttons
treemap_btn = Button(label="Treemap View", button_type="primary", width=200, height=50)
sunburst_btn = Button(label="Sunburst View", button_type="default", width=200, height=50)

toggle_to_treemap = CustomJS(
    args={
        "treemap": html_treemap_renderer,
        "sunburst": html_sunburst_renderer,
        "tm_labels": html_treemap_labels_renderer,
        "tm_values": html_treemap_values_renderer,
        "tm_btn": treemap_btn,
        "sb_btn": sunburst_btn,
    },
    code="""
    treemap.visible = true;
    sunburst.visible = false;
    tm_labels.visible = true;
    tm_values.visible = true;
    tm_btn.button_type = 'primary';
    sb_btn.button_type = 'default';
    """,
)

toggle_to_sunburst = CustomJS(
    args={
        "treemap": html_treemap_renderer,
        "sunburst": html_sunburst_renderer,
        "tm_labels": html_treemap_labels_renderer,
        "tm_values": html_treemap_values_renderer,
        "tm_btn": treemap_btn,
        "sb_btn": sunburst_btn,
    },
    code="""
    treemap.visible = false;
    sunburst.visible = true;
    tm_labels.visible = false;
    tm_values.visible = false;
    tm_btn.button_type = 'default';
    sb_btn.button_type = 'primary';
    """,
)

treemap_btn.js_on_click(toggle_to_treemap)
sunburst_btn.js_on_click(toggle_to_sunburst)

title_div = Div(
    text="<h2 style='font-size: 24px; color: #306998; margin: 10px;'>Company Budget Allocation</h2>",
    width=400,
    height=50,
)

button_row = row(treemap_btn, sunburst_btn)
layout = column(title_div, button_row, p_html)

# Save HTML for interactive version
save(layout, filename="plot.html", resources=CDN, title="Hierarchy Toggle View")

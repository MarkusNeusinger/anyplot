""" anyplot.ai
hierarchy-toggle-view: Interactive Treemap-Sunburst Toggle View
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-05-19
"""

import os
import sys


# Prevent self-import: when run as `python bokeh.py`, the script directory is
# prepended to sys.path, which makes `import bokeh` find this file instead of
# the installed bokeh package. Remove the script directory before other imports.
_script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path = [p for p in sys.path if p and os.path.realpath(p) != _script_dir]

import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.layouts import column, row  # noqa: E402
from bokeh.models import Button, ColumnDataSource, CustomJS, Label, Legend, LegendItem  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from bokeh.resources import CDN  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito colors for top-level departments; derived shades for sub-departments
DEPT_COLORS = {"engineering": "#009E73", "marketing": "#D55E00", "operations": "#0072B2", "hr": "#CC79A7"}
SUB_COLORS = {
    "frontend": "#00C48D",
    "backend": "#007A58",
    "devops": "#33B48A",
    "qa": "#66C8A8",
    "digital": "#FF7722",
    "content": "#AA4800",
    "analytics": "#E88240",
    "logistics": "#0092E0",
    "facilities": "#005688",
    "procurement": "#3398CC",
    "recruiting": "#E099C0",
    "training": "#A85C85",
    "benefits": "#D9A3C4",
}
NODE_COLORS = {**DEPT_COLORS, **SUB_COLORS}

# Data — company budget hierarchy
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

id_to_node = {n["id"]: n for n in hierarchy}
for node in reversed(hierarchy):
    if node["value"] == 0:
        node["value"] = sum(n["value"] for n in hierarchy if n["parent"] == node["id"])

leaf_nodes = [n for n in hierarchy if not any(m["parent"] == n["id"] for m in hierarchy)]
leaf_values = [n["value"] for n in leaf_nodes]

# Squarify treemap layout — left panel bounding box
sq_x, sq_y, sq_w, sq_h = 150, 380, 2100, 2150
sq_total = sum(leaf_values)
sq_remaining = list(enumerate(leaf_values))
treemap_rects = []

while sq_remaining:
    if sq_w >= sq_h:
        strip, strip_sum, best_ratio, strip_idx = [], 0, float("inf"), 0
        for i, (idx, v) in enumerate(sq_remaining):
            test = strip + [(idx, v)]
            s = strip_sum + v
            sw = (s / sq_total) * sq_w if sq_total > 0 else sq_w
            ratios = [max(sw / max((sv / s) * sq_h, 1e-9), max((sv / s) * sq_h, 1e-9) / sw) for _, sv in test if s > 0]
            worst = max(ratios) if ratios else float("inf")
            if worst <= best_ratio:
                strip, strip_sum, best_ratio, strip_idx = test, s, worst, i + 1
            else:
                break
        sw = (strip_sum / sq_total) * sq_w if sq_total > 0 else sq_w
        cy = sq_y
        for idx, sv in strip:
            sh = (sv / strip_sum) * sq_h if strip_sum > 0 else sq_h / len(strip)
            treemap_rects.append((idx, sq_x, cy, sw, sh))
            cy += sh
        sq_x += sw
        sq_w -= sw
        sq_total -= strip_sum
        sq_remaining = sq_remaining[strip_idx:]
    else:
        strip, strip_sum, best_ratio, strip_idx = [], 0, float("inf"), 0
        for i, (idx, v) in enumerate(sq_remaining):
            test = strip + [(idx, v)]
            s = strip_sum + v
            sh = (s / sq_total) * sq_h if sq_total > 0 else sq_h
            ratios = [max(sh / max((sv / s) * sq_w, 1e-9), max((sv / s) * sq_w, 1e-9) / sh) for _, sv in test if s > 0]
            worst = max(ratios) if ratios else float("inf")
            if worst <= best_ratio:
                strip, strip_sum, best_ratio, strip_idx = test, s, worst, i + 1
            else:
                break
        sh = (strip_sum / sq_total) * sq_h if sq_total > 0 else sq_h
        cx = sq_x
        for idx, sv in strip:
            sw = (sv / strip_sum) * sq_w if strip_sum > 0 else sq_w / len(strip)
            treemap_rects.append((idx, cx, sq_y, sw, sh))
            cx += sw
        sq_y += sh
        sq_h -= sh
        sq_total -= strip_sum
        sq_remaining = sq_remaining[strip_idx:]

# Build treemap data arrays (side-by-side positions for PNG static figure)
tm_cx_arr, tm_cy_arr = [], []
tm_w_arr, tm_h_arr = [], []
tm_colors, tm_tooltip, tm_text, tm_vals = [], [], [], []
tm_lx, tm_ly, tm_vx, tm_vy = [], [], [], []

for idx, rx, ry, rw, rh in treemap_rects:
    node = leaf_nodes[idx]
    cx_val = rx + rw / 2
    cy_val = ry + rh / 2
    tm_cx_arr.append(cx_val)
    tm_cy_arr.append(cy_val)
    tm_w_arr.append(max(rw - 6, 1))
    tm_h_arr.append(max(rh - 6, 1))
    tm_colors.append(NODE_COLORS.get(node["id"], "#999999"))
    tm_tooltip.append(f"{node['label']}: ${node['value']}K")
    tm_text.append(node["label"])
    tm_vals.append(f"${node['value']}K")
    tm_lx.append(cx_val)
    tm_ly.append(cy_val + 38)
    tm_vx.append(cx_val)
    tm_vy.append(cy_val - 38)

# Sunburst layout — right panel, center (3480, 1455)
SCX, SCY = 3480, 1455
DEPT_INNER, DEPT_OUTER = 170, 490
SUB_INNER, SUB_OUTER = 510, 840
total_val = id_to_node["company"]["value"]

sb_inner, sb_outer, sb_start, sb_end = [], [], [], []
sb_colors, sb_tooltip = [], []

angle_cursor = 0.0
departments = [n for n in hierarchy if n["parent"] == "company"]
for dept in departments:
    dept_span = (dept["value"] / total_val) * 2 * np.pi
    sb_inner.append(DEPT_INNER)
    sb_outer.append(DEPT_OUTER)
    sb_start.append(angle_cursor)
    sb_end.append(angle_cursor + dept_span)
    sb_colors.append(DEPT_COLORS.get(dept["id"], "#999999"))
    sb_tooltip.append(f"{dept['label']}: ${dept['value']}K")

    sub_cursor = angle_cursor
    for sub in [n for n in hierarchy if n["parent"] == dept["id"]]:
        sub_span = (sub["value"] / total_val) * 2 * np.pi
        sb_inner.append(SUB_INNER)
        sb_outer.append(SUB_OUTER)
        sb_start.append(sub_cursor)
        sb_end.append(sub_cursor + sub_span)
        sb_colors.append(SUB_COLORS.get(sub["id"], "#999999"))
        sb_tooltip.append(f"{sub['label']}: ${sub['value']}K")
        sub_cursor += sub_span

    angle_cursor += dept_span

# Convert sunburst wedges to patch polygons
sb_xs_list, sb_ys_list = [], []
for i in range(len(sb_inner)):
    angles = np.linspace(sb_start[i], sb_end[i], 32)
    ix = SCX + sb_inner[i] * np.cos(angles)
    iy = SCY + sb_inner[i] * np.sin(angles)
    ox = SCX + sb_outer[i] * np.cos(angles[::-1])
    oy = SCY + sb_outer[i] * np.sin(angles[::-1])
    sb_xs_list.append(list(ix) + list(ox))
    sb_ys_list.append(list(iy) + list(oy))

# --- Static side-by-side figure (for PNG screenshot) ---
p_static = figure(
    width=4800,
    height=2700,
    x_range=(-50, 4750),
    y_range=(0, 2700),
    tools="hover",
    tooltips="@tooltip",
    toolbar_location=None,
)

p_static.title.text = "hierarchy-toggle-view · python · bokeh · anyplot.ai"
p_static.title.text_font_size = "28pt"
p_static.title.text_color = INK
p_static.title.text_font_style = "bold"

p_static.background_fill_color = PAGE_BG
p_static.border_fill_color = PAGE_BG
p_static.outline_line_color = None
p_static.xaxis.visible = False
p_static.yaxis.visible = False
p_static.grid.visible = False

# Panel header labels
p_static.add_layout(
    Label(
        x=1200,
        y=2560,
        text="Treemap View",
        text_font_size="26pt",
        text_color=INK,
        text_font_style="bold",
        text_align="center",
    )
)
p_static.add_layout(
    Label(
        x=3480,
        y=2560,
        text="Sunburst View",
        text_font_size="26pt",
        text_color=INK,
        text_font_style="bold",
        text_align="center",
    )
)

# Vertical divider
p_static.segment(x0=[2350], y0=[100], x1=[2350], y1=[2500], line_color=INK_SOFT, line_width=2, line_alpha=0.4)

# Treemap rectangles
tm_source = ColumnDataSource(
    data={
        "x": tm_cx_arr,
        "y": tm_cy_arr,
        "width": tm_w_arr,
        "height": tm_h_arr,
        "color": tm_colors,
        "tooltip": tm_tooltip,
    }
)
p_static.rect(
    x="x",
    y="y",
    width="width",
    height="height",
    color="color",
    source=tm_source,
    line_color=PAGE_BG,
    line_width=3,
    alpha=0.92,
)

# Treemap labels (only for large enough rectangles)
large_mask = [w > 180 and h > 100 for w, h in zip(tm_w_arr, tm_h_arr, strict=True)]
p_static.text(
    x=[tm_lx[i] for i in range(len(tm_lx)) if large_mask[i]],
    y=[tm_ly[i] for i in range(len(tm_ly)) if large_mask[i]],
    text=[tm_text[i] for i in range(len(tm_text)) if large_mask[i]],
    text_font_size="18pt",
    text_color=INK,
    text_align="center",
    text_baseline="middle",
    text_font_style="bold",
)
p_static.text(
    x=[tm_vx[i] for i in range(len(tm_vx)) if large_mask[i]],
    y=[tm_vy[i] for i in range(len(tm_vy)) if large_mask[i]],
    text=[tm_vals[i] for i in range(len(tm_vals)) if large_mask[i]],
    text_font_size="15pt",
    text_color=INK_SOFT,
    text_align="center",
    text_baseline="middle",
)

# Sunburst patches
sb_source = ColumnDataSource(data={"xs": sb_xs_list, "ys": sb_ys_list, "color": sb_colors, "tooltip": sb_tooltip})
p_static.patches(xs="xs", ys="ys", color="color", source=sb_source, line_color=PAGE_BG, line_width=3, alpha=0.92)

# Legend by department
dept_order = ["engineering", "marketing", "operations", "hr"]
dept_labels_map = {"engineering": "Engineering", "marketing": "Marketing", "operations": "Operations", "hr": "HR"}
subdept_order = {
    "engineering": ["backend", "frontend", "devops", "qa"],
    "marketing": ["digital", "content", "analytics"],
    "operations": ["logistics", "facilities", "procurement"],
    "hr": ["recruiting", "training", "benefits"],
}
legend_items = []
for d_id in dept_order:
    r = p_static.rect(x=[-5000], y=[-5000], width=1, height=1, color=DEPT_COLORS[d_id], alpha=0.92)
    legend_items.append(LegendItem(label=dept_labels_map[d_id], renderers=[r]))
    for s_id in subdept_order[d_id]:
        r = p_static.rect(x=[-5000], y=[-5000], width=1, height=1, color=SUB_COLORS[s_id], alpha=0.92)
        legend_items.append(LegendItem(label=f"  {id_to_node[s_id]['label']}", renderers=[r]))

legend = Legend(
    items=legend_items,
    location="top_right",
    title="Budget Hierarchy",
    title_text_font_size="18pt",
    label_text_font_size="14pt",
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
    label_text_color=INK_SOFT,
    title_text_color=INK,
    glyph_height=22,
    glyph_width=22,
    spacing=4,
    padding=14,
)
p_static.add_layout(legend, "right")

# --- HTML toggle figure ---
# Centered treemap: offset x by +1100 so center is at ~2300
H_OFF = 1100
html_tm_cx = [x + H_OFF for x in tm_cx_arr]
html_tm_lx = [x + H_OFF for x in tm_lx]
html_tm_vx = [x + H_OFF for x in tm_vx]

# Centered sunburst: center at (2300, 1455)
H_SCX = 2300
sb_xs_html, sb_ys_html = [], []
for i in range(len(sb_inner)):
    angles = np.linspace(sb_start[i], sb_end[i], 32)
    ix = H_SCX + sb_inner[i] * np.cos(angles)
    iy = SCY + sb_inner[i] * np.sin(angles)
    ox = H_SCX + sb_outer[i] * np.cos(angles[::-1])
    oy = SCY + sb_outer[i] * np.sin(angles[::-1])
    sb_xs_html.append(list(ix) + list(ox))
    sb_ys_html.append(list(iy) + list(oy))

p_html = figure(
    width=4800,
    height=2700,
    x_range=(-50, 4750),
    y_range=(0, 2700),
    tools="hover",
    tooltips="@tooltip",
    toolbar_location=None,
)

p_html.title.text = "hierarchy-toggle-view · python · bokeh · anyplot.ai"
p_html.title.text_font_size = "28pt"
p_html.title.text_color = INK
p_html.title.text_font_style = "bold"
p_html.background_fill_color = PAGE_BG
p_html.border_fill_color = PAGE_BG
p_html.outline_line_color = None
p_html.xaxis.visible = False
p_html.yaxis.visible = False
p_html.grid.visible = False

html_tm_source = ColumnDataSource(
    data={
        "x": html_tm_cx,
        "y": tm_cy_arr,
        "width": tm_w_arr,
        "height": tm_h_arr,
        "color": tm_colors,
        "tooltip": tm_tooltip,
    }
)
html_tm_rect = p_html.rect(
    x="x",
    y="y",
    width="width",
    height="height",
    color="color",
    source=html_tm_source,
    line_color=PAGE_BG,
    line_width=3,
    alpha=0.92,
)
html_tm_name = p_html.text(
    x=[html_tm_lx[i] for i in range(len(html_tm_lx)) if large_mask[i]],
    y=[tm_ly[i] for i in range(len(tm_ly)) if large_mask[i]],
    text=[tm_text[i] for i in range(len(tm_text)) if large_mask[i]],
    text_font_size="18pt",
    text_color=INK,
    text_align="center",
    text_baseline="middle",
    text_font_style="bold",
)
html_tm_val = p_html.text(
    x=[html_tm_vx[i] for i in range(len(html_tm_vx)) if large_mask[i]],
    y=[tm_vy[i] for i in range(len(tm_vy)) if large_mask[i]],
    text=[tm_vals[i] for i in range(len(tm_vals)) if large_mask[i]],
    text_font_size="15pt",
    text_color=INK_SOFT,
    text_align="center",
    text_baseline="middle",
)

html_sb_source = ColumnDataSource(data={"xs": sb_xs_html, "ys": sb_ys_html, "color": sb_colors, "tooltip": sb_tooltip})
html_sb_patches = p_html.patches(
    xs="xs", ys="ys", color="color", source=html_sb_source, line_color=PAGE_BG, line_width=3, alpha=0.92
)
html_sb_patches.visible = False

# Legend for HTML figure
html_legend_items = []
for d_id in dept_order:
    r = p_html.rect(x=[-5000], y=[-5000], width=1, height=1, color=DEPT_COLORS[d_id], alpha=0.92)
    html_legend_items.append(LegendItem(label=dept_labels_map[d_id], renderers=[r]))
    for s_id in subdept_order[d_id]:
        r = p_html.rect(x=[-5000], y=[-5000], width=1, height=1, color=SUB_COLORS[s_id], alpha=0.92)
        html_legend_items.append(LegendItem(label=f"  {id_to_node[s_id]['label']}", renderers=[r]))

html_legend = Legend(
    items=html_legend_items,
    location="top_right",
    title="Budget Hierarchy",
    title_text_font_size="18pt",
    label_text_font_size="14pt",
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
    label_text_color=INK_SOFT,
    title_text_color=INK,
    glyph_height=22,
    glyph_width=22,
    spacing=4,
    padding=14,
)
p_html.add_layout(html_legend, "right")

# Toggle buttons
btn_treemap = Button(label="Treemap View", button_type="primary", width=220, height=55)
btn_sunburst = Button(label="Sunburst View", button_type="default", width=220, height=55)

toggle_treemap_js = CustomJS(
    args={
        "tm_rect": html_tm_rect,
        "tm_name": html_tm_name,
        "tm_val": html_tm_val,
        "sb": html_sb_patches,
        "btn_tm": btn_treemap,
        "btn_sb": btn_sunburst,
    },
    code="""
    tm_rect.visible = true;
    tm_name.visible = true;
    tm_val.visible = true;
    sb.visible = false;
    btn_tm.button_type = 'primary';
    btn_sb.button_type = 'default';
    """,
)
toggle_sunburst_js = CustomJS(
    args={
        "tm_rect": html_tm_rect,
        "tm_name": html_tm_name,
        "tm_val": html_tm_val,
        "sb": html_sb_patches,
        "btn_tm": btn_treemap,
        "btn_sb": btn_sunburst,
    },
    code="""
    tm_rect.visible = false;
    tm_name.visible = false;
    tm_val.visible = false;
    sb.visible = true;
    btn_tm.button_type = 'default';
    btn_sb.button_type = 'primary';
    """,
)

btn_treemap.js_on_click(toggle_treemap_js)
btn_sunburst.js_on_click(toggle_sunburst_js)

html_layout = column(row(btn_treemap, btn_sunburst), p_html)

# Save HTML (toggle interactive version)
output_file(f"plot-{THEME}.html")
save(html_layout, resources=CDN, title="Hierarchy Toggle View")

# Screenshot static side-by-side figure with Selenium
_static_html = f"_plot_static_{THEME}.html"
output_file(_static_html)
save(p_static, resources=CDN, title="Hierarchy Toggle View Static")

W, H = 4800, 2700
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)

driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(_static_html).resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

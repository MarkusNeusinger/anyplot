""" anyplot.ai
bar-drilldown: Column Chart with Hierarchical Drilling
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-20
"""

import os
import sys
import time
from pathlib import Path


# This file is named bokeh.py — remove its directory from sys.path so that
# `import bokeh` resolves to the installed package, not this file itself.
sys.path = [p for p in sys.path if Path(p).resolve() != Path(__file__).resolve().parent]

from bokeh.io import save
from bokeh.layouts import column, row
from bokeh.models import Button, ColumnDataSource, CustomJS, Div, LabelSet, TapTool
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data: 3-level geographic sales hierarchy (Region → Country → City)
hierarchy_data = {
    "root": {"children": ["north_america", "europe", "asia_pacific"]},
    "north_america": {"name": "North America", "value": 450, "parent": "root", "children": ["usa", "canada", "mexico"]},
    "europe": {"name": "Europe", "value": 380, "parent": "root", "children": ["uk", "germany", "france"]},
    "asia_pacific": {
        "name": "Asia Pacific",
        "value": 320,
        "parent": "root",
        "children": ["japan", "australia", "singapore"],
    },
    "usa": {"name": "USA", "value": 280, "parent": "north_america", "children": ["new_york", "los_angeles", "chicago"]},
    "canada": {
        "name": "Canada",
        "value": 95,
        "parent": "north_america",
        "children": ["toronto", "vancouver", "montreal"],
    },
    "mexico": {
        "name": "Mexico",
        "value": 75,
        "parent": "north_america",
        "children": ["mexico_city", "guadalajara", "monterrey"],
    },
    "uk": {"name": "UK", "value": 140, "parent": "europe", "children": ["london", "manchester", "birmingham"]},
    "germany": {"name": "Germany", "value": 130, "parent": "europe", "children": ["berlin", "munich", "hamburg"]},
    "france": {"name": "France", "value": 110, "parent": "europe", "children": ["paris", "lyon", "marseille"]},
    "japan": {"name": "Japan", "value": 150, "parent": "asia_pacific", "children": ["tokyo", "osaka", "kyoto"]},
    "australia": {
        "name": "Australia",
        "value": 100,
        "parent": "asia_pacific",
        "children": ["sydney", "melbourne", "brisbane"],
    },
    "singapore": {"name": "Singapore", "value": 70, "parent": "asia_pacific", "children": []},
    "new_york": {"name": "New York", "value": 120, "parent": "usa", "children": []},
    "los_angeles": {"name": "Los Angeles", "value": 95, "parent": "usa", "children": []},
    "chicago": {"name": "Chicago", "value": 65, "parent": "usa", "children": []},
    "toronto": {"name": "Toronto", "value": 45, "parent": "canada", "children": []},
    "vancouver": {"name": "Vancouver", "value": 30, "parent": "canada", "children": []},
    "montreal": {"name": "Montreal", "value": 20, "parent": "canada", "children": []},
    "mexico_city": {"name": "Mexico City", "value": 40, "parent": "mexico", "children": []},
    "guadalajara": {"name": "Guadalajara", "value": 20, "parent": "mexico", "children": []},
    "monterrey": {"name": "Monterrey", "value": 15, "parent": "mexico", "children": []},
    "london": {"name": "London", "value": 65, "parent": "uk", "children": []},
    "manchester": {"name": "Manchester", "value": 40, "parent": "uk", "children": []},
    "birmingham": {"name": "Birmingham", "value": 35, "parent": "uk", "children": []},
    "berlin": {"name": "Berlin", "value": 55, "parent": "germany", "children": []},
    "munich": {"name": "Munich", "value": 45, "parent": "germany", "children": []},
    "hamburg": {"name": "Hamburg", "value": 30, "parent": "germany", "children": []},
    "paris": {"name": "Paris", "value": 50, "parent": "france", "children": []},
    "lyon": {"name": "Lyon", "value": 35, "parent": "france", "children": []},
    "marseille": {"name": "Marseille", "value": 25, "parent": "france", "children": []},
    "tokyo": {"name": "Tokyo", "value": 70, "parent": "japan", "children": []},
    "osaka": {"name": "Osaka", "value": 50, "parent": "japan", "children": []},
    "kyoto": {"name": "Kyoto", "value": 30, "parent": "japan", "children": []},
    "sydney": {"name": "Sydney", "value": 45, "parent": "australia", "children": []},
    "melbourne": {"name": "Melbourne", "value": 35, "parent": "australia", "children": []},
    "brisbane": {"name": "Brisbane", "value": 20, "parent": "australia", "children": []},
}

# Initial root-level data
root_children = hierarchy_data["root"]["children"]
init_names = [hierarchy_data[c]["name"] for c in root_children]
init_values = [hierarchy_data[c]["value"] for c in root_children]
init_max = max(init_values)

source = ColumnDataSource(
    data={
        "names": init_names,
        "values": init_values,
        "ids": root_children,
        "colors": [OKABE_ITO[i % len(OKABE_ITO)] for i in range(len(init_names))],
        "has_children": [len(hierarchy_data[c].get("children", [])) > 0 for c in root_children],
        "label_y": [v + init_max * 0.025 for v in init_values],
    }
)

state_source = ColumnDataSource(
    data={"current_parent": ["root"], "breadcrumb_path": ["All"], "breadcrumb_ids": ["root"]}
)

# Plot — figure height 1640 leaves room for nav row in the combined layout
p = figure(
    x_range=init_names,
    width=3200,
    height=1640,
    title="bar-drilldown · python · bokeh · anyplot.ai",
    tools="tap",
    toolbar_location=None,
    x_axis_label="Region",
    y_axis_label="Sales ($ millions)",
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

p.vbar(
    x="names",
    top="values",
    width=0.65,
    source=source,
    fill_color="colors",
    line_color=PAGE_BG,
    line_width=3,
    fill_alpha=0.92,
)

labels = LabelSet(
    x="names",
    y="label_y",
    text="values",
    source=source,
    text_align="center",
    text_baseline="bottom",
    text_font_size="34pt",
    text_font_style="bold",
    text_color=INK,
)
p.add_layout(labels)

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_font_size = "50pt"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_orientation = 0

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

p.y_range.start = 0
p.y_range.end = init_max * 1.18

# Navigation: breadcrumb trail + back button
breadcrumb_div = Div(
    text=(
        f'<div style="font-size:28pt;font-family:Arial,sans-serif;'
        f"padding:14px 20px;background:{ELEVATED_BG};"
        f"border-radius:8px;display:inline-block;"
        f'color:{INK};border:1px solid {INK_SOFT};">'
        f"<b>All</b></div>"
    ),
    width=2700,
    height=90,
)

back_button = Button(label="← Back", button_type="primary", width=240, height=90, disabled=True)

# Drill-down: click a bar to show its children
drill_callback = CustomJS(
    args={
        "source": source,
        "state": state_source,
        "p": p,
        "hierarchy": hierarchy_data,
        "okabe_ito": OKABE_ITO,
        "breadcrumb_div": breadcrumb_div,
        "back_button": back_button,
        "ink": INK,
        "ink_soft": INK_SOFT,
        "elevated_bg": ELEVATED_BG,
    },
    code="""
    const indices = source.selected.indices;
    if (indices.length === 0) return;
    const idx = indices[0];
    const clicked_id = source.data['ids'][idx];
    const node = hierarchy[clicked_id];
    if (!node || !node.children || node.children.length === 0) {
        source.selected.indices = [];
        return;
    }
    const children_ids = node.children;
    const names = [], values = [], has_children = [];
    for (const cid of children_ids) {
        const c = hierarchy[cid];
        names.push(c.name);
        values.push(c.value);
        has_children.push(c.children && c.children.length > 0);
    }
    source.data['names'] = names;
    source.data['values'] = values;
    source.data['ids'] = children_ids;
    source.data['has_children'] = has_children;
    source.data['colors'] = names.map((_, i) => okabe_ito[i % okabe_ito.length]);
    const max_v = Math.max(...values);
    source.data['label_y'] = values.map(v => v + max_v * 0.025);
    p.x_range.factors = names;
    p.y_range.end = max_v * 1.18;
    const path = state.data['breadcrumb_path'].slice();
    const ids_path = state.data['breadcrumb_ids'].slice();
    path.push(node.name);
    ids_path.push(clicked_id);
    state.data['current_parent'] = [clicked_id];
    state.data['breadcrumb_path'] = path;
    state.data['breadcrumb_ids'] = ids_path;
    let html = '<div style="font-size:28pt;font-family:Arial,sans-serif;padding:14px 20px;background:' + elevated_bg + ';border-radius:8px;display:inline-block;color:' + ink + ';border:1px solid ' + ink_soft + ';">';
    for (let i = 0; i < path.length; i++) {
        if (i > 0) html += ' <span style="color:' + ink_soft + ';">›</span> ';
        html += (i === path.length - 1) ? '<b>' + path[i] + '</b>' : path[i];
    }
    html += '</div>';
    breadcrumb_div.text = html;
    back_button.disabled = false;
    source.selected.indices = [];
    source.change.emit();
    state.change.emit();
""",
)

# Drill-up: back button navigates to parent level
drill_up_callback = CustomJS(
    args={
        "source": source,
        "state": state_source,
        "p": p,
        "hierarchy": hierarchy_data,
        "okabe_ito": OKABE_ITO,
        "breadcrumb_div": breadcrumb_div,
        "back_button": back_button,
        "ink": INK,
        "ink_soft": INK_SOFT,
        "elevated_bg": ELEVATED_BG,
    },
    code="""
    const path = state.data['breadcrumb_path'];
    const ids_path = state.data['breadcrumb_ids'];
    if (ids_path.length <= 1) return;
    const new_path = path.slice(0, -1);
    const new_ids = ids_path.slice(0, -1);
    const parent_id = new_ids[new_ids.length - 1];
    const children_ids = (parent_id === 'root') ? hierarchy['root']['children'] : hierarchy[parent_id]['children'];
    const names = [], values = [], has_children = [];
    for (const cid of children_ids) {
        const c = hierarchy[cid];
        names.push(c.name);
        values.push(c.value);
        has_children.push(c.children && c.children.length > 0);
    }
    source.data['names'] = names;
    source.data['values'] = values;
    source.data['ids'] = children_ids;
    source.data['has_children'] = has_children;
    source.data['colors'] = names.map((_, i) => okabe_ito[i % okabe_ito.length]);
    const max_v = Math.max(...values);
    source.data['label_y'] = values.map(v => v + max_v * 0.025);
    p.x_range.factors = names;
    p.y_range.end = max_v * 1.18;
    state.data['current_parent'] = [parent_id];
    state.data['breadcrumb_path'] = new_path;
    state.data['breadcrumb_ids'] = new_ids;
    let html = '<div style="font-size:28pt;font-family:Arial,sans-serif;padding:14px 20px;background:' + elevated_bg + ';border-radius:8px;display:inline-block;color:' + ink + ';border:1px solid ' + ink_soft + ';">';
    for (let i = 0; i < new_path.length; i++) {
        if (i > 0) html += ' <span style="color:' + ink_soft + ';">›</span> ';
        html += (i === new_path.length - 1) ? '<b>' + new_path[i] + '</b>' : new_path[i];
    }
    html += '</div>';
    breadcrumb_div.text = html;
    if (new_ids.length <= 1) back_button.disabled = true;
    source.change.emit();
    state.change.emit();
""",
)

back_button.js_on_click(drill_up_callback)
p.select(TapTool).callback = drill_callback

nav_row = row(breadcrumb_div, back_button, spacing=20)
layout = column(nav_row, p, spacing=10)

# Save HTML for interactive use
save(layout, filename=f"plot-{THEME}.html", title="bar-drilldown · python · bokeh · anyplot.ai")

# Save PNG via headless Chrome (Selenium) — export_png is not reliable in this env
W, H = 3200, 1860
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
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

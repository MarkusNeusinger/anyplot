"""anyplot.ai
map-drilldown-geographic: Drillable Geographic Map
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 88/100 | Updated: 2026-05-23
"""

import base64
import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.layouts import column
from bokeh.models import (
    BooleanFilter,
    Button,
    CDSView,
    ColorBar,
    ColumnDataSource,
    CustomJS,
    HoverTool,
    Label,
    LinearColorMapper,
    TapTool,
    Title,
)
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


np.random.seed(42)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
OCEAN_BG = "#D6EAF8" if THEME == "light" else "#1C2833"


# anyplot_seq: brand green (#009E73) → dark azure (#003D94)
ANYPLOT_SEQ256 = [
    "#{:02X}{:02X}{:02X}".format(
        int(round(0x00 + (0x00 - 0x00) * t / 255)),
        int(round(0x9E + (0x3D - 0x9E) * t / 255)),
        int(round(0x73 + (0x94 - 0x73) * t / 255)),
    )
    for t in range(256)
]

# Data: Americas region, annual sales ($M) — hierarchical countries → states → cities

country_xs = [
    [-125, -65, -65, -125],
    [-140, -50, -50, -140],
    [-118, -86, -86, -118],
    [-74, -34, -34, -74],
    [-73, -53, -53, -73],
]
country_ys = [[24, 24, 49, 49], [49, 49, 72, 72], [14, 14, 32, 32], [-34, -34, 5, 5], [-55, -55, -22, -22]]
country_names = ["United States", "Canada", "Mexico", "Brazil", "Argentina"]
country_values = [850, 320, 180, 420, 95]
country_cx = [-95, -95, -102, -54, -63]
country_cy = [38, 61, 24, -14, -37]
country_cy_val = [32, 55, 18, -20, -43]
country_labels = [f"${v}M" for v in country_values]

us_xs = [
    [-124, -114, -114, -124],
    [-106, -93, -93, -106],
    [-80, -72, -72, -80],
    [-87, -80, -80, -87],
    [-91, -87, -87, -91],
    [-124, -117, -117, -124],
]
us_ys = [[32, 32, 42, 42], [26, 26, 36, 36], [40, 40, 45, 45], [25, 25, 31, 31], [37, 37, 42, 42], [45, 45, 49, 49]]
us_names = ["California", "Texas", "New York", "Florida", "Illinois", "Washington"]
us_values = [220, 180, 150, 120, 90, 90]
us_cx = [-119, -99.5, -76, -83.5, -89, -120.5]
us_cy = [38.5, 32.5, 43.0, 29.5, 40.5, 47.5]
us_cy_val = [36.5, 30.5, 41.5, 27.5, 38.5, 46.0]
us_labels = [f"${v}M" for v in us_values]

ca_xs = [
    [-123.3, -122.9, -122.9, -123.3],
    [-123.5, -123.2, -123.2, -123.5],
    [-122.9, -122.5, -122.5, -122.9],
    [-123.0, -122.8, -122.8, -123.0],
    [-119.6, -119.3, -119.3, -119.6],
]
ca_ys = [
    [33.5, 33.5, 34.5, 34.5],
    [37.3, 37.3, 38.0, 38.0],
    [32.4, 32.4, 33.2, 33.2],
    [38.2, 38.2, 39.0, 39.0],
    [37.0, 37.0, 37.6, 37.6],
]
ca_names = ["Los Angeles", "San Francisco", "San Diego", "Sacramento", "San Jose"]
ca_values = [85, 55, 35, 25, 20]
ca_cx = [-118.15, -122.4, -117.15, -121.4, -121.85]
ca_cy = [34.2, 37.85, 33.0, 38.8, 37.5]
ca_cy_val = [33.8, 37.45, 32.6, 38.4, 37.15]
ca_labels = [f"${v}M" for v in ca_values]

cn_xs = [
    [-95, -74, -74, -95],
    [-80, -57, -57, -80],
    [-139, -120, -120, -139],
    [-120, -110, -110, -120],
    [-102, -95, -95, -102],
]
cn_ys = [[42, 42, 57, 57], [45, 45, 63, 63], [49, 49, 60, 60], [49, 49, 60, 60], [49, 49, 60, 60]]
cn_names = ["Ontario", "Quebec", "British Columbia", "Alberta", "Manitoba"]
cn_values = [120, 80, 65, 40, 15]
cn_cx = [-84.5, -68.5, -129.5, -115.0, -98.5]
cn_cy = [50.5, 55.0, 55.0, 55.0, 55.0]
cn_cy_val = [48.5, 53.0, 53.0, 53.0, 53.0]
cn_labels = [f"${v}M" for v in cn_values]

bc_xs = [
    [-123.3, -122.9, -122.9, -123.3],
    [-123.5, -123.2, -123.2, -123.5],
    [-122.9, -122.5, -122.5, -122.9],
    [-123.0, -122.8, -122.8, -123.0],
    [-119.6, -119.3, -119.3, -119.6],
]
bc_ys = [
    [49.2, 49.2, 49.4, 49.4],
    [48.4, 48.4, 48.6, 48.6],
    [49.0, 49.0, 49.2, 49.2],
    [49.2, 49.2, 49.3, 49.3],
    [49.8, 49.8, 50.1, 50.1],
]
bc_names = ["Vancouver", "Victoria", "Surrey", "Burnaby", "Kelowna"]
bc_values = [30, 15, 10, 6, 4]
bc_cx = [-123.1, -123.35, -122.7, -122.9, -119.45]
bc_cy = [49.35, 48.55, 49.15, 49.27, 49.97]
bc_cy_val = [49.23, 48.43, 49.03, 49.22, 49.85]
bc_labels = [f"${v}M" for v in bc_values]

# Color mapper: full data range across all levels
color_mapper = LinearColorMapper(palette=ANYPLOT_SEQ256, low=0, high=850)

# Figure — canonical 3200×1800; btn_back is hidden initially (display:none) so adds no height
p = figure(
    width=3200,
    height=1800,
    x_range=(-140, -25),
    y_range=(-60, 75),
    tools="pan,wheel_zoom,reset",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=280,
)

p.title.text = "map-drilldown-geographic · python · bokeh · anyplot.ai"
p.title.text_font_size = "50pt"
p.title.align = "center"
p.title.text_color = INK

breadcrumb_title = Title(
    text="📍 World",
    text_font_size="30pt",
    text_color=INK,
    align="left",
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.9,
    border_line_color=INK_SOFT,
    border_line_width=1,
    standoff=6,
)
p.add_layout(breadcrumb_title, "above")

instruction_title = Title(
    text="Click a shaded region to drill down  •  Use ← Back button to navigate up the hierarchy",
    text_font_size="24pt",
    text_color=INK_SOFT,
    align="center",
    standoff=8,
)
p.add_layout(instruction_title, "below")

p.background_fill_color = OCEAN_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.outline_line_width = 1

p.xaxis.axis_label = "Longitude"
p.yaxis.axis_label = "Latitude"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Country source shared between drillable and leaf renderers
country_src = ColumnDataSource(
    data={
        "xs": country_xs,
        "ys": country_ys,
        "name": country_names,
        "value": country_values,
        "cx": country_cx,
        "cy": country_cy,
        "cy_val": country_cy_val,
        "label_val": country_labels,
    }
)

# CDSViews split drillable (US, Canada) from leaf (Mexico, Brazil, Argentina)
drillable_view = CDSView(filter=BooleanFilter(booleans=[True, True, False, False, False]))
leaf_view = CDSView(filter=BooleanFilter(booleans=[False, False, True, True, True]))

# Drillable countries: full opacity, solid border
country_drillable_r = p.patches(
    xs="xs",
    ys="ys",
    source=country_src,
    view=drillable_view,
    fill_color={"field": "value", "transform": color_mapper},
    line_color=INK_SOFT,
    line_width=4,
    fill_alpha=0.85,
    hover_fill_alpha=0.95,
    hover_line_color=INK,
    hover_line_width=5,
    visible=True,
)

# Leaf countries: reduced opacity + dashed border signals "no drill-down available"
country_leaf_r = p.patches(
    xs="xs",
    ys="ys",
    source=country_src,
    view=leaf_view,
    fill_color={"field": "value", "transform": color_mapper},
    line_color=INK_SOFT,
    line_width=3,
    fill_alpha=0.45,
    line_dash="dashed",
    hover_fill_alpha=0.55,
    hover_line_color=INK,
    hover_line_width=4,
    visible=True,
)

country_names_r = p.text(
    x="cx",
    y="cy",
    text="name",
    source=country_src,
    text_font_size="34pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK,
    text_font_style="bold",
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.88,
    visible=True,
)
country_vals_r = p.text(
    x="cx",
    y="cy_val",
    text="label_val",
    source=country_src,
    text_font_size="28pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK_SOFT,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.88,
    visible=True,
)

# Narrative annotation: guide viewer to the top-performing region
us_top_label = Label(
    x=-123,
    y=45,
    text="★  United States leads — $850M",
    text_font_size="26pt",
    text_color="#009E73",
    text_font_style="bold",
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.92,
    border_line_color="#009E73",
    border_line_width=2,
    visible=True,
)
p.add_layout(us_top_label)

us_src = ColumnDataSource(
    data={
        "xs": us_xs,
        "ys": us_ys,
        "name": us_names,
        "value": us_values,
        "cx": us_cx,
        "cy": us_cy,
        "cy_val": us_cy_val,
        "label_val": us_labels,
    }
)
us_patches_r = p.patches(
    xs="xs",
    ys="ys",
    source=us_src,
    fill_color={"field": "value", "transform": color_mapper},
    line_color=INK_SOFT,
    line_width=3,
    fill_alpha=0.85,
    hover_fill_alpha=0.95,
    hover_line_color=INK,
    hover_line_width=4,
    visible=False,
)
us_names_r = p.text(
    x="cx",
    y="cy",
    text="name",
    source=us_src,
    text_font_size="28pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK,
    text_font_style="bold",
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.88,
    visible=False,
)
us_vals_r = p.text(
    x="cx",
    y="cy_val",
    text="label_val",
    source=us_src,
    text_font_size="22pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK_SOFT,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.88,
    visible=False,
)

ca_src = ColumnDataSource(
    data={
        "xs": ca_xs,
        "ys": ca_ys,
        "name": ca_names,
        "value": ca_values,
        "cx": ca_cx,
        "cy": ca_cy,
        "cy_val": ca_cy_val,
        "label_val": ca_labels,
    }
)
ca_patches_r = p.patches(
    xs="xs",
    ys="ys",
    source=ca_src,
    fill_color={"field": "value", "transform": color_mapper},
    line_color=INK_SOFT,
    line_width=2,
    fill_alpha=0.85,
    hover_fill_alpha=0.95,
    hover_line_color=INK,
    hover_line_width=3,
    visible=False,
)
ca_names_r = p.text(
    x="cx",
    y="cy",
    text="name",
    source=ca_src,
    text_font_size="22pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK,
    text_font_style="bold",
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.88,
    visible=False,
)
ca_vals_r = p.text(
    x="cx",
    y="cy_val",
    text="label_val",
    source=ca_src,
    text_font_size="18pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK_SOFT,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.88,
    visible=False,
)

cn_src = ColumnDataSource(
    data={
        "xs": cn_xs,
        "ys": cn_ys,
        "name": cn_names,
        "value": cn_values,
        "cx": cn_cx,
        "cy": cn_cy,
        "cy_val": cn_cy_val,
        "label_val": cn_labels,
    }
)
cn_patches_r = p.patches(
    xs="xs",
    ys="ys",
    source=cn_src,
    fill_color={"field": "value", "transform": color_mapper},
    line_color=INK_SOFT,
    line_width=3,
    fill_alpha=0.85,
    hover_fill_alpha=0.95,
    hover_line_color=INK,
    hover_line_width=4,
    visible=False,
)
cn_names_r = p.text(
    x="cx",
    y="cy",
    text="name",
    source=cn_src,
    text_font_size="28pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK,
    text_font_style="bold",
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.88,
    visible=False,
)
cn_vals_r = p.text(
    x="cx",
    y="cy_val",
    text="label_val",
    source=cn_src,
    text_font_size="22pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK_SOFT,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.88,
    visible=False,
)

bc_src = ColumnDataSource(
    data={
        "xs": bc_xs,
        "ys": bc_ys,
        "name": bc_names,
        "value": bc_values,
        "cx": bc_cx,
        "cy": bc_cy,
        "cy_val": bc_cy_val,
        "label_val": bc_labels,
    }
)
bc_patches_r = p.patches(
    xs="xs",
    ys="ys",
    source=bc_src,
    fill_color={"field": "value", "transform": color_mapper},
    line_color=INK_SOFT,
    line_width=2,
    fill_alpha=0.85,
    hover_fill_alpha=0.95,
    hover_line_color=INK,
    hover_line_width=3,
    visible=False,
)
bc_names_r = p.text(
    x="cx",
    y="cy",
    text="name",
    source=bc_src,
    text_font_size="22pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK,
    text_font_style="bold",
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.88,
    visible=False,
)
bc_vals_r = p.text(
    x="cx",
    y="cy_val",
    text="label_val",
    source=bc_src,
    text_font_size="18pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK_SOFT,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.88,
    visible=False,
)

color_bar = ColorBar(
    color_mapper=color_mapper,
    width=50,
    height=600,
    location=(0, 0),
    title="Sales ($M)",
    title_text_font_size="28pt",
    title_text_font_style="bold",
    title_text_color=INK,
    major_label_text_font_size="22pt",
    major_label_text_color=INK_SOFT,
    title_standoff=20,
    margin=30,
    padding=20,
    background_fill_color=PAGE_BG,
)
p.add_layout(color_bar, "right")

hover = HoverTool(
    renderers=[country_drillable_r, country_leaf_r, us_patches_r, ca_patches_r, cn_patches_r, bc_patches_r],
    tooltips=[("Region", "@name"), ("Sales", "$@value{0}M")],
)
p.add_tools(hover)

# Back navigation button — hidden initially (display:none adds no layout height for PNG capture)
btn_back = Button(
    label="← World",
    visible=False,
    width=380,
    height=55,
    button_type="default",
    styles={"margin-left": "180px", "margin-bottom": "6px", "font-size": "20px", "font-weight": "bold"},
)

tap_callback = CustomJS(
    args={
        "p": p,
        "country_src": country_src,
        "country_drillable_r": country_drillable_r,
        "country_leaf_r": country_leaf_r,
        "country_names_r": country_names_r,
        "country_vals_r": country_vals_r,
        "us_patches_r": us_patches_r,
        "us_names_r": us_names_r,
        "us_vals_r": us_vals_r,
        "ca_patches_r": ca_patches_r,
        "ca_names_r": ca_names_r,
        "ca_vals_r": ca_vals_r,
        "cn_patches_r": cn_patches_r,
        "cn_names_r": cn_names_r,
        "cn_vals_r": cn_vals_r,
        "bc_patches_r": bc_patches_r,
        "bc_names_r": bc_names_r,
        "bc_vals_r": bc_vals_r,
        "breadcrumb": breadcrumb_title,
        "btn_back": btn_back,
        "us_top_label": us_top_label,
    },
    code="""
const show = (r) => { r.visible = true; };
const hide = (r) => { r.visible = false; };

const sel_c  = country_src.selected.indices;
const sel_us = us_patches_r.data_source.selected.indices;
const sel_ca = ca_patches_r.data_source.selected.indices;
const sel_cn = cn_patches_r.data_source.selected.indices;
const sel_bc = bc_patches_r.data_source.selected.indices;

if (sel_c.length > 0 && country_drillable_r.visible) {
    const idx = sel_c[0];
    const name = country_src.data['name'][idx];
    if (name === 'United States') {
        [country_drillable_r, country_leaf_r, country_names_r, country_vals_r, us_top_label].forEach(hide);
        [us_patches_r, us_names_r, us_vals_r].forEach(show);
        p.x_range.start = -130; p.x_range.end = -65;
        p.y_range.start = 20;   p.y_range.end = 55;
        breadcrumb.text = "📍 World  ›  United States";
        btn_back.label = "← World";
        btn_back.visible = true;
    } else if (name === 'Canada') {
        [country_drillable_r, country_leaf_r, country_names_r, country_vals_r, us_top_label].forEach(hide);
        [cn_patches_r, cn_names_r, cn_vals_r].forEach(show);
        p.x_range.start = -145; p.x_range.end = -50;
        p.y_range.start = 42;   p.y_range.end = 75;
        breadcrumb.text = "📍 World  ›  Canada";
        btn_back.label = "← World";
        btn_back.visible = true;
    }
    // Leaf regions (Mexico, Brazil, Argentina): tap silently ignored — dashed border signals leaf
    country_src.selected.indices = [];
}

if (sel_us.length > 0 && us_patches_r.visible) {
    const name = us_patches_r.data_source.data['name'][sel_us[0]];
    if (name === 'California') {
        [us_patches_r, us_names_r, us_vals_r].forEach(hide);
        [ca_patches_r, ca_names_r, ca_vals_r].forEach(show);
        p.x_range.start = -125; p.x_range.end = -114;
        p.y_range.start = 32;   p.y_range.end = 42;
        breadcrumb.text = "📍 World  ›  United States  ›  California";
        btn_back.label = "← United States";
    }
    us_patches_r.data_source.selected.indices = [];
}

if (sel_cn.length > 0 && cn_patches_r.visible) {
    const name = cn_patches_r.data_source.data['name'][sel_cn[0]];
    if (name === 'British Columbia') {
        [cn_patches_r, cn_names_r, cn_vals_r].forEach(hide);
        [bc_patches_r, bc_names_r, bc_vals_r].forEach(show);
        p.x_range.start = -140; p.x_range.end = -118;
        p.y_range.start = 47;   p.y_range.end = 62;
        breadcrumb.text = "📍 World  ›  Canada  ›  British Columbia";
        btn_back.label = "← Canada";
    }
    cn_patches_r.data_source.selected.indices = [];
}

if (sel_ca.length > 0) { ca_patches_r.data_source.selected.indices = []; }
if (sel_bc.length > 0) { bc_patches_r.data_source.selected.indices = []; }
""",
)

back_callback = CustomJS(
    args={
        "p": p,
        "country_drillable_r": country_drillable_r,
        "country_leaf_r": country_leaf_r,
        "country_names_r": country_names_r,
        "country_vals_r": country_vals_r,
        "us_patches_r": us_patches_r,
        "us_names_r": us_names_r,
        "us_vals_r": us_vals_r,
        "ca_patches_r": ca_patches_r,
        "ca_names_r": ca_names_r,
        "ca_vals_r": ca_vals_r,
        "cn_patches_r": cn_patches_r,
        "cn_names_r": cn_names_r,
        "cn_vals_r": cn_vals_r,
        "bc_patches_r": bc_patches_r,
        "bc_names_r": bc_names_r,
        "bc_vals_r": bc_vals_r,
        "breadcrumb": breadcrumb_title,
        "btn_back": btn_back,
        "us_top_label": us_top_label,
    },
    code="""
const show = (r) => { r.visible = true; };
const hide = (r) => { r.visible = false; };
const lbl = btn_back.label;

if (lbl === "← World") {
    [us_patches_r, us_names_r, us_vals_r,
     cn_patches_r, cn_names_r, cn_vals_r].forEach(hide);
    [country_drillable_r, country_leaf_r, country_names_r, country_vals_r, us_top_label].forEach(show);
    p.x_range.start = -140; p.x_range.end = -25;
    p.y_range.start = -60;  p.y_range.end = 75;
    breadcrumb.text = "📍 World";
    btn_back.visible = false;
} else if (lbl === "← United States") {
    [ca_patches_r, ca_names_r, ca_vals_r].forEach(hide);
    [us_patches_r, us_names_r, us_vals_r].forEach(show);
    p.x_range.start = -130; p.x_range.end = -65;
    p.y_range.start = 20;   p.y_range.end = 55;
    breadcrumb.text = "📍 World  ›  United States";
    btn_back.label = "← World";
} else if (lbl === "← Canada") {
    [bc_patches_r, bc_names_r, bc_vals_r].forEach(hide);
    [cn_patches_r, cn_names_r, cn_vals_r].forEach(show);
    p.x_range.start = -145; p.x_range.end = -50;
    p.y_range.start = 42;   p.y_range.end = 75;
    breadcrumb.text = "📍 World  ›  Canada";
    btn_back.label = "← World";
}
""",
)
btn_back.js_on_click(back_callback)

tap_tool = TapTool(
    callback=tap_callback,
    renderers=[country_drillable_r, country_leaf_r, us_patches_r, ca_patches_r, cn_patches_r, bc_patches_r],
)
p.add_tools(tap_tool)

# Layout: back button above plot; when hidden (initial state) it has display:none so adds no height
layout = column(btn_back, p, spacing=0)

output_file(f"plot-{THEME}.html")
save(layout)

W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H + 200}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
screenshot = driver.execute_cdp_cmd(
    "Page.captureScreenshot",
    {"format": "png", "captureBeyondViewport": True, "clip": {"x": 0, "y": 0, "width": W, "height": H, "scale": 1}},
)
driver.quit()
img_bytes = base64.b64decode(screenshot["data"])
with open(f"plot-{THEME}.png", "wb") as f:
    f.write(img_bytes)

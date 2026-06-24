""" anyplot.ai
line-stress-strain: Engineering Stress-Strain Curve
Library: bokeh 3.9.1 | Python 3.13.14
Quality: 89/100 | Updated: 2026-06-21
"""

import os
import sys
import time
from pathlib import Path


# Prevent this file (bokeh.py) from shadowing the installed bokeh package
_here = str(Path(__file__).resolve().parent)
sys.path = [p for p in sys.path if Path(p).resolve() != Path(_here)]

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem, Span
from bokeh.plotting import figure
from bokeh.resources import CDN
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens — Imprint palette, theme-adaptive chrome
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette — data element colors
COLOR_CURVE = "#009E73"  # position 1 — brand green — primary stress-strain curve
COLOR_YIELD = "#4467A3"  # position 3 — blue — yield point
COLOR_UTS = "#C475FD"  # position 2 — lavender — ultimate tensile strength
COLOR_FRACTURE = "#AE3030"  # position 5 — matte red — fracture (semantic: material failure)
COLOR_OFFSET = "#BD8233"  # position 4 — ochre — 0.2% offset reference line

# Data — Mild steel tensile test (Ludwik power law model)
np.random.seed(42)

youngs_modulus = 210000  # MPa
yield_strength = 250  # MPa
uts = 400  # MPa
fracture_strain = 0.35
uts_strain = 0.22
yield_strain = yield_strength / youngs_modulus  # ~0.00119

# Elastic region
strain_elastic = np.linspace(0, yield_strain, 60)
stress_elastic = youngs_modulus * strain_elastic

# Strain hardening — Ludwik power law
strain_plastic = np.linspace(yield_strain, uts_strain, 200)
plastic_strain = strain_plastic - yield_strain
stress_plastic = yield_strength + (uts - yield_strength) * (plastic_strain / (uts_strain - yield_strain)) ** 0.45

# Necking region (stress drops after UTS)
strain_necking = np.linspace(uts_strain, fracture_strain, 80)
necking_progress = (strain_necking - uts_strain) / (fracture_strain - uts_strain)
stress_necking = uts - (uts - 320) * necking_progress**0.8

# Combined curve with region labels for hover tooltip
strain = np.concatenate([strain_elastic, strain_plastic, strain_necking])
stress = np.concatenate([stress_elastic, stress_plastic, stress_necking])
region_labels = np.concatenate(
    [
        np.full(len(strain_elastic), "Elastic"),
        np.full(len(strain_plastic), "Strain Hardening"),
        np.full(len(strain_necking), "Necking"),
    ]
)

# 0.2% offset line (parallel to elastic slope, shifted right by 0.002)
offset_strain_line = np.linspace(0.002, 0.002 + yield_strength / youngs_modulus + 0.002, 80)
offset_stress_line = youngs_modulus * (offset_strain_line - 0.002)
mask = offset_stress_line <= yield_strength + 30
offset_strain_line = offset_strain_line[mask]
offset_stress_line = offset_stress_line[mask]

# Key points
yield_point_strain = yield_strain + 0.002  # intersection of offset line with curve
yield_point_stress = yield_strength
uts_point_strain = uts_strain
uts_point_stress = uts
fracture_point_strain = fracture_strain
fracture_point_stress = stress_necking[-1]

# Canvas — hard rule: 3200×1800 landscape
W, H = 3200, 1800
p = figure(
    width=W,
    height=H,
    title="line-stress-strain · python · bokeh · anyplot.ai",
    x_axis_label="Engineering Strain (mm/mm)",
    y_axis_label="Engineering Stress (MPa)",
    toolbar_location=None,  # omit to keep PNG at exactly W×H
    min_border_bottom=160,  # room for 34pt tick labels + 42pt axis label
    min_border_left=180,  # room for 34pt tick labels + 42pt axis label
    min_border_top=110,  # room for 50pt title
    min_border_right=60,
)

# Subtle horizontal reference lines at yield and UTS stress levels
p.add_layout(
    Span(
        location=yield_strength,
        dimension="width",
        line_color=COLOR_YIELD,
        line_alpha=0.18,
        line_dash="dotted",
        line_width=2,
    )
)
p.add_layout(
    Span(location=uts, dimension="width", line_color=COLOR_UTS, line_alpha=0.18, line_dash="dotted", line_width=2)
)

# Main stress-strain curve
source = ColumnDataSource(data={"strain": strain, "stress": stress, "region": region_labels})
main_line = p.line(x="strain", y="stress", source=source, line_width=5, color=COLOR_CURVE)

# HoverTool — Bokeh interactive region-aware tooltip
hover = HoverTool(
    renderers=[main_line],
    tooltips=[("Strain", "@strain{0.0000}"), ("Stress", "@stress{0.1} MPa"), ("Region", "@region")],
    mode="vline",
    line_policy="nearest",
)
p.add_tools(hover)

# 0.2% offset line — dashed reference for yield point determination
offset_source = ColumnDataSource(data={"strain": offset_strain_line, "stress": offset_stress_line})
offset_line = p.line(x="strain", y="stress", source=offset_source, line_width=3, line_dash="dashed", color=COLOR_OFFSET)

# Key point markers — distinct shapes for redundant encoding (5 series)
yield_glyph = p.scatter(
    x=[yield_point_strain],
    y=[yield_point_stress],
    size=28,
    color=COLOR_YIELD,
    marker="circle",
    line_color=PAGE_BG,
    line_width=3,
)
uts_glyph = p.scatter(
    x=[uts_point_strain],
    y=[uts_point_stress],
    size=28,
    color=COLOR_UTS,
    marker="triangle",
    line_color=PAGE_BG,
    line_width=3,
)
fracture_glyph = p.scatter(
    x=[fracture_point_strain],
    y=[fracture_point_stress],
    size=28,
    color=COLOR_FRACTURE,
    marker="square",
    line_color=PAGE_BG,
    line_width=3,
)

# Region labels — spread across zones to reduce left-side congestion
p.add_layout(
    Label(x=0.006, y=155, text="Elastic", text_font_size="34pt", text_color=INK_MUTED, text_font_style="italic")
)
p.add_layout(
    Label(x=0.09, y=295, text="Strain Hardening", text_font_size="34pt", text_color=INK_MUTED, text_font_style="italic")
)
p.add_layout(
    Label(x=0.26, y=390, text="Necking", text_font_size="34pt", text_color=INK_MUTED, text_font_style="italic")
)

# Key point annotations — positioned to avoid elastic-zone crowding
p.add_layout(
    Label(
        x=yield_point_strain + 0.022,
        y=yield_point_stress - 30,
        text=f"Yield ({yield_point_stress} MPa)",
        text_font_size="28pt",
        text_color=COLOR_YIELD,
        text_font_style="bold",
    )
)
p.add_layout(
    Label(
        x=uts_point_strain - 0.075,
        y=uts_point_stress + 16,
        text=f"UTS ({uts_point_stress} MPa)",
        text_font_size="28pt",
        text_color=COLOR_UTS,
        text_font_style="bold",
    )
)
p.add_layout(
    Label(
        x=fracture_point_strain - 0.055,
        y=fracture_point_stress - 40,
        text="Fracture",
        text_font_size="28pt",
        text_color=COLOR_FRACTURE,
        text_font_style="bold",
    )
)

# Young's modulus annotation — moved right to clear the elastic/yield zone
p.add_layout(
    Label(
        x=0.040,
        y=45,
        text=f"E = {youngs_modulus // 1000} GPa",
        text_font_size="26pt",
        text_color=COLOR_CURVE,
        text_font_style="bold",
    )
)

# Legend — bottom-right placement, theme-adaptive styling
legend = Legend(
    items=[
        LegendItem(label="Stress-Strain Curve", renderers=[main_line]),
        LegendItem(label="0.2% Offset Line", renderers=[offset_line]),
        LegendItem(label="Yield Point", renderers=[yield_glyph]),
        LegendItem(label="Ultimate Tensile Strength", renderers=[uts_glyph]),
        LegendItem(label="Fracture Point", renderers=[fracture_glyph]),
    ],
    location="bottom_right",
)
legend.label_text_font_size = "28pt"
legend.label_text_color = INK_SOFT
legend.glyph_height = 38
legend.glyph_width = 38
legend.spacing = 12
legend.padding = 24
legend.margin = 20
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 0.92
legend.border_line_color = INK_SOFT
legend.border_line_alpha = 0.35
legend.border_line_width = 1
p.add_layout(legend, "center")

# Typography — canonical Bokeh sizes for 3200×1800
p.title.text_font_size = "50pt"
p.title.text_font_style = "normal"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Axes — L-shaped frame (outline None, axis lines kept)
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Grid — subtle, y-axis only for line chart
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.12

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Data ranges
p.y_range.start = -10
p.y_range.end = 450
p.x_range.start = -0.005
p.x_range.end = 0.38

# Save interactive HTML (catalog artifact)
output_file(f"plot-{THEME}.html")
save(p, resources=CDN)

# Screenshot with headless Chrome — CDP override forces exact W×H viewport
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

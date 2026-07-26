""" anyplot.ai
sunburst-basic: Basic Sunburst Chart
Library: bokeh 3.9.2 | Python 3.13.14
Quality: 90/100 | Updated: 2026-07-26
"""

import os
import sys
import time
from math import cos, pi, sin
from pathlib import Path


# Remove this script's directory from sys.path so "bokeh" resolves to the
# installed package, not this file itself (which is also named bokeh.py).
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.dirname(os.path.abspath(__file__))]

from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Output directory: same folder as this script, regardless of cwd
OUT_DIR = Path(__file__).parent

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Data - Organizational budget breakdown (Department -> Team -> Project)
hierarchy = [
    # Engineering
    {"level_1": "Engineering", "level_2": "Backend", "level_3": "API Platform", "value": 120},
    {"level_1": "Engineering", "level_2": "Backend", "level_3": "Database", "value": 80},
    {"level_1": "Engineering", "level_2": "Frontend", "level_3": "Web App", "value": 100},
    {"level_1": "Engineering", "level_2": "Frontend", "level_3": "Mobile", "value": 60},
    {"level_1": "Engineering", "level_2": "DevOps", "level_3": "Infrastructure", "value": 50},
    # Marketing
    {"level_1": "Marketing", "level_2": "Digital", "level_3": "Social Media", "value": 45},
    {"level_1": "Marketing", "level_2": "Digital", "level_3": "SEO", "value": 35},
    {"level_1": "Marketing", "level_2": "Content", "level_3": "Blog", "value": 30},
    {"level_1": "Marketing", "level_2": "Content", "level_3": "Video", "value": 40},
    # Sales
    {"level_1": "Sales", "level_2": "Enterprise", "level_3": "EMEA", "value": 70},
    {"level_1": "Sales", "level_2": "Enterprise", "level_3": "APAC", "value": 55},
    {"level_1": "Sales", "level_2": "SMB", "level_3": "Direct Sales", "value": 45},
    # Operations
    {"level_1": "Operations", "level_2": "Support", "level_3": "Tier 1", "value": 40},
    {"level_1": "Operations", "level_2": "Support", "level_3": "Tier 2", "value": 25},
    {"level_1": "Operations", "level_2": "HR", "level_3": "Recruiting", "value": 30},
]

# Imprint categorical palette (canonical order) — departments walk positions
# 1->N in hierarchy order (Engineering, Marketing, Sales, Operations).
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]
dept_order = ["Engineering", "Marketing", "Sales", "Operations"]


def _lerp_hex(c0, c1, t):
    r0, g0, b0 = (int(c0[i : i + 2], 16) for i in (1, 3, 5))
    r1, g1, b1 = (int(c1[i : i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(a + (b - a) * t) for a, b in ((r0, r1), (g0, g1), (b0, b1)))
    return f"#{r:02X}{g:02X}{b:02X}"


def _text_on(bg_hex):
    """Fixed (non theme-adaptive) black/white text pick via YIQ luminance —
    data-layer labels sit on data colors that stay constant across themes,
    so their text color must stay constant too."""
    r, g, b = (int(bg_hex[i : i + 2], 16) for i in (1, 3, 5))
    yiq = (r * 299 + g * 587 + b * 114) / 1000
    return "#1A1A17" if yiq >= 128 else "#FFFFFF"


# Department color families: Imprint base tinted toward white for child rings
dept_colors = {
    dept: {"base": base, "mid": _lerp_hex(base, "#FFFFFF", 0.35), "light": _lerp_hex(base, "#FFFFFF", 0.68)}
    for dept, base in zip(dept_order, IMPRINT_PALETTE, strict=True)
}

# Clearer abbreviations than 3-char truncation
dept_abbrev = {"Engineering": "Eng.", "Marketing": "Mktg", "Sales": "Sales", "Operations": "Ops"}

# Calculate totals
level_1_totals = {}
level_2_totals = {}
for item in hierarchy:
    l1, l2, val = item["level_1"], item["level_2"], item["value"]
    level_1_totals[l1] = level_1_totals.get(l1, 0) + val
    level_2_totals[(l1, l2)] = level_2_totals.get((l1, l2), 0) + val

total = sum(item["value"] for item in hierarchy)

# Ring radii — rings touch directly (no radial gap); the white wedge borders
# alone provide separation. A gap here would show as PAGE_BG, which reads as
# a distracting near-black ring on the dark theme.
r1_inner, r1_outer = 0.0, 0.30
r2_inner, r2_outer = 0.30, 0.60
r3_inner, r3_outer = 0.60, 0.92

# Build vectorized segment data for each ring (enables HoverTool)
_keys = ["x", "y", "inner_radius", "outer_radius", "start_angle", "end_angle", "fill_color", "name", "budget"]
l1_data = {k: [] for k in _keys}
l2_data = {k: [] for k in _keys}
l3_data = {k: [] for k in _keys}

l1_angles = {}
l2_angles = {}
l3_labels = []  # (mid_angle, text, fill_color, show) — computed once, reused for labels

# Level 1 segments
start_angle = pi / 2
for l1 in dept_order:
    angle_span = (level_1_totals[l1] / total) * 2 * pi
    end_angle = start_angle - angle_span
    for k, v in zip(
        _keys,
        [0, 0, r1_inner, r1_outer, end_angle, start_angle, dept_colors[l1]["base"], l1, f"${level_1_totals[l1]}K"],
        strict=True,
    ):
        l1_data[k].append(v)
    l1_angles[l1] = {"start": start_angle, "end": end_angle}
    start_angle = end_angle

# Level 2 segments
for l1 in dept_order:
    l1_start = l1_angles[l1]["start"]
    l1_span = l1_start - l1_angles[l1]["end"]
    l2_items = [(k, v) for k, v in level_2_totals.items() if k[0] == l1]
    l1_total = level_1_totals[l1]
    current_start = l1_start
    for (_, l2_name), l2_val in l2_items:
        angle_span = (l2_val / l1_total) * l1_span
        end_angle = current_start - angle_span
        for k, v in zip(
            _keys,
            [0, 0, r2_inner, r2_outer, end_angle, current_start, dept_colors[l1]["mid"], l2_name, f"${l2_val}K"],
            strict=True,
        ):
            l2_data[k].append(v)
        l2_angles[(l1, l2_name)] = {"start": current_start, "end": end_angle}
        current_start = end_angle

# Level 3 segments — mid_angle is computed once here and reused by the label
# loop below instead of being recomputed from the hierarchy a second time.
for item in hierarchy:
    l1, l2, l3, val = item["level_1"], item["level_2"], item["level_3"], item["value"]
    l2_start = l2_angles[(l1, l2)]["start"]
    l2_span = l2_start - l2_angles[(l1, l2)]["end"]
    l2_total = level_2_totals[(l1, l2)]
    l3_items = [h for h in hierarchy if h["level_1"] == l1 and h["level_2"] == l2]
    l3_idx = next(i for i, h in enumerate(l3_items) if h["level_3"] == l3)
    cumulative = sum(l3_items[i]["value"] for i in range(l3_idx))
    seg_start = l2_start - (cumulative / l2_total) * l2_span
    seg_end = seg_start - (val / l2_total) * l2_span
    fill = dept_colors[l1]["light"]
    for k, v in zip(_keys, [0, 0, r3_inner, r3_outer, seg_end, seg_start, fill, l3, f"${val}K"], strict=True):
        l3_data[k].append(v)
    l3_labels.append(((seg_start + seg_end) / 2, l3, fill, val / total > 0.04))

# Plot — square canvas: a sunburst has no preferred horizontal axis.
W = H = 2400
p = figure(
    width=W,
    height=H,
    title="sunburst-basic · bokeh · anyplot.ai",
    toolbar_location=None,
    tools="",
    x_range=(-1.45, 1.45),
    y_range=(-1.85, 1.05),
)

# Draw rings via ColumnDataSource (required for HoverTool)
l1_r = p.annular_wedge(
    x="x",
    y="y",
    inner_radius="inner_radius",
    outer_radius="outer_radius",
    start_angle="start_angle",
    end_angle="end_angle",
    fill_color="fill_color",
    line_color="white",
    line_width=3,
    source=ColumnDataSource(l1_data),
)
l2_r = p.annular_wedge(
    x="x",
    y="y",
    inner_radius="inner_radius",
    outer_radius="outer_radius",
    start_angle="start_angle",
    end_angle="end_angle",
    fill_color="fill_color",
    line_color="white",
    line_width=2,
    source=ColumnDataSource(l2_data),
)
l3_r = p.annular_wedge(
    x="x",
    y="y",
    inner_radius="inner_radius",
    outer_radius="outer_radius",
    start_angle="start_angle",
    end_angle="end_angle",
    fill_color="fill_color",
    line_color="white",
    line_width=1,
    source=ColumnDataSource(l3_data),
)

# Hover tooltips for each ring level
p.add_tools(HoverTool(renderers=[l1_r], tooltips=[("Department", "@name"), ("Budget", "@budget")]))
p.add_tools(HoverTool(renderers=[l2_r], tooltips=[("Team", "@name"), ("Budget", "@budget")]))
p.add_tools(HoverTool(renderers=[l3_r], tooltips=[("Project", "@name"), ("Budget", "@budget")]))

# Level 1 labels (clearer abbreviations) — fixed text color per segment,
# never theme-adaptive INK, since the segment fill is constant across themes.
for l1 in dept_order:
    angles = l1_angles[l1]
    mid_angle = (angles["start"] + angles["end"]) / 2
    label_r = (r1_inner + r1_outer) / 2 + 0.02
    p.add_layout(
        Label(
            x=label_r * cos(mid_angle),
            y=label_r * sin(mid_angle),
            text=dept_abbrev[l1],
            text_font_size="30pt",
            text_color=_text_on(dept_colors[l1]["base"]),
            text_font_style="bold",
            text_align="center",
            text_baseline="middle",
        )
    )

# Level 2 labels (full names, no truncation)
for l1 in dept_order:
    l1_start = l1_angles[l1]["start"]
    l1_span = l1_start - l1_angles[l1]["end"]
    l2_items = [(k, v) for k, v in level_2_totals.items() if k[0] == l1]
    l1_total = level_1_totals[l1]
    current_start = l1_start
    for (_, l2_name), l2_val in l2_items:
        angle_span = (l2_val / l1_total) * l1_span
        end_angle = current_start - angle_span
        if l2_val / total > 0.06:
            mid_angle = (current_start + end_angle) / 2
            label_r = (r2_inner + r2_outer) / 2
            p.add_layout(
                Label(
                    x=label_r * cos(mid_angle),
                    y=label_r * sin(mid_angle),
                    text=l2_name,
                    text_font_size="26pt",
                    text_color=_text_on(dept_colors[l1]["mid"]),
                    text_align="center",
                    text_baseline="middle",
                )
            )
        current_start = end_angle

# Level 3 labels — reuses mid_angle/fill computed during the segment build above.
for mid_angle, text, fill, show in l3_labels:
    if show:
        label_r = (r3_inner + r3_outer) / 2
        p.add_layout(
            Label(
                x=label_r * cos(mid_angle),
                y=label_r * sin(mid_angle),
                text=text,
                text_font_size="21pt",
                text_color=_text_on(fill),
                text_align="center",
                text_baseline="middle",
            )
        )

# Ring level labels
for radius, text in [(0.14, "Department"), (0.44, "Team"), (0.76, "Project")]:
    p.add_layout(
        Label(
            x=radius,
            y=-1.0,
            text=text,
            text_font_size="20pt",
            text_color=INK_MUTED,
            text_align="center",
            text_baseline="middle",
        )
    )

# Legend — horizontal row below the rings (square canvas has no side gutter)
legend_y_swatch = -1.32
legend_y_label = -1.55
legend_col_x = [-1.09, -0.36, 0.36, 1.09]

for i, l1 in enumerate(dept_order):
    colors = dept_colors[l1]
    cx = legend_col_x[i]
    for shade, x_off in [("base", -0.09), ("mid", 0.0), ("light", 0.09)]:
        p.rect(
            x=cx + x_off,
            y=legend_y_swatch,
            width=0.08,
            height=0.16,
            fill_color=colors[shade],
            line_color=PAGE_BG,
            line_width=1,
        )
    p.add_layout(
        Label(
            x=cx,
            y=legend_y_label,
            text=l1,
            text_font_size="22pt",
            text_color=INK,
            text_font_style="bold",
            text_align="center",
            text_baseline="middle",
        )
    )
    p.add_layout(
        Label(
            x=cx,
            y=legend_y_label - 0.16,
            text=f"${level_1_totals[l1]}K",
            text_font_size="19pt",
            text_color=INK_SOFT,
            text_align="center",
            text_baseline="middle",
        )
    )

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Save HTML (use OUT_DIR so script runs correctly from any cwd)
html_path = OUT_DIR / f"plot-{THEME}.html"
png_path = OUT_DIR / f"plot-{THEME}.png"
output_file(str(html_path))
save(p)

# Screenshot with headless Chrome
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
driver.get(f"file://{html_path.resolve()}")
# Headless Chrome's --window-size sets the OUTER window, which still reserves
# a phantom title-bar height even headless — pin the viewport exactly via CDP.
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(str(png_path))
driver.quit()

"""anyplot.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: bokeh 3.9.1 | Python 3.13.13
Quality: 89/100 | Updated: 2026-06-08
"""

import os
import sys
import time
from pathlib import Path


# Prevent this script (bokeh.py) from shadowing the installed bokeh package when
# Python adds its own directory to sys.path[0] on direct invocation.
sys.path = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != os.path.dirname(os.path.abspath(__file__))]

import numpy as np
from bokeh.io import save
from bokeh.models import ColumnDataSource, FactorRange, HoverTool, Label, Legend, LegendItem, Range1d, Span
from bokeh.plotting import figure
from bokeh.resources import CDN
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# --- Theme ---
THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome tokens (Imprint palette)
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — 8 hues, theme-independent, hybrid-v3 sort
IMPRINT_PALETTE = [
    "#009E73",  # 1: brand green  — ALWAYS first series
    "#C475FD",  # 2: lavender
    "#4467A3",  # 3: blue
    "#BD8233",  # 4: ochre
    "#AE3030",  # 5: matte red   — semantic anchor: bad / loss / error
    "#2ABCCD",  # 6: cyan
    "#954477",  # 7: rose
    "#99B314",  # 8: lime green  — growth / recovery
]
ANYPLOT_AMBER = "#DDCC77"  # warning / caution semantic anchor

# --- Data: Simulated Phase II oncology trial, 25 patients, two treatment arms ---
np.random.seed(42)

n_patients = 25
patient_ids = [f"PT-{i + 1:03d}" for i in range(n_patients)]
arms = np.random.choice(["Arm A (Combo)", "Arm B (Mono)"], size=n_patients, p=[0.52, 0.48])
durations = np.round(np.random.exponential(scale=18, size=n_patients) + 4, 1)
durations = np.clip(durations, 4, 52)

event_labels_map = {
    "partial_response": "Partial Response",
    "complete_response": "Complete Response",
    "progressive_disease": "Progressive Disease",
    "adverse_event": "Adverse Event",
}

events_time = []
events_type = []
events_patient = []
events_label = []
ongoing_patients = set()

for i in range(n_patients):
    dur = durations[i]
    patient_events = []

    if np.random.random() < 0.6:
        t = np.round(np.random.uniform(4, min(dur * 0.4, 12)), 1)
        patient_events.append((t, "partial_response"))

    if np.random.random() < 0.3 and dur > 16:
        t = np.round(np.random.uniform(12, min(dur * 0.6, 24)), 1)
        patient_events.append((t, "complete_response"))

    if np.random.random() < 0.35:
        t = np.round(np.random.uniform(2, dur * 0.8), 1)
        patient_events.append((t, "adverse_event"))

    if np.random.random() < 0.4 and dur < 30:
        t = np.round(dur - np.random.uniform(0, 2), 1)
        patient_events.append((t, "progressive_disease"))

    if dur > 25 and not any(e[1] == "progressive_disease" for e in patient_events):
        ongoing_patients.add(i)

    for t, etype in patient_events:
        events_time.append(t)
        events_type.append(etype)
        events_patient.append(patient_ids[i])
        events_label.append(event_labels_map[etype])

# Sort patients by duration (longest at top)
sort_idx = np.argsort(durations)[::-1]
sorted_patient_ids = [patient_ids[i] for i in sort_idx]
sorted_durations = [durations[i] for i in sort_idx]
sorted_arms = [arms[i] for i in sort_idx]

# Arm colors: Imprint palette positions 1 and 2 (first series always #009E73)
arm_colors = {
    "Arm A (Combo)": IMPRINT_PALETTE[0],  # #009E73 brand green
    "Arm B (Mono)": IMPRINT_PALETTE[1],  # #C475FD lavender
}

median_duration = float(np.median(durations))

# --- Plot ---
W, H = 3200, 1800

p = figure(
    y_range=FactorRange(*sorted_patient_ids),
    width=W,
    height=H,
    title="swimmer-clinical-timeline · python · bokeh · anyplot.ai",
    x_axis_label="Time on Study (Weeks)",
    toolbar_location=None,  # must be None — toolbar adds ~30-50px, causing canvas size drift
    min_border_bottom=160,  # room for 28pt x-tick labels + 42pt x-axis label
    min_border_left=200,  # room for 20pt y-tick labels + 42pt y-axis label
    min_border_top=110,  # room for 50pt title
    min_border_right=60,
)

# Horizontal bars per treatment arm
bars_a = bars_b = None
for arm_name, arm_color in arm_colors.items():
    idx = [i for i, a in enumerate(sorted_arms) if a == arm_name]
    source = ColumnDataSource(
        data={
            "y": [sorted_patient_ids[i] for i in idx],
            "right": [sorted_durations[i] for i in idx],
            "arm": [arm_name] * len(idx),
            "dur_str": [f"{sorted_durations[i]:.1f} weeks" for i in idx],
            "status": ["Ongoing" if sort_idx[i] in ongoing_patients else "Completed/Progressed" for i in idx],
        }
    )
    renderer = p.hbar(
        y="y",
        right="right",
        left=0,
        height=0.65,
        color=arm_color,
        alpha=0.80,
        line_color=PAGE_BG,
        line_width=1.5,
        source=source,
    )
    if arm_name == "Arm A (Combo)":
        bars_a = renderer
    else:
        bars_b = renderer

# HoverTool for bars (Bokeh-specific interactivity)
bar_hover = HoverTool(
    renderers=[bars_a, bars_b],
    tooltips=[("Patient", "@y"), ("Treatment", "@arm"), ("Duration", "@dur_str"), ("Status", "@status")],
    point_policy="follow_mouse",
)
p.add_tools(bar_hover)

# Event marker config — Imprint palette with semantic alignment
# Partial response (positive): blue; Complete response (recovery): lime-green;
# Progressive disease (bad outcome): matte red; Adverse event (caution): amber
event_marker_config = {
    "partial_response": {
        "marker": "triangle",
        "color": IMPRINT_PALETTE[2],  # #4467A3 blue — cool positive
        "size": 20,
    },
    "complete_response": {
        "marker": "star",
        "color": IMPRINT_PALETTE[7],  # #99B314 lime-green — growth / recovery
        "size": 24,
    },
    "progressive_disease": {
        "marker": "diamond",
        "color": IMPRINT_PALETTE[4],  # #AE3030 matte red — bad / decline
        "size": 20,
    },
    "adverse_event": {
        "marker": "square",
        "color": ANYPLOT_AMBER,  # #DDCC77 amber — warning / caution
        "size": 17,
    },
}

event_renderers = {}
for etype, config in event_marker_config.items():
    mask = [j for j in range(len(events_type)) if events_type[j] == etype]
    if not mask:
        continue
    source_evt = ColumnDataSource(
        data={
            "x": [events_time[j] for j in mask],
            "y": [events_patient[j] for j in mask],
            "event": [events_label[j] for j in mask],
            "week": [f"Week {events_time[j]:.1f}" for j in mask],
        }
    )
    r = p.scatter(
        x="x",
        y="y",
        source=source_evt,
        marker=config["marker"],
        size=config["size"],
        color=config["color"],
        line_color=INK,
        line_width=1.5,
    )
    event_renderers[etype] = r

# HoverTool for event markers
evt_hover = HoverTool(
    renderers=list(event_renderers.values()),
    tooltips=[("Patient", "@y"), ("Event", "@event"), ("Time", "@week")],
    point_policy="snap_to_data",
)
p.add_tools(evt_hover)

# Ongoing indicators — right-pointing triangles at bar ends (more prominent)
ongoing_idx_sorted = [i for i in range(n_patients) if sort_idx[i] in ongoing_patients]
ongoing_r = None
if ongoing_idx_sorted:
    arrow_source = ColumnDataSource(
        data={
            "x": [sorted_durations[i] + 1.5 for i in ongoing_idx_sorted],
            "y": [sorted_patient_ids[i] for i in ongoing_idx_sorted],
        }
    )
    ongoing_r = p.scatter(
        x="x",
        y="y",
        source=arrow_source,
        marker="triangle",
        size=24,
        angle=3 * np.pi / 2,  # 270° CCW from up = pointing right
        color=INK_SOFT,
        line_color=INK,
        line_width=1.5,
    )

# Median duration reference line for visual storytelling
median_span = Span(
    location=median_duration,
    dimension="height",
    line_color=INK_MUTED,
    line_dash="dashed",
    line_width=2.0,
    line_alpha=0.65,
)
p.add_layout(median_span)

median_label = Label(
    x=median_duration,
    y=1560,
    y_units="screen",
    text=f"Median: {median_duration:.1f} wk",
    text_font_size="22pt",
    text_color=INK_MUTED,
    text_font_style="italic",
    x_offset=12,
)
p.add_layout(median_label)

# --- Theme-adaptive chrome ---
p.title.text_font_size = "50pt"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "28pt"
p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None

p.yaxis.axis_label = "Patient"
p.yaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_color = INK
p.yaxis.major_label_text_font_size = "24pt"  # smaller to avoid crowding 25 labels
p.yaxis.major_label_text_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.yaxis.minor_tick_line_color = None

p.x_range = Range1d(-0.5, max(sorted_durations) + 5)

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_dash = "solid"

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Legend
legend_items = [
    LegendItem(label="Arm A (Combo)", renderers=[bars_a]),
    LegendItem(label="Arm B (Mono)", renderers=[bars_b]),
]
for etype, label in [
    ("partial_response", "Partial Response"),
    ("complete_response", "Complete Response"),
    ("progressive_disease", "Progressive Disease"),
    ("adverse_event", "Adverse Event"),
]:
    if etype in event_renderers:
        legend_items.append(LegendItem(label=label, renderers=[event_renderers[etype]]))

if ongoing_r is not None:
    legend_items.append(LegendItem(label="Ongoing", renderers=[ongoing_r]))

legend = Legend(items=legend_items, location="center_right", orientation="vertical")
legend.label_text_font_size = "28pt"
legend.label_text_color = INK_SOFT
legend.glyph_height = 30
legend.glyph_width = 30
legend.spacing = 10
legend.padding = 20
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 0.92
legend.border_line_color = INK_SOFT
legend.border_line_width = 1
p.add_layout(legend)

# --- Save ---
# Interactive HTML artifact (catalog requirement)
save(p, filename=f"plot-{THEME}.html", resources=CDN, title="Swimmer Clinical Timeline")

# Static PNG via headless Chrome (Selenium — avoids broken chromedriver snap path)
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

# Chrome headless has ~139px of browser chrome overhead; resize so the viewport
# (window.innerHeight) is exactly H, not H minus that overhead.
vh = driver.execute_script("return window.innerHeight")
if vh != H:
    driver.set_window_size(W, H + (H - vh))

driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

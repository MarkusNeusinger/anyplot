""" anyplot.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: highcharts unknown | Python 3.13.13
Quality: 89/100 | Updated: 2026-06-08
"""

import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import BarSeries
from highcharts_core.options.series.scatter import ScatterSeries
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette system)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint categorical palette — 8 hues, theme-independent, hybrid-v3 sort
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — lognormal distribution for independent scenario vs sibling impls
np.random.seed(42)
n_patients = 25
patient_ids = [f"PT-{i + 1:03d}" for i in range(n_patients)]
arms = np.random.choice(["Arm A (Combo)", "Arm B (Mono)"], size=n_patients, p=[0.52, 0.48])
durations = np.round(np.clip(np.random.lognormal(mean=2.8, sigma=0.6, size=n_patients), 3, 48), 1)

sort_idx = np.argsort(durations)
patient_ids = [patient_ids[i] for i in sort_idx]
arms = arms[sort_idx]
durations = durations[sort_idx]

ongoing_mask = np.random.choice([True, False], size=n_patients, p=[0.28, 0.72])

events = []
for i in range(n_patients):
    dur = durations[i]
    patient_events = []
    if dur > 6 and np.random.random() < 0.65:
        pr_time = round(np.random.uniform(4, min(dur * 0.5, 16)), 1)
        patient_events.append({"time": pr_time, "type": "partial_response"})
        if dur > 14 and np.random.random() < 0.4:
            cr_time = round(np.random.uniform(pr_time + 4, min(dur * 0.8, 36)), 1)
            patient_events.append({"time": cr_time, "type": "complete_response"})
    if not ongoing_mask[i] and np.random.random() < 0.55:
        pd_time = round(dur * np.random.uniform(0.7, 0.95), 1)
        patient_events.append({"time": pd_time, "type": "progressive_disease"})
    if dur > 8 and np.random.random() < 0.3:
        ae_time = round(np.random.uniform(2, dur * 0.7), 1)
        patient_events.append({"time": ae_time, "type": "adverse_event"})
    events.append(patient_events)

n_responders = sum(1 for evts in events if any(e["type"] in ("partial_response", "complete_response") for e in evts))
n_cr = sum(1 for evts in events if any(e["type"] == "complete_response" for e in evts))
n_ongoing = int(ongoing_mask.sum())
median_dur = float(np.median(durations))
responder_patients = {
    i for i, evts in enumerate(events) if any(e["type"] in ("partial_response", "complete_response") for e in evts)
}

# Arm colors — Imprint palette positions 1 and 2; muted via rgba for non-responders
arm_solid = {
    "Arm A (Combo)": IMPRINT_PALETTE[0],  # #009E73 brand green
    "Arm B (Mono)": IMPRINT_PALETTE[1],  # #C475FD lavender
}
arm_muted_rgba = {"Arm A (Combo)": "rgba(0,158,115,0.38)", "Arm B (Mono)": "rgba(196,117,253,0.38)"}

# Event styling — Imprint palette positions 3-6; matte red for progression (semantic: bad)
event_colors = {
    "partial_response": IMPRINT_PALETTE[2],  # #4467A3 blue
    "complete_response": IMPRINT_PALETTE[3],  # #BD8233 ochre
    "progressive_disease": IMPRINT_PALETTE[4],  # #AE3030 matte red (semantic: bad)
    "adverse_event": IMPRINT_PALETTE[5],  # #2ABCCD cyan
}
event_markers = {
    "partial_response": "triangle",
    "complete_response": "diamond",
    "progressive_disease": "triangle-down",
    "adverse_event": "square",
}
event_labels = {
    "partial_response": "Partial Response",
    "complete_response": "Complete Response",
    "progressive_disease": "Progressive Disease",
    "adverse_event": "Adverse Event",
}

# Title — 60 chars < 67 baseline, use standard 66px
title = "swimmer-clinical-timeline · python · highcharts · anyplot.ai"
n_chars = len(title)
title_px = round(66 * min(1.0, 67 / n_chars))

# Chart
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "bar",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"fontFamily": "Helvetica, Arial, sans-serif", "color": INK},
    "marginLeft": 130,
    "marginRight": 280,
    "marginBottom": 130,
    "marginTop": 130,
}

chart.options.title = {
    "text": title,
    "style": {"fontSize": f"{title_px}px", "fontWeight": "600", "color": INK},
    "margin": 16,
}

chart.options.subtitle = {
    "text": (
        f"Phase II Oncology Trial — {n_responders}/{n_patients} responded "
        f"({n_cr} CR), {n_ongoing} ongoing at cutoff, median {median_dur:.0f} wks"
    ),
    "style": {"fontSize": "34px", "color": INK_SOFT},
}

chart.options.x_axis = {
    "categories": patient_ids,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "28px", "color": INK_SOFT}},
    "lineWidth": 0,
    "tickWidth": 0,
    "gridLineWidth": 0,
}

chart.options.y_axis = {
    "title": {"text": "Time on Study (Weeks)", "style": {"fontSize": "44px", "color": INK}, "margin": 20},
    "labels": {"style": {"fontSize": "34px", "color": INK_SOFT}},
    "gridLineWidth": 1,
    "gridLineColor": GRID,
    "min": 0,
    "max": round(float(max(durations)) * 1.06),
    "endOnTick": False,
    "lineWidth": 0,
    "plotLines": [
        {
            "value": 24,
            "color": INK_MUTED,
            "width": 2,
            "dashStyle": "LongDash",
            "label": {
                "text": "24-Week Milestone",
                "style": {"fontSize": "28px", "color": INK_MUTED, "fontWeight": "500"},
                "align": "right",
                "x": -10,
                "y": -10,
            },
            "zIndex": 3,
        },
        {
            "value": median_dur,
            "color": INK_MUTED,
            "width": 1,
            "dashStyle": "ShortDot",
            "label": {
                "text": f"Median {median_dur:.0f} wks",
                "style": {"fontSize": "26px", "color": INK_MUTED, "fontWeight": "400"},
                "align": "left",
                "x": 8,
                "y": -8,
            },
            "zIndex": 3,
        },
    ],
}

chart.options.legend = {
    "enabled": True,
    "align": "right",
    "verticalAlign": "top",
    "layout": "vertical",
    "x": -16,
    "y": 90,
    "floating": True,
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 1,
    "borderColor": INK_SOFT,
    "borderRadius": 6,
    "itemStyle": {"fontSize": "30px", "fontWeight": "400", "color": INK_SOFT},
    "padding": 16,
    "symbolRadius": 4,
    "itemMarginBottom": 6,
}

chart.options.plot_options = {
    "bar": {"pointPadding": 0.05, "groupPadding": 0.05, "borderWidth": 0, "pointWidth": 22},
    "scatter": {"jitter": {"x": 0, "y": 0}},
    "series": {"animation": False},
}

chart.options.tooltip = {
    "headerFormat": '<span style="font-size:26px;font-weight:bold">{point.key}</span><br/>',
    "style": {"fontSize": "26px"},
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 6,
    "borderWidth": 1,
}

chart.options.credits = {"enabled": False}

# Duration bars — per-point color by arm; muted rgba for non-responders preserves readability
bar_data = []
for i in range(n_patients):
    is_responder = i in responder_patients
    arm = arms[i]
    color = arm_solid[arm] if is_responder else arm_muted_rgba[arm]
    bar_data.append({"y": float(durations[i]), "color": color, "borderRadius": 2})

bar_series = BarSeries()
bar_series.data = bar_data
bar_series.name = "Duration"
bar_series.show_in_legend = False
chart.add_series(bar_series)

# Arm legend entries (invisible scatter series for legend symbols)
for arm_name, arm_color in arm_solid.items():
    arm_legend = ScatterSeries()
    arm_legend.data = []
    arm_legend.name = arm_name
    arm_legend.color = arm_color
    arm_legend.marker = {"symbol": "square", "radius": 10, "fillColor": arm_color}
    arm_legend.show_in_legend = True
    chart.add_series(arm_legend)

# Ongoing markers (triangle at bar endpoint for patients still on treatment)
ongoing_data = []
for i in range(n_patients):
    if ongoing_mask[i]:
        ongoing_data.append({"x": i, "y": float(durations[i])})

if ongoing_data:
    ongoing_series = ScatterSeries()
    ongoing_series.data = ongoing_data
    ongoing_series.name = "Ongoing (at cutoff)"
    ongoing_series.color = INK
    ongoing_series.marker = {
        "symbol": "triangle",
        "radius": 11,
        "fillColor": INK,
        "lineColor": PAGE_BG,
        "lineWidth": 2,
        "enabled": True,
    }
    ongoing_series.z_index = 5
    ongoing_series.show_in_legend = True
    chart.add_series(ongoing_series)

# Clinical event scatter series — each type gets distinct Imprint color + marker shape
for etype in event_colors:
    etype_data = []
    for i in range(n_patients):
        for ev in events[i]:
            if ev["type"] == etype:
                etype_data.append({"x": i, "y": float(ev["time"])})
    if etype_data:
        ev_series = ScatterSeries()
        ev_series.data = etype_data
        ev_series.name = event_labels[etype]
        ev_series.color = event_colors[etype]
        ev_series.marker = {
            "symbol": event_markers[etype],
            "radius": 11,
            "fillColor": event_colors[etype],
            "lineColor": PAGE_BG,
            "lineWidth": 2,
        }
        ev_series.z_index = 5
        ev_series.show_in_legend = True
        chart.add_series(ev_series)

# Load Highcharts JS — CDN with required Referer header
hc_js_url = "https://code.highcharts.com/highcharts.js"
hc_req = urllib.request.Request(hc_js_url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://highcharts.com/"})
with urllib.request.urlopen(hc_req, timeout=30) as r:
    highcharts_js = r.read().decode("utf-8")

html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and screenshot for PNG artifact
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
# CDP override is authoritative — --window-size alone doesn't prevent Chrome from eating ~139 px
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

# Pin to exact canvas dimensions — safety net for ±1-2 px rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")

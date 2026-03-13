""" pyplots.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: highcharts unknown | Python 3.14.3
Quality: 78/100 | Created: 2026-03-13
"""

import json
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data
np.random.seed(42)

n_patients = 25
patient_ids = [f"PT-{i + 1:03d}" for i in range(n_patients)]
arms = np.random.choice(["Arm A (Combo)", "Arm B (Mono)"], size=n_patients, p=[0.52, 0.48])
durations = np.round(np.random.exponential(scale=18, size=n_patients) + 4, 1)
durations = np.clip(durations, 3, 52)

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

# Colors
arm_a_color = "#306998"
arm_b_color = "#E8855E"
event_colors = {
    "partial_response": "#2CA02C",
    "complete_response": "#FFD700",
    "progressive_disease": "#D62728",
    "adverse_event": "#9467BD",
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

# Single bar series with per-point color by arm
bar_data = []
for i in range(n_patients):
    color = arm_a_color if arms[i] == "Arm A (Combo)" else arm_b_color
    bar_data.append({"y": float(durations[i]), "color": color})

# Ongoing markers at bar endpoints
ongoing_data = []
for i in range(n_patients):
    if ongoing_mask[i]:
        ongoing_data.append({"x": i, "y": float(durations[i])})

# Event scatter data
event_series_data = {etype: [] for etype in event_colors}
for i in range(n_patients):
    for ev in events[i]:
        event_series_data[ev["type"]].append({"x": i, "y": float(ev["time"])})

# Build series list
all_series = [{"type": "bar", "name": "Duration", "data": bar_data, "showInLegend": False, "borderRadius": 0}]

# Invisible scatter series for arm legend entries (avoids bar grouping)
all_series.append(
    {
        "type": "scatter",
        "name": "Arm A (Combo)",
        "color": arm_a_color,
        "marker": {"symbol": "square", "radius": 10, "fillColor": arm_a_color},
        "data": [],
        "showInLegend": True,
    }
)
all_series.append(
    {
        "type": "scatter",
        "name": "Arm B (Mono)",
        "color": arm_b_color,
        "marker": {"symbol": "square", "radius": 10, "fillColor": arm_b_color},
        "data": [],
        "showInLegend": True,
    }
)

if ongoing_data:
    all_series.append(
        {
            "type": "scatter",
            "name": "Ongoing",
            "color": "#333333",
            "marker": {"symbol": "triangle", "radius": 12, "fillColor": "#333333"},
            "data": ongoing_data,
            "showInLegend": True,
        }
    )

for etype, etype_data in event_series_data.items():
    if etype_data:
        all_series.append(
            {
                "type": "scatter",
                "name": event_labels[etype],
                "color": event_colors[etype],
                "marker": {
                    "symbol": event_markers[etype],
                    "radius": 14,
                    "fillColor": event_colors[etype],
                    "lineColor": "#ffffff",
                    "lineWidth": 2,
                },
                "data": etype_data,
                "showInLegend": True,
            }
        )

# Chart options
title_text = "swimmer-clinical-timeline \u00b7 highcharts \u00b7 pyplots.ai"

options_dict = {
    "chart": {
        "type": "bar",
        "width": 4800,
        "height": 2700,
        "backgroundColor": "#ffffff",
        "marginLeft": 180,
        "marginRight": 300,
        "marginBottom": 80,
        "marginTop": 70,
        "spacingTop": 5,
        "spacingBottom": 5,
    },
    "title": {
        "text": title_text,
        "style": {"fontSize": "28px", "fontWeight": "500", "color": "#333333"},
        "align": "center",
    },
    "xAxis": {
        "categories": patient_ids,
        "title": {"text": None},
        "labels": {"style": {"fontSize": "18px", "color": "#333333"}},
        "lineWidth": 0,
        "tickWidth": 0,
        "gridLineWidth": 0,
    },
    "yAxis": {
        "title": {"text": "Time on Study (Weeks)", "style": {"fontSize": "22px", "color": "#333333"}},
        "labels": {"style": {"fontSize": "18px", "color": "#555555"}},
        "gridLineWidth": 1,
        "gridLineColor": "rgba(0,0,0,0.08)",
        "min": 0,
        "lineWidth": 1,
        "lineColor": "#cccccc",
    },
    "legend": {
        "enabled": True,
        "itemStyle": {"fontSize": "20px", "fontWeight": "normal", "color": "#333333"},
        "symbolRadius": 2,
        "align": "right",
        "verticalAlign": "top",
        "layout": "vertical",
        "x": -20,
        "y": 60,
        "itemMarginBottom": 8,
    },
    "plotOptions": {
        "bar": {"pointPadding": 0.02, "groupPadding": 0.05, "borderWidth": 0, "pointWidth": 24},
        "scatter": {"jitter": {"x": 0, "y": 0}},
        "series": {"animation": False},
    },
    "tooltip": {"enabled": False},
    "credits": {"enabled": False},
    "series": all_series,
}

js_options = json.dumps(options_dict)

# Load Highcharts JS from npm package
hc_js_path = Path(__file__).resolve().parents[3] / "node_modules" / "highcharts" / "highcharts.js"
if not hc_js_path.exists():
    subprocess.run(["npm", "install", "highcharts"], cwd=str(hc_js_path.parents[2]), check=True, capture_output=True)
highcharts_js = hc_js_path.read_text(encoding="utf-8")

# Generate HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
        Highcharts.chart('container', {js_options});
    </script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save HTML
Path("plot.html").write_text(html_content, encoding="utf-8")

# Screenshot with Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

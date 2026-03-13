""" pyplots.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: highcharts unknown | Python 3.14.3
Quality: 90/100 | Created: 2026-03-13
"""

import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import BarSeries
from highcharts_core.options.series.scatter import ScatterSeries
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

# Compute storytelling stats
n_responders = sum(1 for evts in events if any(e["type"] in ("partial_response", "complete_response") for e in evts))
n_cr = sum(1 for evts in events if any(e["type"] == "complete_response" for e in evts))
n_ongoing = int(ongoing_mask.sum())
median_dur = float(np.median(durations))
responder_patients = {
    i for i, evts in enumerate(events) if any(e["type"] in ("partial_response", "complete_response") for e in evts)
}

# Colorblind-safe palette (Okabe-Ito inspired)
arm_a_color = "#306998"
arm_b_color = "#E8855E"
arm_a_muted = "#5a8db8"
arm_b_muted = "#e8a98e"
event_colors = {
    "partial_response": "#0072B2",
    "complete_response": "#F0E442",
    "progressive_disease": "#D55E00",
    "adverse_event": "#9467BD",
}
event_markers = {
    "partial_response": "circle",
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

# Create chart with typed highcharts-core API
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "bar",
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#fafbfc",
    "style": {"fontFamily": "'Segoe UI', Helvetica, Arial, sans-serif"},
    "marginLeft": 200,
    "marginRight": 280,
    "marginBottom": 160,
    "marginTop": 140,
}

chart.options.title = {
    "text": "swimmer-clinical-timeline \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "52px", "fontWeight": "600", "color": "#2c3e50", "letterSpacing": "1px"},
    "margin": 10,
}

chart.options.subtitle = {
    "text": (
        f"Phase II Oncology Trial \u2014 {n_responders}/{n_patients} patients responded "
        f"({n_cr} CR), {n_ongoing} ongoing at data cutoff, median duration {median_dur:.0f} wks"
    ),
    "style": {"fontSize": "32px", "color": "#5a6c7d", "fontWeight": "400"},
}

chart.options.x_axis = {
    "categories": patient_ids,
    "title": {"text": None},
    "labels": {"style": {"fontSize": "22px", "color": "#34495e", "fontWeight": "500"}},
    "lineWidth": 0,
    "tickWidth": 0,
    "gridLineWidth": 0,
}

chart.options.y_axis = {
    "title": {
        "text": "Time on Study (Weeks)",
        "style": {"fontSize": "36px", "color": "#34495e", "fontWeight": "500"},
        "margin": 20,
    },
    "labels": {"style": {"fontSize": "26px", "color": "#7f8c8d"}},
    "gridLineWidth": 1,
    "gridLineColor": "rgba(0, 0, 0, 0.06)",
    "gridLineDashStyle": "Dot",
    "min": 0,
    "lineWidth": 0,
    "plotLines": [
        {
            "value": 24,
            "color": "rgba(44, 62, 80, 0.35)",
            "width": 3,
            "dashStyle": "LongDash",
            "label": {
                "text": "24-Week Milestone",
                "style": {"fontSize": "24px", "color": "rgba(44, 62, 80, 0.6)", "fontWeight": "500"},
                "align": "right",
                "x": -12,
                "y": -8,
            },
            "zIndex": 3,
        },
        {
            "value": median_dur,
            "color": "rgba(39, 174, 96, 0.4)",
            "width": 2,
            "dashStyle": "ShortDot",
            "label": {
                "text": f"Median {median_dur:.0f} wks",
                "style": {"fontSize": "22px", "color": "rgba(39, 174, 96, 0.7)", "fontWeight": "500"},
                "align": "left",
                "x": 8,
                "y": -6,
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
    "y": 60,
    "floating": True,
    "backgroundColor": "rgba(255, 255, 255, 0.94)",
    "borderWidth": 1,
    "borderColor": "#dce1e6",
    "borderRadius": 10,
    "itemStyle": {"fontSize": "24px", "fontWeight": "400", "color": "#34495e"},
    "padding": 18,
    "symbolRadius": 4,
    "itemMarginBottom": 5,
    "shadow": {"color": "rgba(0,0,0,0.04)", "offsetX": 1, "offsetY": 2, "width": 6},
}

chart.options.plot_options = {
    "bar": {"pointPadding": 0.02, "groupPadding": 0.05, "borderWidth": 0, "pointWidth": 28},
    "scatter": {"jitter": {"x": 0, "y": 0}},
    "series": {"animation": False},
}

chart.options.tooltip = {
    "headerFormat": '<span style="font-size:22px;font-weight:bold">{point.key}</span><br/>',
    "style": {"fontSize": "22px"},
    "backgroundColor": "rgba(255, 255, 255, 0.95)",
    "borderRadius": 8,
    "borderWidth": 1,
    "shadow": {"color": "rgba(0,0,0,0.1)", "offsetX": 2, "offsetY": 2, "width": 4},
}

chart.options.credits = {"enabled": False}

# Duration bars — per-point color by treatment arm, muted for non-responders
bar_data = []
for i in range(n_patients):
    is_responder = i in responder_patients
    if arms[i] == "Arm A (Combo)":
        color = arm_a_color if is_responder else arm_a_muted
    else:
        color = arm_b_color if is_responder else arm_b_muted
    bar_data.append({"y": float(durations[i]), "color": color, "borderRadius": 3})

bar_series = BarSeries()
bar_series.data = bar_data
bar_series.name = "Duration"
bar_series.show_in_legend = False
chart.add_series(bar_series)

# Invisible scatter series for arm legend entries
for arm_name, arm_color in [("Arm A (Combo)", arm_a_color), ("Arm B (Mono)", arm_b_color)]:
    arm_legend = ScatterSeries()
    arm_legend.data = []
    arm_legend.name = arm_name
    arm_legend.color = arm_color
    arm_legend.marker = {"symbol": "square", "radius": 12, "fillColor": arm_color}
    arm_legend.show_in_legend = True
    chart.add_series(arm_legend)

# Ongoing markers at bar endpoints — use right-pointing arrow (url marker)
ongoing_data = []
for i in range(n_patients):
    if ongoing_mask[i]:
        ongoing_data.append({"x": i, "y": float(durations[i])})

if ongoing_data:
    ongoing_series = ScatterSeries()
    ongoing_series.data = ongoing_data
    ongoing_series.name = "Ongoing"
    ongoing_series.color = "#2c3e50"
    ongoing_series.marker = {
        "symbol": "triangle",
        "radius": 14,
        "fillColor": "#2c3e50",
        "lineColor": "#ffffff",
        "lineWidth": 2,
        "enabled": True,
    }
    ongoing_series.z_index = 5
    ongoing_series.show_in_legend = True
    chart.add_series(ongoing_series)

# Event scatter series — each event type gets its own distinct marker shape
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
            "radius": 14,
            "fillColor": event_colors[etype],
            "lineColor": "#ffffff",
            "lineWidth": 3,
        }
        ev_series.z_index = 5
        ev_series.show_in_legend = True
        chart.add_series(ev_series)

# Load Highcharts JS from npm package
hc_js_path = Path(__file__).resolve().parents[3] / "node_modules" / "highcharts" / "highcharts.js"
if not hc_js_path.exists():
    subprocess.run(["npm", "install", "highcharts"], cwd=str(hc_js_path.parents[2]), check=True, capture_output=True)
highcharts_js = hc_js_path.read_text(encoding="utf-8")

# Generate HTML with inline scripts via typed API
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

# Save interactive HTML
Path("plot.html").write_text(
    f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script src="https://code.highcharts.com/highcharts.js"></script>
</head>
<body style="margin:0; background:#fafbfc;">
    <div id="container" style="width: 100%; height: 100vh;"></div>
    <script>{html_str}</script>
</body>
</html>""",
    encoding="utf-8",
)

# Screenshot with Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)

container = driver.find_element("id", "container")
container.screenshot("plot.png")
driver.quit()

Path(temp_path).unlink()

""" anyplot.ai
network-bipartite: Bipartite Network Graph
Library: highcharts unknown | Python 3.13.13
Quality: 82/100 | Created: 2026-05-14
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

COLOR_A = "#009E73"  # Students — Okabe-Ito position 1
COLOR_B = "#4467A3"  # Courses — Okabe-Ito position 3
EDGE_COLOR = "rgba(74,74,68,0.22)" if THEME == "light" else "rgba(184,183,176,0.25)"

# Data — student course enrollment network
np.random.seed(42)

students = ["Alice", "Bob", "Carlos", "Diana", "Emma", "Frank", "Grace", "Henry", "Iris", "James", "Karen", "Liam"]
courses = [
    "Data Science",
    "Machine Learning",
    "Statistics",
    "Linear Algebra",
    "Python Programming",
    "Databases",
    "Algorithms",
    "Computer Vision",
]

# Build enrollment edges (each student takes 2–4 courses)
edge_list = []
for student in students:
    n_enroll = np.random.randint(2, 5)
    enrolled = np.random.choice(len(courses), size=n_enroll, replace=False)
    for j in enrolled:
        edge_list.append((student, courses[j]))

# Compute node degrees
student_degree = {s: sum(1 for e in edge_list if e[0] == s) for s in students}
course_degree = {c: sum(1 for e in edge_list if e[1] == c) for c in courses}

# Y-positions — both columns span the same [0, y_max] range
n_s = len(students)
n_c = len(courses)
y_max = max(n_s, n_c) - 1  # 11

student_y = {s: i * y_max / (n_s - 1) for i, s in enumerate(students)}
course_y = {c: i * y_max / (n_c - 1) for i, c in enumerate(courses)}

# Node datasets
student_nodes = [
    {
        "x": 0.0,
        "y": round(student_y[s], 4),
        "name": s,
        "marker": {"radius": 28 + student_degree[s] * 9, "fillColor": COLOR_A, "lineColor": PAGE_BG, "lineWidth": 3},
    }
    for s in students
]

course_nodes = [
    {
        "x": 2.0,
        "y": round(course_y[c], 4),
        "name": c,
        "marker": {"radius": 28 + course_degree[c] * 9, "fillColor": COLOR_B, "lineColor": PAGE_BG, "lineWidth": 3},
    }
    for c in courses
]

# Edge data — null separators create disconnected line segments
edge_data = []
for student, course in edge_list:
    edge_data.append({"x": 0.0, "y": round(student_y[student], 4)})
    edge_data.append({"x": 2.0, "y": round(course_y[course], 4)})
    edge_data.append(None)

# Highcharts configuration
chart_options = {
    "chart": {
        "backgroundColor": PAGE_BG,
        "width": 4800,
        "height": 2700,
        "marginLeft": 350,
        "marginRight": 500,
        "marginTop": 200,
        "marginBottom": 160,
        "style": {"fontFamily": "'Helvetica Neue', Arial, sans-serif"},
    },
    "title": {
        "text": "Student Course Enrollment · network-bipartite · highcharts · anyplot.ai",
        "style": {"fontSize": "28px", "color": INK, "fontWeight": "600"},
        "margin": 40,
    },
    "subtitle": {
        "text": "Node size encodes number of connections — Students (left) · Courses (right)",
        "style": {"fontSize": "20px", "color": INK_SOFT},
    },
    "xAxis": {"visible": False, "min": -0.4, "max": 2.4, "startOnTick": False, "endOnTick": False},
    "yAxis": {"visible": False, "min": -0.8, "max": y_max + 0.8, "startOnTick": False, "endOnTick": False},
    "tooltip": {
        "headerFormat": "",
        "pointFormat": "<span style='font-size:18px'><b>{point.name}</b></span>",
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "style": {"color": INK},
    },
    "legend": {
        "enabled": True,
        "align": "center",
        "verticalAlign": "bottom",
        "itemStyle": {"fontSize": "22px", "color": INK_SOFT, "fontWeight": "normal"},
        "symbolRadius": 8,
        "backgroundColor": ELEVATED_BG,
        "borderColor": INK_SOFT,
        "borderWidth": 1,
        "borderRadius": 4,
        "padding": 20,
        "itemMarginTop": 8,
        "itemMarginBottom": 8,
    },
    "plotOptions": {
        "line": {
            "enableMouseTracking": False,
            "marker": {"enabled": False},
            "lineWidth": 2,
            "connectNulls": False,
            "states": {"hover": {"enabled": False}},
        },
        "scatter": {"enableMouseTracking": True},
    },
    "series": [
        # Edges drawn as a single disconnected line series
        {
            "type": "line",
            "name": "Enrollments",
            "data": edge_data,
            "color": EDGE_COLOR,
            "lineWidth": 2,
            "connectNulls": False,
            "marker": {"enabled": False},
            "enableMouseTracking": False,
            "showInLegend": False,
        },
        # Student nodes (left column)
        {
            "type": "scatter",
            "name": "Students",
            "color": COLOR_A,
            "data": student_nodes,
            "marker": {"symbol": "circle"},
            "dataLabels": {
                "enabled": True,
                "format": "{point.name}",
                "x": -110,
                "y": 0,
                "align": "right",
                "verticalAlign": "middle",
                "allowOverlap": True,
                "overflow": "allow",
                "crop": False,
                "style": {"fontSize": "22px", "color": INK_SOFT, "fontWeight": "normal", "textOutline": "none"},
            },
        },
        # Course nodes (right column)
        {
            "type": "scatter",
            "name": "Courses",
            "color": COLOR_B,
            "data": course_nodes,
            "marker": {"symbol": "circle"},
            "dataLabels": {
                "enabled": True,
                "format": "{point.name}",
                "x": 110,
                "y": 0,
                "align": "left",
                "verticalAlign": "middle",
                "allowOverlap": True,
                "overflow": "allow",
                "crop": False,
                "style": {"fontSize": "22px", "color": INK_SOFT, "fontWeight": "normal", "textOutline": "none"},
            },
        },
    ],
    "credits": {"enabled": False},
}

# Download Highcharts JS from jsDelivr (required for headless Chrome — no CDN links)
highcharts_url = "https://cdn.jsdelivr.net/npm/highcharts@latest/highcharts.js"
req = urllib.request.Request(
    highcharts_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)
with urllib.request.urlopen(req, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

chart_json = json.dumps(chart_options)

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>
    Highcharts.chart('container', {chart_json});
    </script>
</body>
</html>"""

# Save HTML artifact
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2700")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()

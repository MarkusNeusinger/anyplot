"""pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: highcharts unknown | Python 3.14.3
Quality: 85/100 | Created: 2026-03-14
"""

import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


np.random.seed(42)

# Data - Simulated CPU profiling data with nested function call hierarchies
stacks = {
    "main": {
        "process_request": {
            "parse_headers": {"decode_utf8": 45, "validate_fields": 32},
            "authenticate": {"load_session": 28, "verify_token": {"hash_compare": 65, "check_expiry": 18}},
            "handle_route": {
                "query_database": {
                    "connect_pool": 22,
                    "execute_sql": {"build_query": 38, "fetch_rows": 95, "parse_result": 42},
                },
                "render_template": {"load_cache": 30, "compile_template": 58, "serialize_json": 48},
                "apply_middleware": {"compress_gzip": 35, "set_cors_headers": 12},
            },
        },
        "log_metrics": {"format_entry": 15, "write_buffer": 25, "flush_async": 20},
        "gc_collect": 40,
    }
}

# Calculate total samples iteratively (flat, no helper functions)
total_samples = 0
size_stack = [stacks]
while size_stack:
    node = size_stack.pop()
    if isinstance(node, (int, float)):
        total_samples += node
    elif isinstance(node, dict):
        size_stack.extend(node.values())

# Build flame rectangles iteratively as columnrange data points
# Each bar: depth level (x), start position (low), end position (high)
rectangles = []
traverse = [(stacks, 0, 0)]  # (node, depth, x_start)

while traverse:
    node, depth, x_start = traverse.pop()
    if not isinstance(node, dict):
        continue
    current_x = x_start
    for name, child in node.items():
        child_size = 0
        sq = [child]
        while sq:
            item = sq.pop()
            if isinstance(item, (int, float)):
                child_size += item
            elif isinstance(item, dict):
                sq.extend(item.values())
        if child_size > 0:
            rectangles.append(
                {
                    "x": depth,
                    "low": current_x,
                    "high": current_x + child_size,
                    "name": name,
                    "samples": child_size,
                    "pct": round(child_size / total_samples * 100, 1),
                }
            )
            if isinstance(child, dict):
                traverse.append((child, depth + 1, current_x))
        current_x += child_size

# Warm color palette (yellows, oranges, reds) - conventional flame graph aesthetic
flame_colors = [
    "#E25822",  # deep orange-red
    "#F4C430",  # golden yellow
    "#CC3300",  # dark red
    "#F0A30A",  # amber
    "#D4602E",  # burnt orange
    "#FFD700",  # bright gold
    "#B8301C",  # crimson
    "#E8963A",  # tangerine
    "#F5D060",  # light yellow
    "#C04820",  # brick red
    "#F0BE50",  # warm yellow
    "#DA4500",  # vermillion
    "#E8751A",  # orange
    "#F7E070",  # pale yellow
    "#A83210",  # deep red
]
for i, rect in enumerate(rectangles):
    rect["color"] = flame_colors[(i * 3 + rect["x"] * 7) % len(flame_colors)]

# Flip depth so root (depth 0) is at the bottom — flame graph orientation
max_depth = max(r["x"] for r in rectangles)
for r in rectangles:
    r["x"] = max_depth - r["x"]

# Build chart using highcharts-core Python API with columnrange series
chart = Chart(container="container")
chart.options = HighchartsOptions()
chart.options.chart = {
    "type": "columnrange",
    "inverted": True,
    "width": 4800,
    "height": 2700,
    "backgroundColor": "#ffffff",
    "marginLeft": 160,
    "marginRight": 40,
    "marginTop": 150,
    "marginBottom": 50,
}
chart.options.title = {
    "text": "flamegraph-basic \u00b7 highcharts \u00b7 pyplots.ai",
    "style": {"fontSize": "48px", "fontWeight": "bold", "color": "#333333"},
}
chart.options.subtitle = {
    "text": f"CPU Profile \u2014 Web Server Request Handling ({int(total_samples)} samples)",
    "style": {"fontSize": "32px", "color": "#666666"},
}

# Value axis (horizontal in inverted chart) - represents sample counts
chart.options.y_axis = {"visible": False, "min": 0, "max": total_samples}

# Category axis (vertical in inverted chart) - represents stack depth
chart.options.x_axis = {
    "categories": [str(i) for i in range(max_depth + 1)],
    "title": {"text": "Stack Depth", "style": {"fontSize": "32px", "color": "#555555"}},
    "labels": {"enabled": False},
}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.tooltip = {"headerFormat": "", "pointFormat": "<b>{point.name}</b>", "style": {"fontSize": "24px"}}

chart.options.plot_options = {
    "columnrange": {
        "grouping": False,
        "borderWidth": 2,
        "borderColor": "#ffffff",
        "pointPadding": 0,
        "groupPadding": 0,
        "borderRadius": 1,
    }
}

# Create series data with pre-computed labels per point
# Estimate bar pixel width: chart plot area ~4600px maps to total_samples
px_per_sample = 4600 / total_samples
char_width_px = 18  # approximate character width at 28px monospace

series_data = []
for r in rectangles:
    bar_width_px = (r["high"] - r["low"]) * px_per_sample
    max_chars = int((bar_width_px - 20) / char_width_px)

    # Determine label text based on available space
    full_label = f"{r['name']} ({r['pct']}%)"
    if max_chars >= len(full_label):
        label_text = full_label
    elif max_chars >= len(r["name"]):
        label_text = r["name"]
    elif max_chars >= 4:
        label_text = r["name"][: max_chars - 1] + "\u2026"
    else:
        label_text = None

    point = {"x": r["x"], "low": r["low"], "high": r["high"], "color": r["color"], "name": r["name"]}
    if label_text:
        point["dataLabels"] = {
            "enabled": True,
            "inside": True,
            "crop": True,
            "align": "left",
            "verticalAlign": "middle",
            "x": 10,
            "format": label_text,
            "style": {
                "fontSize": "28px",
                "fontWeight": "normal",
                "fontFamily": '"SF Mono", "Consolas", "Monaco", monospace',
                "color": "#ffffff",
                "textOutline": "2px rgba(0,0,0,0.4)",
            },
        }
    series_data.append(point)

chart.options.series = [{"type": "columnrange", "data": series_data, "name": "Call Stack"}]

# Download Highcharts JS and highcharts-more (required for columnrange)
highcharts_js = None
for url in ["https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"]:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
            break
    except Exception:
        continue
if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS")

highcharts_more_js = None
for url in [
    "https://code.highcharts.com/highcharts-more.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js",
]:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            highcharts_more_js = response.read().decode("utf-8")
            break
    except Exception:
        continue
if highcharts_more_js is None:
    raise RuntimeError("Failed to download Highcharts More JS")

# Generate HTML with inline scripts (required for headless Chrome)
html_str = chart.to_js_literal()
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{html_str}</script>
</body>
</html>"""

# Save interactive HTML version
with open("plot.html", "w", encoding="utf-8") as f:
    f.write(
        f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>flamegraph-basic \u00b7 highcharts \u00b7 pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
    <style>
        body {{ margin: 0; padding: 20px; font-family: sans-serif; background: #fff; }}
        #container {{ width: 100%; height: 90vh; min-height: 600px; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <script>{html_str}</script>
</body>
</html>"""
    )

# Take screenshot with Selenium
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=4800,2900")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()
Path(temp_path).unlink()

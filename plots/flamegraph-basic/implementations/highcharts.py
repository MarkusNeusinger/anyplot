"""pyplots.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: highcharts | Python 3.13
Quality: pending | Created: 2026-03-14
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - Simulated CPU profiling data with nested function call hierarchies
np.random.seed(42)

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


def calc_size(node):
    if isinstance(node, (int, float)):
        return node
    return sum(calc_size(v) for v in node.values())


def build_flame_rects(node, x, base_y, width, level, rects, level_height, total_root):
    if isinstance(node, (int, float)):
        return

    total = calc_size(node)
    if total == 0:
        return

    current_x = x
    for name, child in node.items():
        child_size = calc_size(child)
        child_width = (child_size / total) * width if total > 0 else 0

        if child_width > 0:
            # Flame graph: stack grows upward, so y decreases with level
            y = base_y - level * level_height
            rects.append(
                {
                    "name": name,
                    "x": current_x,
                    "y": y,
                    "width": child_width,
                    "height": level_height,
                    "level": level,
                    "samples": child_size,
                    "pct": round(child_size / total_root * 100, 1),
                }
            )

            if not isinstance(child, (int, float)):
                build_flame_rects(child, current_x, base_y, child_width, level + 1, rects, level_height, total_root)

        current_x += child_width


# Chart layout
chart_x = 120
base_y = 2300  # Bottom of flame graph (root sits here)
chart_width = 4560
level_height = 320

total_samples = calc_size(stacks)
rectangles = []
build_flame_rects(stacks, chart_x, base_y, chart_width, 0, rectangles, level_height, total_samples)

# Warm color palette (yellows, oranges, reds) - conventional flame graph aesthetic
flame_colors = [
    "#E25822",
    "#E8751A",
    "#F0A30A",
    "#F4C430",
    "#E8963A",
    "#D4602E",
    "#F0BE50",
    "#E07828",
    "#CC5500",
    "#F5D060",
    "#DA7028",
    "#E8A020",
    "#C04820",
    "#F0C844",
    "#D85818",
]


def get_flame_color(index):
    return flame_colors[index % len(flame_colors)]


# Assign colors with variation
for i, rect in enumerate(rectangles):
    rect["color"] = get_flame_color(i * 3 + rect["level"] * 7)

rects_json = json.dumps(rectangles)

# Highcharts renderer for custom flame graph
chart_config = f"""
(function() {{
    var rects = {rects_json};

    var chart = Highcharts.chart('container', {{
        chart: {{
            width: 4800,
            height: 2700,
            backgroundColor: '#ffffff',
            events: {{
                load: function() {{
                    var ren = this.renderer;

                    rects.forEach(function(r) {{
                        // Draw rectangle with warm flame colors
                        ren.rect(r.x, r.y, r.width - 2, r.height - 3, 1)
                            .attr({{
                                fill: r.color,
                                stroke: '#ffffff',
                                'stroke-width': 2,
                                zIndex: 1
                            }})
                            .add();

                        // Label inside bar if wide enough
                        var labelText = r.name + ' (' + r.pct + '%)';
                        var charWidth = 22;
                        var maxChars = Math.floor((r.width - 20) / charWidth);

                        if (maxChars >= 4) {{
                            if (labelText.length > maxChars) {{
                                // Try name only
                                labelText = r.name;
                                if (labelText.length > maxChars) {{
                                    labelText = labelText.substring(0, maxChars - 1) + '\u2026';
                                }}
                            }}

                            ren.text(labelText, r.x + 12, r.y + r.height / 2 + 12)
                                .attr({{
                                    zIndex: 2
                                }})
                                .css({{
                                    color: '#ffffff',
                                    fontSize: '32px',
                                    fontWeight: 'normal',
                                    fontFamily: '"SF Mono", "Consolas", "Monaco", monospace',
                                    textShadow: '1px 1px 2px rgba(0,0,0,0.4)'
                                }})
                                .add();
                        }}
                    }});

                    // Y-axis label for stack depth
                    ren.text('Stack Depth', 45, 1400)
                        .attr({{
                            rotation: -90,
                            zIndex: 3
                        }})
                        .css({{
                            color: '#555555',
                            fontSize: '36px',
                            fontWeight: 'normal',
                            textAnchor: 'middle'
                        }})
                        .add();
                }}
            }}
        }},
        title: {{
            text: 'flamegraph-basic \u00b7 highcharts \u00b7 pyplots.ai',
            style: {{
                fontSize: '52px',
                fontWeight: 'bold',
                color: '#333333'
            }},
            y: 55
        }},
        subtitle: {{
            text: 'CPU Profile \u2014 Web Server Request Handling ({int(total_samples)} samples)',
            style: {{
                fontSize: '34px',
                color: '#666666'
            }},
            y: 110
        }},
        credits: {{
            enabled: false
        }}
    }});
}})();
"""

# Download Highcharts JS
highcharts_urls = [
    "https://code.highcharts.com/highcharts.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js",
]
highcharts_js = None
for url in highcharts_urls:
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
            break
    except Exception:
        continue
if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS from all CDN sources")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:#ffffff;">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_config}</script>
</body>
</html>"""

# Save HTML for interactive version
with open("plot.html", "w", encoding="utf-8") as f:
    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>flamegraph-basic \u00b7 highcharts \u00b7 pyplots.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <style>
        body {{ margin: 0; padding: 20px; font-family: sans-serif; background: #ffffff; }}
        #container {{ width: 100%; height: 90vh; min-height: 600px; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <script>{chart_config}</script>
</body>
</html>"""
    f.write(standalone_html)

# Write temp HTML and take screenshot
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

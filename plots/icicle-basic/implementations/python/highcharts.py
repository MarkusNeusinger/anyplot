""" anyplot.ai
icicle-basic: Basic Icicle Chart
Library: highcharts unknown | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-13
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for main categories
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - File system hierarchy with folders and files
hierarchy = {
    "Project Files": {
        "src": {
            "components": {"Header.tsx": 95, "Footer.tsx": 55, "Sidebar.tsx": 110, "Modal.tsx": 78},
            "utils": {"helpers.ts": 42, "constants.ts": 28, "validators.ts": 65},
            "api": {"client.ts": 88, "endpoints.ts": 56, "types.ts": 34},
        },
        "docs": {"README.md": 45, "guide.md": 120, "api.md": 85},
        "tests": {"test_main.py": 65, "test_utils.py": 48, "test_api.py": 72},
        "assets": {
            "images": {"logo.png": 125, "banner.jpg": 280, "icons.svg": 45},
            "styles": {"main.css": 92, "theme.css": 68},
        },
    }
}

# Category colors from Okabe-Ito palette
cat_colors = {"src": IMPRINT[0], "docs": IMPRINT[1], "tests": IMPRINT[2], "assets": IMPRINT[3]}

# Flatten hierarchy into list of nodes with calculated sizes
all_nodes = []
queue = [("Project Files", hierarchy["Project Files"], 0, "")]

while queue:
    key, val, level, parent = queue.pop(0)

    if isinstance(val, (int, float)):
        all_nodes.append({"name": key, "value": val, "level": level, "parent": parent})
    else:
        # Calculate total size for this node (sum of all descendants)
        total_size = 0
        for _, v in val.items():
            if isinstance(v, (int, float)):
                total_size += v
            else:
                for _, subv in v.items():
                    if isinstance(subv, (int, float)):
                        total_size += subv
                    else:
                        for _, subsubv in subv.items():
                            if isinstance(subsubv, (int, float)):
                                total_size += subsubv

        all_nodes.append({"name": key, "value": total_size, "level": level, "parent": parent})

        # Queue children for processing
        for k, v in val.items():
            queue.append((k, v, level + 1, key))

# Group nodes by level and parent for positioning
level_groups = {}
for node in all_nodes:
    lv = node["level"]
    parent = node["parent"]
    if lv not in level_groups:
        level_groups[lv] = {}
    if parent not in level_groups[lv]:
        level_groups[lv][parent] = []
    level_groups[lv][parent].append(node)

# Layout rectangles in icicle grid
rectangles = []
max_level = max((n["level"] for n in all_nodes), default=0)
level_height = 2300 // (max_level + 1) if max_level > 0 else 500

for lv in sorted(level_groups.keys()):
    for parent, children in level_groups[lv].items():
        top_cat = parent if parent in cat_colors else "src"
        color = cat_colors.get(top_cat, IMPRINT[0])

        total_val = sum(c["value"] for c in children)
        x_pos = 200

        for child in children:
            width = (child["value"] / total_val) * 4400 if total_val > 0 else 0
            height = level_height
            y_pos = 300 + (lv * level_height)

            # Determine font size by level
            if lv == 0:
                font_sz = 48
            elif lv == 1:
                font_sz = 36
            elif lv == 2:
                font_sz = 28
            else:
                font_sz = 22

            # Label visibility based on rectangle size
            min_width = font_sz * max(2, len(child["name"]) // 2)
            show_lbl = width >= min_width and height >= font_sz + 8

            rectangles.append(
                {
                    "x": x_pos,
                    "y": y_pos,
                    "width": width,
                    "height": height,
                    "color": color,
                    "name": child["name"],
                    "value": child["value"],
                    "font_size": font_sz,
                    "show_label": show_lbl,
                    "level": lv,
                }
            )
            x_pos += width

# Generate JavaScript to render icicle chart with Highcharts
rects_json = json.dumps(rectangles)

chart_config = f"""
(function() {{
    var rects = {rects_json};
    var pageBackground = '{PAGE_BG}';
    var textColor = '{INK}';
    var textSoftColor = '{INK_SOFT}';

    var chart = Highcharts.chart('container', {{
        chart: {{
            width: 4800,
            height: 2700,
            backgroundColor: pageBackground,
            events: {{
                load: function() {{
                    var ren = this.renderer;

                    // Draw all rectangles and labels
                    rects.forEach(function(r) {{
                        ren.rect(r.x, r.y, r.width - 2, r.height - 2, 0)
                            .attr({{
                                fill: r.color,
                                stroke: pageBackground,
                                'stroke-width': 2,
                                zIndex: 1
                            }})
                            .add();

                        if (r.show_label) {{
                            var label = r.name;
                            if (r.level > 2) {{
                                label = label + ' (' + r.value + ' KB)';
                            }}

                            var maxChars = Math.max(3, Math.floor(r.width / (r.font_size * 0.45)));
                            if (label.length > maxChars) {{
                                label = label.substring(0, maxChars - 1) + '…';
                            }}

                            ren.text(label, r.x + r.width / 2, r.y + r.height / 2 + r.font_size / 3)
                                .attr({{
                                    zIndex: 2,
                                    textAnchor: 'middle'
                                }})
                                .css({{
                                    color: textColor,
                                    fontSize: r.font_size + 'px',
                                    fontWeight: r.level <= 1 ? 'bold' : 'normal'
                                }})
                                .add();
                        }}
                    }});

                    // Draw legend
                    var cats = [
                        {{ name: 'src', color: '{IMPRINT[0]}' }},
                        {{ name: 'docs', color: '{IMPRINT[1]}' }},
                        {{ name: 'tests', color: '{IMPRINT[2]}' }},
                        {{ name: 'assets', color: '{IMPRINT[3]}' }}
                    ];

                    var legendY = 2520;
                    var legendX = 1500;
                    var spacing = 700;

                    cats.forEach(function(cat, i) {{
                        ren.rect(legendX + i * spacing, legendY, 50, 50, 2)
                            .attr({{
                                fill: cat.color,
                                stroke: textSoftColor,
                                'stroke-width': 2,
                                zIndex: 3
                            }})
                            .add();

                        ren.text(cat.name, legendX + i * spacing + 70, legendY + 35)
                            .css({{
                                color: textColor,
                                fontSize: '24px'
                            }})
                            .attr({{ zIndex: 3 }})
                            .add();
                    }});
                }}
            }}
        }},
        title: {{
            text: 'icicle-basic · highcharts · anyplot.ai',
            align: 'left',
            margin: 40,
            style: {{
                fontSize: '28px',
                fontWeight: 'bold',
                color: textColor
            }}
        }},
        subtitle: {{
            text: 'File System Structure',
            align: 'left',
            style: {{
                fontSize: '22px',
                color: textSoftColor
            }}
        }},
        credits: {{ enabled: false }},
        exporting: {{ enabled: false }}
    }});
}})();
"""

# Download Highcharts JS from CDN
hc_url = "https://cdnjs.cloudflare.com/ajax/libs/highcharts/11.3.0/highcharts.js"
with urllib.request.urlopen(hc_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# Generate HTML with inline scripts
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 4800px; height: 2700px;"></div>
    <script>{chart_config}</script>
</body>
</html>"""

# Save HTML version
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Take screenshot via Selenium
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

""" pyplots.ai
icicle-basic: Basic Icicle Chart
Library: highcharts unknown | Python 3.13.11
Quality: 94/100 | Created: 2025-12-30
"""

import json
import tempfile
import time
import urllib.request
from pathlib import Path

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Data - File system hierarchy with folders and files
# Hierarchical structure showing directories and file sizes (KB)
# For icicle chart: root at top, children stacked below in rows
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


# Colorblind-safe palette for directory categories
colors = {"Project Files": "#5A5A5A", "src": "#306998", "docs": "#FFD43B", "tests": "#9467BD", "assets": "#17BECF"}


def get_color(name, parent_chain):
    """Get color based on top-level parent category."""
    if name in colors:
        return colors[name]
    for p in parent_chain:
        if p in colors:
            base = colors[p]
            # Lighter shade for deeper levels
            if len(parent_chain) >= 2:
                return base + "CC"  # Add transparency for lighter appearance
            return base
    return "#888888"


def calc_size(node):
    """Calculate total size of a node (sum of all descendants)."""
    if isinstance(node, (int, float)):
        return node
    return sum(calc_size(v) for v in node.values())


def build_rectangles(node, x, y, width, height, level, parent_chain, rects, level_height):
    """Recursively build rectangles for icicle chart."""
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
            color = get_color(name, parent_chain)
            rect = {
                "name": name,
                "x": current_x,
                "y": y,
                "width": child_width,
                "height": level_height,
                "color": color.replace("CC", ""),  # Remove transparency suffix
                "level": level,
                "size": child_size,
                "is_leaf": isinstance(child, (int, float)),
            }
            rects.append(rect)

            # Recurse for children
            if not isinstance(child, (int, float)):
                build_rectangles(
                    child,
                    current_x,
                    y + level_height,
                    child_width,
                    height - level_height,
                    level + 1,
                    parent_chain + [name],
                    rects,
                    level_height,
                )

        current_x += child_width


# Build all rectangles
# Chart dimensions (leaving margins for title and legend)
chart_x = 100
chart_y = 200
chart_width = 4600
chart_height = 2000
level_height = 400  # Fixed height per level (5 levels max)

rectangles = []
build_rectangles(hierarchy, chart_x, chart_y, chart_width, chart_height, 0, [], rectangles, level_height)

# Generate SVG rectangles for Highcharts renderer
svg_elements = []
for rect in rectangles:
    # Determine font size based on level and rectangle size
    if rect["level"] == 0:
        font_size = 52
    elif rect["level"] == 1:
        font_size = 40
    elif rect["level"] == 2:
        font_size = 32
    else:
        font_size = 28

    # Only show label if rectangle is wide enough
    min_width_for_label = font_size * len(rect["name"]) * 0.5
    show_label = rect["width"] >= min_width_for_label and rect["height"] >= font_size + 10

    svg_elements.append(
        {
            "x": rect["x"],
            "y": rect["y"],
            "width": rect["width"],
            "height": rect["height"],
            "color": rect["color"],
            "name": rect["name"],
            "size": rect["size"],
            "is_leaf": rect["is_leaf"],
            "font_size": font_size,
            "show_label": show_label,
        }
    )

# Convert to JavaScript array
rects_json = json.dumps(svg_elements)

# Highcharts renderer to draw custom icicle chart
chart_config = f"""
(function() {{
    var rects = {rects_json};

    // Create chart with renderer
    var chart = Highcharts.chart('container', {{
        chart: {{
            width: 4800,
            height: 2700,
            backgroundColor: '#ffffff',
            events: {{
                load: function() {{
                    var ren = this.renderer;

                    // Draw rectangles
                    rects.forEach(function(r) {{
                        // Draw rectangle
                        ren.rect(r.x, r.y, r.width - 3, r.height - 3, 2)
                            .attr({{
                                fill: r.color,
                                stroke: '#ffffff',
                                'stroke-width': 3,
                                zIndex: 1
                            }})
                            .add();

                        // Draw label if there's room
                        if (r.show_label) {{
                            var labelText = r.name;
                            if (r.is_leaf) {{
                                labelText = r.name + ' (' + r.size + ' KB)';
                            }}

                            // Truncate if too long for rectangle
                            var maxChars = Math.floor(r.width / (r.font_size * 0.55));
                            if (labelText.length > maxChars) {{
                                labelText = labelText.substring(0, maxChars - 2) + '...';
                            }}

                            ren.text(labelText, r.x + r.width / 2, r.y + r.height / 2 + r.font_size / 3)
                                .attr({{
                                    zIndex: 2
                                }})
                                .css({{
                                    color: r.color === '#FFD43B' ? '#333333' : '#ffffff',
                                    fontSize: r.font_size + 'px',
                                    fontWeight: r.font_size >= 40 ? 'bold' : 'normal',
                                    textAnchor: 'middle',
                                    textShadow: r.color === '#FFD43B' ? 'none' : '2px 2px 3px rgba(0,0,0,0.5)'
                                }})
                                .add();
                        }}
                    }});

                    // Draw legend at bottom
                    var legendY = 2450;
                    var legendItems = [
                        {{ name: 'src', color: '#306998' }},
                        {{ name: 'docs', color: '#FFD43B' }},
                        {{ name: 'tests', color: '#9467BD' }},
                        {{ name: 'assets', color: '#17BECF' }}
                    ];
                    var legendX = 1600;
                    var legendSpacing = 400;

                    legendItems.forEach(function(item, i) {{
                        // Legend color box
                        ren.rect(legendX + i * legendSpacing, legendY, 40, 40, 4)
                            .attr({{
                                fill: item.color,
                                stroke: '#333333',
                                'stroke-width': 2,
                                zIndex: 3
                            }})
                            .add();

                        // Legend text
                        ren.text(item.name, legendX + i * legendSpacing + 55, legendY + 30)
                            .css({{
                                color: '#333333',
                                fontSize: '36px',
                                fontWeight: 'normal'
                            }})
                            .add();
                    }});
                }}
            }}
        }},
        title: {{
            text: 'icicle-basic · highcharts · pyplots.ai',
            style: {{
                fontSize: '56px',
                fontWeight: 'bold'
            }},
            y: 60
        }},
        subtitle: {{
            text: 'File System Structure - Directory sizes shown in KB (root at top, children below)',
            style: {{
                fontSize: '36px'
            }},
            y: 120
        }},
        credits: {{
            enabled: false
        }}
    }});
}})();
"""

# Download Highcharts JS
highcharts_url = "https://code.highcharts.com/highcharts.js"

with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

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
    <title>icicle-basic · highcharts · pyplots.ai</title>
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
time.sleep(5)  # Wait for chart to render
driver.save_screenshot("plot_raw.png")
driver.quit()

# Crop to exact 4800x2700 dimensions
img = Image.open("plot_raw.png")
img_cropped = img.crop((0, 0, 4800, 2700))
img_cropped.save("plot.png")
Path("plot_raw.png").unlink()

Path(temp_path).unlink()  # Clean up temp file

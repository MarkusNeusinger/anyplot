"""anyplot.ai
cartogram-area-distortion: Cartogram with Area Distortion by Data Value
Library: highcharts unknown | Python 3.13.13
Quality: 88/100 | Updated: 2026-06-08
Repair: attempt 1 — add radial gradients for depth, refine legend, improve storytelling
"""

import json
import os
import tempfile
import time
import urllib.request
from pathlib import Path

from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — positions 1-4 for four US Census regions
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def make_bubble_gradient(hex_color):
    """Radial gradient: soft white highlight at center → solid hue at edge."""
    return {
        "radialGradient": {"cx": 0.4, "cy": 0.3, "r": 0.7},
        "stops": [[0, "rgba(255,255,255,0.48)"], [0.55, hex_color], [1, hex_color]],
    }


region_colors = {
    "Midwest": IMPRINT_PALETTE[0],  # #009E73 brand green — ALWAYS first series
    "West": IMPRINT_PALETTE[1],  # #C475FD lavender
    "Northeast": IMPRINT_PALETTE[2],  # #4467A3 blue
    "South": IMPRINT_PALETTE[3],  # #BD8233 ochre
}

# US states population (2020 Census, thousands)
states_data = [
    ("CA", "California", 39538, "West"),
    ("TX", "Texas", 29146, "South"),
    ("FL", "Florida", 21538, "South"),
    ("NY", "New York", 20201, "Northeast"),
    ("PA", "Pennsylvania", 13002, "Northeast"),
    ("IL", "Illinois", 12812, "Midwest"),
    ("OH", "Ohio", 11799, "Midwest"),
    ("GA", "Georgia", 10712, "South"),
    ("NC", "North Carolina", 10439, "South"),
    ("MI", "Michigan", 10077, "Midwest"),
    ("NJ", "New Jersey", 9289, "Northeast"),
    ("VA", "Virginia", 8632, "South"),
    ("WA", "Washington", 7615, "West"),
    ("AZ", "Arizona", 7151, "West"),
    ("MA", "Massachusetts", 7030, "Northeast"),
    ("TN", "Tennessee", 6910, "South"),
    ("IN", "Indiana", 6786, "Midwest"),
    ("MO", "Missouri", 6154, "Midwest"),
    ("MD", "Maryland", 6177, "South"),
    ("WI", "Wisconsin", 5894, "Midwest"),
    ("CO", "Colorado", 5774, "West"),
    ("MN", "Minnesota", 5707, "Midwest"),
    ("SC", "South Carolina", 5119, "South"),
    ("AL", "Alabama", 5024, "South"),
    ("LA", "Louisiana", 4658, "South"),
    ("KY", "Kentucky", 4506, "South"),
    ("OR", "Oregon", 4238, "West"),
    ("OK", "Oklahoma", 3960, "South"),
    ("CT", "Connecticut", 3606, "Northeast"),
    ("UT", "Utah", 3272, "West"),
    ("IA", "Iowa", 3191, "Midwest"),
    ("NV", "Nevada", 3104, "West"),
    ("AR", "Arkansas", 3012, "South"),
    ("MS", "Mississippi", 2961, "South"),
    ("KS", "Kansas", 2937, "Midwest"),
    ("NM", "New Mexico", 2118, "West"),
    ("NE", "Nebraska", 1962, "Midwest"),
    ("ID", "Idaho", 1901, "West"),
    ("WV", "West Virginia", 1794, "South"),
    ("HI", "Hawaii", 1456, "West"),
    ("NH", "New Hampshire", 1378, "Northeast"),
    ("ME", "Maine", 1362, "Northeast"),
    ("MT", "Montana", 1085, "West"),
    ("RI", "Rhode Island", 1098, "Northeast"),
    ("DE", "Delaware", 990, "South"),
    ("SD", "South Dakota", 887, "Midwest"),
    ("ND", "North Dakota", 779, "Midwest"),
    ("AK", "Alaska", 733, "West"),
    ("VT", "Vermont", 643, "Northeast"),
    ("WY", "Wyoming", 577, "West"),
]

# Dorling cartogram: geographic positions for bubble centers
geo_positions = {
    "AK": (-114, 30),
    "HI": (-109, 27),
    "WA": (-120, 47.5),
    "OR": (-120.5, 44),
    "CA": (-122, 37),
    "NV": (-117, 39),
    "ID": (-114, 44),
    "MT": (-110, 47),
    "WY": (-108, 43),
    "UT": (-112, 39.5),
    "CO": (-106, 39),
    "AZ": (-112, 34),
    "NM": (-106, 34.5),
    "ND": (-100, 47.5),
    "SD": (-100, 44.5),
    "NE": (-100, 41),
    "KS": (-98, 38.5),
    "OK": (-97, 35.5),
    "TX": (-99, 31),
    "MN": (-94, 46),
    "IA": (-93, 42),
    "MO": (-92, 38.5),
    "AR": (-92, 35),
    "LA": (-92, 31),
    "WI": (-89, 44.5),
    "IL": (-89, 40),
    "MS": (-90, 33),
    "MI": (-85, 44.5),
    "IN": (-86, 40),
    "OH": (-82.5, 40.5),
    "KY": (-85.5, 37.5),
    "TN": (-86, 35.5),
    "AL": (-87, 33),
    "GA": (-83.5, 33),
    "FL": (-82, 28.5),
    "SC": (-80.5, 34),
    "NC": (-79, 35.5),
    "VA": (-77.5, 37.5),
    "WV": (-80.5, 39),
    "PA": (-76, 41.5),
    "NY": (-73, 44.5),
    "NJ": (-69, 39),
    "DE": (-72, 36.5),
    "MD": (-75.5, 38),
    "CT": (-66.5, 43),
    "RI": (-64.5, 41),
    "MA": (-66, 45),
    "VT": (-70, 47),
    "NH": (-68, 46),
    "ME": (-65, 48),
}

top5_states = {"CA", "TX", "FL", "NY", "PA"}

# Simplified US continental outline for geographic reference
us_outline = [
    [-124.7, 48.4],
    [-124.2, 42.0],
    [-122.4, 37.8],
    [-120.5, 34.5],
    [-117.1, 32.5],
    [-114.7, 32.7],
    [-111.0, 31.3],
    [-108.2, 31.8],
    [-106.6, 31.8],
    [-104.0, 29.5],
    [-100.0, 26.5],
    [-97.0, 26.0],
    [-94.5, 29.5],
    [-91.0, 29.0],
    [-88.5, 30.2],
    [-85.5, 30.0],
    [-84.0, 30.5],
    [-82.0, 25.0],
    [-80.0, 25.5],
    [-80.5, 31.5],
    [-78.5, 33.5],
    [-75.5, 35.0],
    [-75.0, 37.5],
    [-74.0, 39.5],
    [-73.5, 40.5],
    [-71.5, 41.0],
    [-70.0, 41.5],
    [-69.5, 43.0],
    [-67.0, 44.5],
    [-67.0, 47.5],
    [-69.5, 47.5],
    [-75.0, 45.0],
    [-79.5, 43.5],
    [-83.0, 46.0],
    [-84.5, 46.5],
    [-88.5, 48.0],
    [-92.0, 48.5],
    [-95.0, 49.0],
    [-104.0, 49.0],
    [-117.0, 49.0],
    [-124.7, 48.4],
]

# Build per-region data points (label size inlined by population tier)
data_by_region = {r: [] for r in region_colors}
for abbr, name, pop, region in states_data:
    lon, lat = geo_positions[abbr]
    label_size = "26px" if pop > 5000 else "22px" if pop > 2000 else "18px"
    point = {
        "name": name,
        "code": abbr,
        "x": lon,
        "y": lat,
        "z": pop,
        "region": region,
        "dataLabels": {"style": {"fontSize": label_size}},
    }
    if abbr in top5_states:
        point["marker"] = {"lineWidth": 4, "lineColor": INK}
    data_by_region[region].append(point)

# Title: 60 chars — within 67-char baseline, no fontsize scaling needed
title = "cartogram-area-distortion · python · highcharts · anyplot.ai"

# Build chart options via highcharts-core
chart = Chart(container="container")
chart.options = HighchartsOptions()

chart.options.chart = {
    "type": "bubble",
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "plotBackgroundColor": "transparent",
    "spacing": [80, 40, 80, 40],
    "style": {"fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"},
}

chart.options.title = {"text": title, "style": {"fontSize": "66px", "fontWeight": "600", "color": INK}, "y": 48}

chart.options.subtitle = {
    "text": ("Dorling Cartogram — Circle area proportional to state population (2020 U.S. Census, thousands)"),
    "style": {"fontSize": "36px", "color": INK_MUTED},
}

chart.options.x_axis = {"visible": False, "min": -128, "max": -60}
chart.options.y_axis = {"visible": False, "min": 24, "max": 50}

chart.options.legend = {
    "enabled": True,
    "layout": "horizontal",
    "align": "center",
    "verticalAlign": "bottom",
    "itemStyle": {"fontSize": "34px", "fontWeight": "normal", "color": INK_SOFT},
    "backgroundColor": ELEVATED_BG,
    "borderWidth": 0,
    "borderRadius": 8,
    "symbolRadius": 10,
    "symbolHeight": 18,
    "symbolWidth": 18,
    "itemDistance": 60,
    "padding": 20,
    "title": {"text": "Region", "style": {"fontSize": "34px", "fontWeight": "bold", "color": INK}},
}

chart.options.credits = {"enabled": False}

chart.options.tooltip = {
    "style": {"fontSize": "28px"},
    "headerFormat": "",
    "pointFormat": ("<b>{point.name}</b> ({point.code})<br/>Population: {point.z:,.0f}k<br/>Region: {point.region}"),
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "borderRadius": 8,
}

chart.options.plot_options = {
    "bubble": {
        "minSize": 28,
        "maxSize": 155,
        "sizeBy": "area",
        "zMin": 0,
        "zMax": 42000,
        "clip": False,
        "dataLabels": {
            "enabled": True,
            "format": "{point.code}",
            "style": {
                "fontSize": "20px",
                "fontWeight": "700",
                "color": "#ffffff",
                "textOutline": "2px rgba(0,0,0,0.55)",
            },
            "allowOverlap": True,
        },
        "opacity": 0.88,
        "borderWidth": 1.5,
        "borderColor": PAGE_BG,
    }
}

# Convert validated options to dict, then append series with custom point fields
options_dict = json.loads(chart.options.to_json())

series_list = []

# Faint US outline for geographic context
series_list.append(
    {
        "type": "line",
        "name": "U.S. Outline",
        "data": us_outline,
        "color": INK_MUTED,
        "lineWidth": 1.5,
        "enableMouseTracking": False,
        "showInLegend": False,
        "marker": {"enabled": False},
        "zIndex": 0,
        "dashStyle": "Dot",
        "opacity": 0.45,
    }
)

# One bubble series per region for categorical legend; gradient gives 3D depth
for region_name, hex_color in region_colors.items():
    points = sorted(data_by_region[region_name], key=lambda p: -p["z"])
    series_list.append(
        {
            "type": "bubble",
            "name": region_name,
            "color": make_bubble_gradient(hex_color),
            "legendSymbolColor": hex_color,
            "data": points,
            "zIndex": 1,
        }
    )

options_dict["series"] = series_list

# Annotation box: area encoding key + population concentration story
options_dict["annotations"] = [
    {
        "draggable": "",
        "labels": [
            {
                "point": {"x": -66, "y": 27.5, "xAxis": 0, "yAxis": 0},
                "text": (
                    f'<b style="font-size:28px;color:{INK}">Circle area ∝ Population</b><br/>'
                    f'<span style="color:{INK_SOFT};font-size:24px;line-height:1.55">'
                    "#1 California · 39,538k<br/>"
                    "#2 Texas · 29,146k<br/>"
                    "#50 Wyoming · 577k<br/>"
                    f'<span style="color:{INK_MUTED};font-size:22px">'
                    "Top 5 states hold 38% of U.S. pop."
                    "</span></span>"
                ),
                "backgroundColor": ELEVATED_BG,
                "borderColor": INK_SOFT,
                "borderRadius": 10,
                "borderWidth": 0,
                "style": {"fontSize": "24px", "color": INK, "lineHeight": "36px"},
                "padding": 22,
                "shape": "rect",
            }
        ],
    }
]

chart_json = json.dumps(options_dict)

# Download Highcharts JS libraries for inline embedding (headless Chrome blocks CDN)
headers = {"User-Agent": "Mozilla/5.0", "Accept": "*/*", "Referer": "https://www.highcharts.com/"}

req = urllib.request.Request("https://code.highcharts.com/highcharts.js", headers=headers)
with urllib.request.urlopen(req, timeout=60) as resp:
    highcharts_js = resp.read().decode("utf-8")

req = urllib.request.Request("https://code.highcharts.com/highcharts-more.js", headers=headers)
with urllib.request.urlopen(req, timeout=60) as resp:
    more_js = resp.read().decode("utf-8")

req = urllib.request.Request("https://code.highcharts.com/modules/annotations.js", headers=headers)
with urllib.request.urlopen(req, timeout=60) as resp:
    annotations_js = resp.read().decode("utf-8")

html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{more_js}</script>
    <script>{annotations_js}</script>
</head>
<body style="margin:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>
        var chartConfig = {chart_json};
        Highcharts.chart('container', chartConfig);
    </script>
</body>
</html>"""

# Save interactive HTML artifact (theme-suffixed)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Screenshot via headless Chrome with authoritative CDP viewport
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
# CDP override is authoritative — --window-size alone loses ~139 px to Chrome chrome
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
Path(temp_path).unlink()

# PIL canvas normalization — Step 0 safety net for ±1–2 px rounding
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")

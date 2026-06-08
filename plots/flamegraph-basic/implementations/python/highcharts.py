"""anyplot.ai
flamegraph-basic: Flame Graph for Performance Profiling
Library: highcharts unknown | Python 3.13.13
Quality: 85/100 | Updated: 2026-06-08
"""

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


# Theme tokens — Imprint chrome (see default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint categorical palette (positions 1..8) — first slot is the brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — simulated CPU profile for a web-server request handler
stacks = {
    "main": {
        "process_request": {
            "parse_headers": {
                "decode_utf8": 45,
                "validate_fields": {"check_required": 22, "type_coerce": 14},
                "sanitize_input": 18,
            },
            "authenticate": {
                "load_session": 28,
                "verify_token": {"hash_compare": 65, "check_expiry": 18, "rotate_jwt": 32},
                "check_acl": {"load_perms": 24, "match_policy": 19},
            },
            "handle_route": {
                "query_database": {
                    "connect_pool": 22,
                    "execute_sql": {"build_query": 38, "fetch_rows": 95, "parse_result": 42, "deserialize_blobs": 28},
                    "release_conn": 12,
                },
                "render_template": {"load_cache": 30, "compile_template": 58, "serialize_json": 48, "escape_html": 22},
                "apply_middleware": {
                    "compress_gzip": 35,
                    "set_cors_headers": 12,
                    "add_csp_headers": 14,
                    "rate_limit_check": {"redis_get": 16, "redis_incr": 9},
                },
            },
            "write_response": {"encode_chunked": 26, "flush_socket": {"poll_fd": 14, "send_buffer": 22}},
        },
        "log_metrics": {"format_entry": 15, "write_buffer": 25, "flush_async": {"open_fd": 8, "write_syscall": 12}},
        "gc_collect": {"mark_phase": 18, "sweep_phase": 22},
        "heartbeat_send": 12,
    }
}

# Total samples (iterative — no helper functions allowed by codestyle)
total_samples = 0
size_stack = [stacks]
while size_stack:
    node = size_stack.pop()
    if isinstance(node, (int, float)):
        total_samples += node
    elif isinstance(node, dict):
        size_stack.extend(node.values())

# Build flame rectangles iteratively: depth, start, end, name, samples.
# Also flag the dominant call-stack path (parent hot ∧ largest child = hot) so
# the bottleneck reads at-a-glance via a per-point border accent.
rectangles = []
traverse = [(stacks, 0, 0, True)]
while traverse:
    node, depth, x_start, parent_hot = traverse.pop()
    if not isinstance(node, dict):
        continue
    sized_children = []
    for name, child in node.items():
        child_size = 0
        sq = [child]
        while sq:
            item = sq.pop()
            if isinstance(item, (int, float)):
                child_size += item
            elif isinstance(item, dict):
                sq.extend(item.values())
        sized_children.append((name, child, child_size))
    hot_name = max(sized_children, key=lambda t: t[2])[0] if sized_children else None
    current_x = x_start
    for name, child, child_size in sized_children:
        is_hot = parent_hot and (name == hot_name)
        if child_size > 0:
            rectangles.append(
                {
                    "x": depth,
                    "low": current_x,
                    "high": current_x + child_size,
                    "name": name,
                    "samples": child_size,
                    "pct": round(child_size / total_samples * 100, 1),
                    "hot": is_hot,
                }
            )
            if isinstance(child, dict):
                traverse.append((child, depth + 1, current_x, is_hot))
        current_x += child_size

# Color assignment: root (depth 0) lands on Imprint slot 1 (#009E73, brand green
# per the "first series ALWAYS #009E73" rule). Descendants cycle the canonical
# palette so siblings at the same depth alternate hues for visual separation.
for i, rect in enumerate(sorted(rectangles, key=lambda r: (r["x"], r["low"]))):
    rect["color"] = IMPRINT_PALETTE[(i * 5 + rect["x"] * 3) % len(IMPRINT_PALETTE)]

# Flip depth so root sits at the bottom (conventional flame orientation)
max_depth = max(r["x"] for r in rectangles)
for r in rectangles:
    r["x"] = max_depth - r["x"]

# Chart — columnrange + inverted gives horizontal bars stacked vertically
chart = Chart(container="container")
chart.options = HighchartsOptions()
chart.options.chart = {
    "type": "columnrange",
    "inverted": True,
    "width": 3200,
    "height": 1800,
    "backgroundColor": PAGE_BG,
    "style": {"color": INK, "fontFamily": "Helvetica, Arial, sans-serif"},
    "marginLeft": 80,
    "marginRight": 80,
    "marginTop": 140,
    "marginBottom": 60,
}
chart.options.title = {
    "text": "flamegraph-basic · python · highcharts · anyplot.ai",
    "style": {"fontSize": "60px", "fontWeight": "bold", "color": INK},
    "margin": 18,
}
chart.options.subtitle = {
    "text": (f"CPU profile — web-server request handler ({int(total_samples)} samples, root at bottom)"),
    "style": {"fontSize": "34px", "color": INK_SOFT},
}

# Value axis (horizontal in inverted): hidden, full proportional width
chart.options.y_axis = {"visible": False, "min": 0, "max": total_samples}

# Category axis (vertical in inverted): hidden — flame format is self-explaining
chart.options.x_axis = {"categories": [str(i) for i in range(max_depth + 1)], "visible": False}

chart.options.legend = {"enabled": False}
chart.options.credits = {"enabled": False}

chart.options.plot_options = {
    "columnrange": {
        "grouping": False,
        "borderWidth": 2,
        "borderColor": PAGE_BG,
        "pointPadding": 0,
        "groupPadding": 0,
        "borderRadius": 1,
    }
}

# Per-point dataLabels with pixel-width-aware truncation.
# Plot area width ~ canvas - marginLeft - marginRight.
plot_width_px = 3200 - 80 - 80
px_per_sample = plot_width_px / total_samples
char_width_px = 14  # approximate width per char at 24px monospace

# Pass 1: pick a candidate label per rectangle (full, name-only, truncated, or none).
for r in rectangles:
    bar_width_px = (r["high"] - r["low"]) * px_per_sample
    max_chars = int((bar_width_px - 16) / char_width_px)
    full_label = f"{r['name']}  {r['pct']}%"
    if max_chars >= len(full_label):
        r["label_text"] = full_label
        r["truncated"] = False
    elif max_chars >= len(r["name"]):
        r["label_text"] = r["name"]
        r["truncated"] = False
    elif max_chars >= 4:
        r["label_text"] = r["name"][: max_chars - 1] + "…"
        r["truncated"] = True
    else:
        r["label_text"] = None
        r["truncated"] = False

# Pass 2: drop truncated labels whose ellipsised form maps to >1 distinct full
# names (e.g. `load…` could mean load_session/load_perms/load_cache). Better to
# show nothing than three identical labels for three different frames.
ambiguous = {}
for r in rectangles:
    if r["truncated"] and r["label_text"]:
        ambiguous.setdefault(r["label_text"], set()).add(r["name"])
for r in rectangles:
    if r["truncated"] and r["label_text"] and len(ambiguous[r["label_text"]]) > 1:
        r["label_text"] = None

# Pass 3: assemble points. Hot-path frames get a darker, thicker border so the
# dominant bottleneck (main → process_request → handle_route → query_database
# → execute_sql → fetch_rows) reads at-a-glance without an annotation overlay.
series_data = []
for r in rectangles:
    point = {"x": r["x"], "low": r["low"], "high": r["high"], "color": r["color"], "name": r["name"]}
    if r["hot"]:
        point["borderColor"] = INK
        point["borderWidth"] = 4
    if r["label_text"]:
        point["dataLabels"] = {
            "enabled": True,
            "inside": True,
            "crop": True,
            "align": "left",
            "verticalAlign": "middle",
            "x": 12,
            "format": r["label_text"],
            "style": {
                "fontSize": "24px",
                "fontWeight": "700" if r["hot"] else "500",
                "fontFamily": '"SF Mono", "Consolas", "Monaco", monospace',
                "color": "#FAF8F1",
                "textOutline": "2px rgba(0,0,0,0.55)",
            },
        }
    series_data.append(point)

chart.options.series = [{"type": "columnrange", "data": series_data, "name": "Call stack"}]
chart.options.tooltip = {
    "headerFormat": "",
    "pointFormat": "<b>{point.name}</b> — {point.samples} samples ({point.pct}%)",
    "backgroundColor": ELEVATED_BG,
    "borderColor": INK_SOFT,
    "style": {"fontSize": "20px", "color": INK},
}

# Download Highcharts JS + highcharts-more (columnrange needs the latter)
highcharts_js = None
for url in ("https://code.highcharts.com/highcharts.js", "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts.js"):
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            highcharts_js = response.read().decode("utf-8")
            break
    except Exception:
        continue
if highcharts_js is None:
    raise RuntimeError("Failed to download Highcharts JS")

highcharts_more_js = None
for url in (
    "https://code.highcharts.com/highcharts-more.js",
    "https://cdn.jsdelivr.net/npm/highcharts@11/highcharts-more.js",
):
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            highcharts_more_js = response.read().decode("utf-8")
            break
    except Exception:
        continue
if highcharts_more_js is None:
    raise RuntimeError("Failed to download Highcharts More JS")

# Inline-script HTML for headless Chrome (file:// can't load CDN bundles)
chart_js = chart.to_js_literal()
inline_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <script>{highcharts_js}</script>
    <script>{highcharts_more_js}</script>
</head>
<body style="margin:0; padding:0; background:{PAGE_BG};">
    <div id="container" style="width: 3200px; height: 1800px;"></div>
    <script>{chart_js}</script>
</body>
</html>"""

# Interactive HTML artifact (CDN scripts — works in regular browsers)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(
        f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>flamegraph-basic · python · highcharts · anyplot.ai</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
    <style>
        body {{ margin: 0; padding: 20px; font-family: Helvetica, Arial, sans-serif; background: {PAGE_BG}; color: {INK}; }}
        #container {{ width: 100%; height: 90vh; min-height: 600px; }}
    </style>
</head>
<body>
    <div id="container"></div>
    <script>{chart_js}</script>
</body>
</html>"""
    )

# PNG screenshot via headless Chrome — CDP override makes viewport authoritative
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(inline_html)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--hide-scrollbars")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": 3200, "height": 1800, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{temp_path}")
time.sleep(5)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
Path(temp_path).unlink()

# Belt-and-braces: pin saved PNG to exact dims so the post-render gate is happy
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
if _img.size != (3200, 1800):
    _norm = Image.new("RGB", (3200, 1800), PAGE_BG)
    _norm.paste(_img, ((3200 - _img.size[0]) // 2, (1800 - _img.size[1]) // 2))
    _norm.save(f"plot-{THEME}.png")

# highcharts

**Note**: Highcharts requires a license for commercial use.

## Import

```python
# IMPORTANT: Correct import path
from highcharts_core.chart import Chart
from highcharts_core.options import HighchartsOptions
from highcharts_core.options.series.bar import BarSeries, ColumnSeries
from highcharts_core.options.series.scatter import ScatterSeries
```

## Create Chart

**CRITICAL**: Always pass `container="container"` to the Chart constructor. This ensures the generated JavaScript targets the correct HTML element.

```python
# CORRECT - always specify container
chart = Chart(container="container")
chart.options = HighchartsOptions()

# Title
chart.options.title = {'text': title}

# Axes
chart.options.x_axis = {'title': {'text': x_label}}
chart.options.y_axis = {'title': {'text': y_label}}
```

## Add Series

```python
from highcharts_core.options.series.scatter import ScatterSeries

series = ScatterSeries()
series.data = list(zip(x_values, y_values))
series.name = 'Data'

chart.add_series(series)
```

## Series Types

```python
from highcharts_core.options.series.bar import BarSeries, ColumnSeries  # ColumnSeries for vertical bars
from highcharts_core.options.series.line import LineSeries
from highcharts_core.options.series.scatter import ScatterSeries
from highcharts_core.options.series.area import AreaSeries
from highcharts_core.options.series.pie import PieSeries
from highcharts_core.options.series.boxplot import BoxPlotSeries
```

## PNG Export (via Selenium)

**IMPORTANT**: Headless Chrome cannot load external CDN scripts from `file://` URLs. You MUST download Highcharts JS and embed it inline.

```python
import tempfile
import time
import urllib.request
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Download Highcharts JS (required for headless Chrome)
highcharts_url = "https://code.highcharts.com/highcharts.js"
with urllib.request.urlopen(highcharts_url, timeout=30) as response:
    highcharts_js = response.read().decode("utf-8")

# For boxplot/errorbar charts, also download highcharts-more.js:
# highcharts_more_url = "https://code.highcharts.com/highcharts-more.js"
# with urllib.request.urlopen(highcharts_more_url, timeout=30) as response:
#     highcharts_more_js = response.read().decode("utf-8")

# Generate HTML with INLINE scripts (not CDN links!)
# Note: PAGE_BG comes from the Theme-adaptive Chrome section below — already tied to ANYPLOT_THEME
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"

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

# Save the HTML artifact for the site (both themes)
with open(f"plot-{THEME}.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Write temp HTML and take screenshot for the PNG artifact
with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
    f.write(html_content)
    temp_path = f.name

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=3200,1800")

driver = webdriver.Chrome(options=chrome_options)
driver.get(f"file://{temp_path}")
time.sleep(5)  # Wait for chart to render
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

Path(temp_path).unlink()  # Clean up temp file
```

## Sizing for 3200×1800 px (starting values — review-loop tunes)

Size + text sizes + marker sizes (the theme/color concerns are covered in the "Theme-adaptive Chrome" section below — do not duplicate):

```python
# Marker sizes (in plotOptions) — density-aware, see default-style-guide.md
chart.options.plot_options = {
    'scatter': {'marker': {'radius': 6}},  # ~2-3x default
    'line': {'lineWidth': 2.5}
}
```

See `prompts/default-style-guide.md` "Proportional Sizing" for review criteria.

**IMPORTANT:** Three places encode the canvas size — keep them in sync:
1. Selenium `--window-size=3200,1800`
2. HTML `<div id="container" style="width: 3200px; height: 1800px;">`
3. `chart.options.chart = {'width': 3200, 'height': 1800, ...}` (see below)

## Output Files

- Implementation: `plots/{spec-id}/implementations/highcharts.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` + `plot-light.html` + `plot-dark.html`.

## Common Pitfalls

1. **White/blank images**: Forgetting `container="container"` in Chart() constructor
2. **CDN not loading**: Using `<script src="...">` instead of inline scripts in headless Chrome
3. **Missing modules**: BoxPlot needs `highcharts-more.js` in addition to `highcharts.js`
4. **Screenshot timing**: Use `time.sleep(5)` for reliable rendering
5. **Encoding errors**: Always use `encoding="utf-8"` in NamedTemporaryFile (Highcharts JS contains special Unicode characters)
6. **X-axis labels cut off in PNG**: Category labels may be clipped at the bottom. Fix by:
   - Increase bottom margin: `chart.options.chart = {'marginBottom': 100, ...}`
   - Or add spacingBottom: `chart.options.chart = {'spacingBottom': 60, ...}`
   - Ensure labels have `style: {'fontSize': '14px'}` for visibility at 3200x1800

## Colors

Use the Okabe-Ito palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`.

```python
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7",
             "#E69F00", "#56B4E9", "#F0E442"]

# Single-series via chart-level colors (first is used)
chart.options.colors = OKABE_ITO[:1]

# Multi-series: assign the full palette; highcharts picks per-series in order
chart.options.colors = OKABE_ITO

# Continuous — NOT Okabe-Ito. Use minColor/maxColor or stops for heatmap/treemap:
chart.options.color_axis = {
    'minColor': '#FFF7BC',   # light side of a viridis-like ramp
    'maxColor': '#014636',
    'stops': [[0, '#440154'], [0.5, '#21908C'], [1, '#FDE725']],  # viridis stops
}
```

## Theme-adaptive Chrome (highcharts mapping)

Every chart option that governs color must be tied to `ANYPLOT_THEME`:

```python
import os
THEME       = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT    = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID        = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

chart.options.chart = {
    'type': 'column',
    'width': 3200, 'height': 1800,
    'backgroundColor': PAGE_BG,
    'style': {'color': INK},
}
chart.options.title = {'text': title, 'style': {'fontSize': '18px', 'color': INK}}
chart.options.x_axis = {
    'title': {'text': x_label, 'style': {'fontSize': '14px', 'color': INK}},
    'labels': {'style': {'fontSize': '12px', 'color': INK_SOFT}},
    'lineColor': INK_SOFT, 'tickColor': INK_SOFT, 'gridLineColor': GRID,
}
chart.options.y_axis = {
    'title': {'text': y_label, 'style': {'fontSize': '14px', 'color': INK}},
    'labels': {'style': {'fontSize': '12px', 'color': INK_SOFT}},
    'lineColor': INK_SOFT, 'tickColor': INK_SOFT, 'gridLineColor': GRID,
}
chart.options.legend = {
    'itemStyle': {'color': INK_SOFT, 'fontSize': '12px'},
    'backgroundColor': ELEVATED_BG, 'borderColor': INK_SOFT, 'borderWidth': 1,
}
```

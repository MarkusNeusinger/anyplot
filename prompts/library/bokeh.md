# bokeh

## Import

```python
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.io import output_file, save
```

## Create Figure

```python
# Target: 4800 × 2700 px (see default-style-guide.md)
p = figure(
    width=4800,
    height=2700,
    title=title,
    x_axis_label=x_label,
    y_axis_label=y_label
)
```

## Plot Methods

```python
# Numeric data
p.scatter(x='x', y='y', source=source)
p.line(x='x', y='y', source=source)

# IMPORTANT: Categorical axes
p = figure(x_range=categories, ...)  # define x_range!
source = ColumnDataSource(data={'x': cat_data, 'y': num_data})
p.scatter(x='x', y='y', source=source)
```

## ColumnDataSource

```python
# Always use ColumnDataSource for flexibility
source = ColumnDataSource(data={
    'x': df['col_x'],
    'y': df['col_y'],
    'color': df['col_color']
})
```

## Save (HTML + PNG via headless Chrome)

**Do NOT use `bokeh.io.export_png`.** It probes `/usr/bin/chromedriver` first; on this dev box that's a snap
shim that fails with "requires the chromium snap to be installed", regardless of whether `xvfb-run` wraps
the call. Save the HTML and screenshot it directly with Selenium instead — this is the same pattern
`highcharts.py` already uses successfully:

```python
import time
from pathlib import Path
from bokeh.io import output_file, save
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Write the interactive HTML (also a required catalog artifact)
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot it with headless Chrome — Selenium 4 / Selenium Manager
# auto-resolves a working driver for the system Chrome.
W, H = 4800, 2700
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
```

## Sizing for 4800×2700 px

```python
# Text sizes
p.title.text_font_size = '28pt'
p.xaxis.axis_label_text_font_size = '22pt'
p.yaxis.axis_label_text_font_size = '22pt'
p.xaxis.major_label_text_font_size = '18pt'
p.yaxis.major_label_text_font_size = '18pt'

# Element sizes
p.scatter(..., size=15)        # ~3-4x default
p.line(..., line_width=3)
```

## Colors

Use the Okabe-Ito palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`.

```python
OKABE_ITO = ['#009E73', '#D55E00', '#0072B2', '#CC79A7',
             '#E69F00', '#56B4E9', '#F0E442']

# Single-series
p.scatter(x, y, color=OKABE_ITO[0])

# Multi-series: iterate in canonical order
for i, group in enumerate(groups):
    p.scatter(..., color=OKABE_ITO[i], legend_label=group)

# Continuous — NOT Okabe-Ito. Use bokeh's built-in palettes:
from bokeh.palettes import Viridis256, Cividis256, BrBG11
#   Sequential: Viridis256, Cividis256
#   Diverging:  BrBG11 (or BrBG9 for coarser binning)
```

## Theme-adaptive Chrome (bokeh mapping)

```python
import os
THEME       = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT    = "#4A4A44" if THEME == "light" else "#B8B7B0"

p.background_fill_color = PAGE_BG
p.border_fill_color     = PAGE_BG
p.outline_line_color    = INK_SOFT

p.title.text_color      = INK
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

if p.legend:
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.border_line_color     = INK_SOFT
    p.legend.label_text_color      = INK_SOFT

# See "Save (HTML + PNG via headless Chrome)" above for output_file + Selenium screenshot.
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/bokeh.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` + `plot-light.html` + `plot-dark.html`.


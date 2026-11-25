# bokeh

**API level:** Bokeh 3. `uv.lock` pins this major; write against its API.

## Import

```python
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.io import output_file, save
from bokeh.transform import dodge  # grouped bars, see "Data block"
```

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (post-render gate in `impl-review.yml` rejects anything off by more than 16 px and re-triggers repair):

- **Landscape**: `width=3200, height=1800`
- **Square**: `width=2400, height=2400`

The Selenium `--window-size` below **must match** these dims. **Do not omit `toolbar_location=None`** — bokeh's default toolbar adds ~30–50 px above the plot, which is what shrank every May 2026 bokeh PNG from 3200×1800 to 3200×1661. The HTML artifact still gets a working toolbar from `output_file(...)`.

## Create Figure

```python
# `width` / `height` are the TOTAL canvas; axis labels at the new 36–42pt
# native-pixel sizes need explicit `min_border_*` reservations or they get
# clipped at the edges of the rendered PNG. Reserve ~150px per side for
# the tick + axis-label stack.
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label=x_label,
    y_axis_label=y_label,
    toolbar_location=None,   # IMPORTANT: bokeh's default toolbar (above the plot)
                             # adds ~30-50px above the canvas, so the saved screenshot
                             # ends up SHORTER than `height=` (e.g. 3200×1800 became
                             # 3200×1661 in the May 2026 fan-out). Disable it for the
                             # static catalog renders — the HTML preview retains the
                             # default toolbar via `output_file(...)` if needed.
    min_border_bottom=160,   # room for 34pt x-tick labels + 42pt x-axis label
    min_border_left=180,     # room for 34pt y-tick labels + 42pt y-axis label
    min_border_top=110,      # room for 50pt title
    min_border_right=50,
)
```

## Plot Methods

```python
source = ColumnDataSource(df)

# Numeric data
p.scatter(x=STUDY_HOURS, y=EXAM_SCORE, source=source)
p.line(x=DATE, y=PRICE, source=source)

# IMPORTANT: Categorical axes — define x_range from the data, in its own order
p = figure(x_range=list(df[QUARTER].unique()), ...)
p.vbar(x=QUARTER, top=SALES, width=0.8, source=source)
```

## Data block

The file follows the six zones of `prompts/adaptable-code.md`. bokeh reads the tidy `df` through `ColumnDataSource(df)`, and every glyph names its columns with the constants: a string argument is a column name, so names with spaces, units and dots work as they are. bokeh never titles an axis from a column name, so pass `x_axis_label=QUARTER, y_axis_label=SALES` and the legend title from the constants. Groups come from the data, each with its palette position:

```python
# Plot: reads only df and the constants above
p = figure(x_range=list(df[QUARTER].unique()), x_axis_label=QUARTER, y_axis_label=SALES, ...)
lines = list(df[PRODUCT_LINE].unique())
width = 0.75 / len(lines)
for i, line in enumerate(lines):
    rows = ColumnDataSource(df[df[PRODUCT_LINE] == line])
    offset = (i - (len(lines) - 1) / 2) * width
    p.vbar(x=dodge(QUARTER, offset, range=p.x_range), top=SALES, width=width, source=rows,
           color=IMPRINT_PALETTE[i], legend_label=str(line))
p.legend.title = PRODUCT_LINE
```

In a tooltip, wrap a column name with spaces in braces: `tooltips=[(SALES, f"@{{{SALES}}}")]`. Ranges come from the data (`Range1d(0, df[SALES].max() * 1.15)`) or stay automatic, never typed numbers. The `0` there is the baseline of a bar or area chart, where the length of the mark is the value; a line or point axis takes both limits from the data, a little outside its smallest and largest value, or stays automatic.

## ColumnDataSource

```python
# Always use ColumnDataSource, built from the tidy df
source = ColumnDataSource(df)
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
# IMPORTANT: W,H must match the figure's width/height above, otherwise the
# bokeh canvas paints into the upper-left corner with white space around it.
W, H = 3200, 1800
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
# IMPORTANT: headless Chrome's --window-size sets the OUTER window, which still
# reserves a phantom ~143px title-bar height even headless — innerHeight (and
# thus the screenshot) comes out short of H. Pin the viewport exactly via CDP.
driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False})
# IMPORTANT: paint the page in the theme's page color. The canvas edge is
# anti-aliased, so the browser's default white page shows through it as a 1 px
# light line along the top and left edge of the PNG (rgb 197,197,196 in dark).
driver.execute_script("document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG)
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
```

## Sizing for 3200×1800 px (starting values — review-loop tunes)

```python
# Text sizes — bokeh fonts render via headless Chrome at CSS pt sizing
# (1pt ≈ 1.333 source-px). The pt values here end up at roughly the same
# source-pixel height as matplotlib 12/10/8pt @ dpi=400 (target ~67 px
# for title). See default-style-guide.md "Why the Native-pixel numbers
# look so much bigger".
p.title.text_font_size = '50pt'
p.xaxis.axis_label_text_font_size = '42pt'
p.yaxis.axis_label_text_font_size = '42pt'
p.xaxis.major_label_text_font_size = '34pt'
p.yaxis.major_label_text_font_size = '34pt'

# Legend — only when a legend is present (legend_label= on glyphs, or a Legend
# added with add_layout). bokeh's legend metrics are fixed pixels sized for an
# 800 px plot: the 20 px key is a speck beside a 34pt label (~45 px) on this canvas.
if p.legend:
    p.legend.label_text_font_size = '34pt'
    p.legend.title_text_font_size = '34pt'  # the 13px default title is unreadable beside the labels
    p.legend.glyph_height = 40    # key about as tall as the label
    p.legend.glyph_width = 40
    p.legend.label_standoff = 16  # key to label
    p.legend.spacing = 12         # between entries
    p.legend.padding = 20         # inside the legend frame

# Element sizes (density-aware — see default-style-guide.md)
p.scatter(..., size=10)        # ~2-3x default
p.line(..., line_width=2.5)
```

See `prompts/default-style-guide.md` "Proportional Sizing" for review criteria.

## Colors

Use the Imprint palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`.

```python
IMPRINT_PALETTE = ['#009E73', '#C475FD', '#4467A3', '#BD8233',
                   '#AE3030', '#2ABCCD', '#954477', '#99B314']
ANYPLOT_AMBER = '#DDCC77'  # warning / caution (outside the categorical pool)

# Single-series
p.scatter(x=STUDY_HOURS, y=EXAM_SCORE, source=source, color=IMPRINT_PALETTE[0])

# Multi-series: iterate the data's groups in canonical palette order
for i, (school, rows) in enumerate(df.groupby(SCHOOL, sort=False)):
    p.scatter(x=STUDY_HOURS, y=EXAM_SCORE, source=ColumnDataSource(rows),
              color=IMPRINT_PALETTE[i], legend_label=str(school))

# Continuous — only the two Imprint ramps are allowed, as (position, hex) stops, low → high,
# with their own stops per theme (style guide, "Continuous Data"). FIELDS: colored cells that
# fill the plot (image, rect or hex grids, patches of a map). MARKS: colored points, lines,
# outlines or bars on the page. Keep only the ramps the plot uses.
import math
from itertools import pairwise
SEQ_FIELDS = (
    [(0.0, "#66E2B2"), (0.368, "#009E73"), (0.582, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#00573D"), (0.467, "#009E73"), (1.0, "#CDD9FF")]
)
SEQ_MARKS = (
    [(0.0, "#009E73"), (0.338, "#4467A3"), (1.0, "#002850")]
    if THEME == "light"
    else [(0.0, "#007755"), (0.32, "#009E73"), (1.0, "#CDD9FF")]
)
# Diverging: the midpoint is the page for fields and a grey that keeps 3:1 for marks
DIV_FIELDS = [(0.0, "#AE3030"), (0.5, "#FAF8F1" if THEME == "light" else "#1A1A17"), (1.0, "#4467A3")]
DIV_MARKS = [(0.0, "#AE3030"), (0.5, "#6B6A63" if THEME == "light" else "#686762"), (1.0, "#4467A3")]

def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    if not math.isfinite(t):
        return "none"  # a missing value draws nothing, never the low end
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i:i + 2], 16) * (1 - share) + int(c1[i:i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )

# LinearColorMapper takes evenly spaced colors, so sample the stops at 256 even steps
ANYPLOT_SEQ256 = [ramp_color(SEQ_FIELDS, k / 255) for k in range(256)]  # SEQ_MARKS on marks
ANYPLOT_DIV256 = [ramp_color(DIV_FIELDS, k / 255) for k in range(256)]  # DIV_MARKS on marks
# Pass to bokeh.models.LinearColorMapper(palette=ANYPLOT_SEQ256, low=…, high=…);
# for the diverging ramp put the midpoint on the middle: low=-m, high=m
# Forbidden: bokeh's Viridis/Cividis/BrBG and any other named palette for continuous data.
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
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15

if p.legend:
    p.legend.background_fill_color = ELEVATED_BG
    p.legend.border_line_color     = INK_SOFT
    p.legend.label_text_color      = INK_SOFT
    p.legend.title_text_color      = INK

# See "Save (HTML + PNG via headless Chrome)" above for output_file + Selenium screenshot.
```

## Output Files

- Implementation: `plots/{spec-id}/implementations/bokeh.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` + `plot-light.html` + `plot-dark.html`.


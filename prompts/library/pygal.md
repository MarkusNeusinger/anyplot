# pygal

## Import

```python
import pygal
from pygal.style import Style
```

## Canvas — hard rule, no deviation

The saved PNG must be **exactly** one of these two sizes (post-render gate in `impl-review.yml` rejects anything off by more than 16 px and re-triggers repair):

- **Landscape**: `width=3200, height=1800`
- **Square**: `width=2400, height=2400`

## Create Chart

```python
chart = pygal.Bar(
    width=3200,
    height=1800,
    title=title,
    x_title=x_label,
    y_title=y_label
)
```

## Chart Types

```python
pygal.Bar()          # Vertical bars
pygal.HorizontalBar()# Horizontal bars
pygal.Line()         # Lines
pygal.XY()           # Scatter (XY coordinates)
pygal.Pie()          # Pie chart
pygal.Box()          # Boxplot
pygal.Histogram()    # Histogram
```

## Add Data

```python
chart.add('Series 1', [1, 2, 3, 4])
chart.add('Series 2', [4, 3, 2, 1])

# X-axis labels
chart.x_labels = ['A', 'B', 'C', 'D']
```

## Save

```python
import os
THEME = os.getenv("ANYPLOT_THEME", "light")

chart.render_to_file(f'plot-{THEME}.svg')                 # SVG (native)
chart.render_to_png(f'plot-{THEME}.png')                  # PNG (requires cairosvg)

# Interactive HTML (pygal renders interactive JS charts)
with open(f'plot-{THEME}.html', 'wb') as f:
    f.write(chart.render())
```

## Sizing + Theme for 3200×1800 px (starting values — review-loop tunes)

pygal's `Style` object carries ALL theme tokens. Derive them from `ANYPLOT_THEME`.

```python
import os
from pygal.style import Style

THEME       = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG     = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK         = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED   = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ('#009E73', '#D55E00', '#0072B2', '#CC79A7',
             '#E69F00', '#56B4E9', '#F0E442')

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,                 # primary text
    foreground_strong=INK,          # title
    foreground_subtle=INK_MUTED,    # tick labels, grid tone
    colors=OKABE_ITO,               # first series = brand green
    # pygal font sizes are unitless integers, rendered into the SVG at the
    # source-pixel grid (no DPI/scale multiplier). To match matplotlib 12pt
    # @ dpi=400 (= 67 source-px), set unitless values directly to the target
    # source-pixel size — see default-style-guide.md "Why the Native-pixel
    # numbers look so much bigger".
    title_font_size=66,             # kept compact for the long mandated title
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)

chart = pygal.Bar(style=custom_style)
```

See `prompts/default-style-guide.md` "Proportional Sizing" for review criteria.

## Grid

```python
chart = pygal.Bar(
    show_x_guides=True,
    show_y_guides=True
)
```

## Colors

Use the Okabe-Ito palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`. For pygal, the palette is always passed via the `Style` object — see the Sizing + Theme section above.

```python
OKABE_ITO = ('#009E73', '#D55E00', '#0072B2', '#CC79A7',
             '#E69F00', '#56B4E9', '#F0E442')

# Single-series: OKABE_ITO[0] is still the first color pygal cycles through
custom_style = Style(..., colors=OKABE_ITO)

# Continuous data: pygal doesn't have built-in cmaps. For heatmap-like scales,
# interpolate manually from viridis via matplotlib (e.g., matplotlib.cm.viridis(t))
# and pass the resulting hex tuple as `colors`.
```

## Grid Opacity

Pygal doesn't expose a grid alpha parameter. The theme-adaptive `foreground_subtle` (tied to `INK_MUTED`) keeps grid lines subtle without manual tuning — both light and dark themes already use the correct muted tone.

## Output Files

- Implementation: `plots/{spec-id}/implementations/pygal.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` + `plot-light.html` + `plot-dark.html` (pygal is interactive).

# pygal

**API level:** Pygal 3. `uv.lock` pins this major; write against its API.

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
# Plot: pygal takes plain lists, built from df below the Data block
table = df.pivot_table(index=QUARTER, columns=PRODUCT_LINE, values=SALES, sort=False)
chart.x_labels = table.index.tolist()
for line in table.columns:
    chart.add(str(line), table[line].tolist())
```

## Data block

The file follows the six zones of `prompts/adaptable-code.md`: the block still ends in a tidy `df`. pygal takes plain Python lists, never a DataFrame, so build them from `df` below the block with `.tolist()`: `df[SALES].tolist()` for one series, a `pivot_table(..., sort=False)` per group as above, and `list(zip(df[STUDY_HOURS], df[EXAM_SCORE]))` for the `(x, y)` points of an XY chart. pygal never titles an axis from a column name, so pass `x_title=QUARTER, y_title=SALES` from the constants. The palette goes in whole through `Style(colors=IMPRINT_PALETTE)`; pygal hands out the first n in order.

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

IMPRINT_PALETTE = ('#009E73', '#C475FD', '#4467A3', '#BD8233',
                   '#AE3030', '#2ABCCD', '#954477', '#99B314')
ANYPLOT_AMBER = '#DDCC77'  # warning / caution (outside the categorical pool)

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,                 # primary text
    foreground_strong=INK,          # title
    foreground_subtle=INK_MUTED,    # tooltips and map outlines; not the grid (see "Grid Opacity")
    guide_stroke_color=INK_MUTED,          # grid lines: pygal's default is black, lost on the dark page
    major_guide_stroke_color=INK_MUTED,    # grid lines at the major ticks
    colors=IMPRINT_PALETTE,         # first series = brand green
    # pygal font sizes are unitless integers, rendered into the SVG at the
    # source-pixel grid (no DPI/scale multiplier). To match matplotlib 12pt
    # @ dpi=400 (= 67 source-px), set unitless values directly to the target
    # source-pixel size — see default-style-guide.md "Why the Native-pixel
    # numbers look so much bigger".
    title_font_size=66,             # kept compact for the long mandated title
    label_font_size=44,             # tick labels (pygal calls the ticks "labels")
    major_label_font_size=44,       # major tick labels: the same size, or one axis shows two sizes
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

Use the Imprint palette (see `prompts/default-style-guide.md` "Categorical Palette"). First series is **always** `#009E73`. For pygal, the palette is always passed via the `Style` object — see the Sizing + Theme section above.

```python
IMPRINT_PALETTE = ('#009E73', '#C475FD', '#4467A3', '#BD8233',
                   '#AE3030', '#2ABCCD', '#954477', '#99B314')
ANYPLOT_AMBER = '#DDCC77'  # warning / caution (outside the categorical pool)

# Single-series: IMPRINT_PALETTE[0] is still the first color pygal cycles through
custom_style = Style(..., colors=IMPRINT_PALETTE)

# Continuous data: pygal doesn't have built-in cmaps. Interpolate manually along
# the Imprint ramps — never substitute viridis or any other named cmap. Each ramp
# is a list of (position, hex) stops, low → high, with its own stops per theme
# (style guide, "Continuous Data"). FIELDS: colored cells that fill the plot
# (treemap tiles, map regions). MARKS: colored points, lines or bars on the page,
# most pygal charts. Keep only the ramps the plot uses.
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
# Diverging (around a meaningful midpoint): the midpoint is the page for fields
# and the muted anchor for marks
DIV_FIELDS = [(0.0, "#AE3030"), (0.5, "#FAF8F1" if THEME == "light" else "#1A1A17"), (1.0, "#4467A3")]
DIV_MARKS = [(0.0, "#AE3030"), (0.5, "#6B6A63" if THEME == "light" else "#A8A79F"), (1.0, "#4467A3")]

def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    t = min(max(t, 0.0), 1.0)
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i:i + 2], 16) * (1 - share) + int(c1[i:i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )

# One color per value: ramp_color(SEQ_MARKS, (value - lo) / (hi - lo))
```

## Grid Opacity

Pygal doesn't expose a grid alpha parameter, and `foreground_subtle` does not color the grid: the guide lines take `guide_stroke_color` and `major_guide_stroke_color`, whose default is black, which almost vanishes on the dark page. Set both from `INK_MUTED` in the `Style`, as above, so the grid stays a muted tone in both themes.

## Output Files

- Implementation: `plots/{spec-id}/implementations/pygal.py` — executed twice with different `ANYPLOT_THEME`.
- Generated artifacts: `plot-light.png` + `plot-dark.png` + `plot-light.html` + `plot-dark.html` (pygal is interactive).

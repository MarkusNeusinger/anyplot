""" pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 79/100 | Created: 2026-03-06
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem, Range1d
from bokeh.plotting import figure, output_file, save


# Data: CREB1 transcription factor binding site motif (10 positions)
positions = list(range(1, 11))
bases = ["A", "C", "G", "T"]
base_colors = {"A": "#2CA02C", "C": "#1F77B4", "G": "#FF7F0E", "T": "#D62728"}

frequencies = np.array(
    [
        [0.25, 0.15, 0.35, 0.25],  # Pos 1: weak preference
        [0.10, 0.10, 0.10, 0.70],  # Pos 2: strong T
        [0.05, 0.05, 0.85, 0.05],  # Pos 3: strong G
        [0.80, 0.05, 0.10, 0.05],  # Pos 4: strong A
        [0.05, 0.80, 0.05, 0.10],  # Pos 5: strong C
        [0.05, 0.05, 0.80, 0.10],  # Pos 6: strong G
        [0.15, 0.10, 0.10, 0.65],  # Pos 7: strong T
        [0.05, 0.80, 0.10, 0.05],  # Pos 8: strong C
        [0.70, 0.10, 0.10, 0.10],  # Pos 9: strong A
        [0.30, 0.20, 0.25, 0.25],  # Pos 10: weak preference
    ]
)

# Calculate information content at each position
max_bits = np.log2(len(bases))
entropy = np.array([-np.sum(f * np.log2(np.where(f > 0, f, 1))) for f in frequencies])
information_content = max_bits - entropy

# Build letter stacks: stretched letter glyphs filling colored rectangles
rect_x, rect_y, rect_w, rect_h, rect_color = [], [], [], [], []
text_x, text_y, text_letter, text_size = [], [], [], []
hover_base, hover_freq, hover_ic, hover_pos = [], [], [], []

# Y-range: tight fit around actual data
max_ic = float(np.max(information_content))
y_top = max_ic + 0.05

# Minimum visible height threshold — skip letters too small to render
MIN_HEIGHT = 0.005

# Plot area pixel height (~2200px effective for 2700 canvas minus margins)
PLOT_PX_HEIGHT = 2200.0
PX_PER_UNIT = PLOT_PX_HEIGHT / y_top
# Font scaling: letter cap-height ≈ 72% of em-height, 1pt ≈ 1.33px
# We want the letter to visually fill the rectangle height
PT_SCALE = PX_PER_UNIT / (1.33 * 0.72)

COLUMN_WIDTH = 0.82

for i, pos in enumerate(positions):
    ic = information_content[i]
    freqs = frequencies[i]
    sorted_indices = np.argsort(freqs)
    y_bottom = 0.0

    for idx in sorted_indices:
        letter = bases[idx]
        height = freqs[idx] * ic
        if height < MIN_HEIGHT:
            y_bottom += height
            continue

        center_y = y_bottom + height / 2

        # Colored rectangle filling the allocated space
        rect_x.append(pos)
        rect_y.append(center_y)
        rect_w.append(COLUMN_WIDTH)
        rect_h.append(height)
        rect_color.append(base_colors[letter])

        # Letter glyph scaled to fill the rectangle
        text_x.append(pos)
        text_y.append(center_y)
        text_letter.append(letter)
        font_pt = max(14, min(int(height * PT_SCALE * 0.92), 260))
        text_size.append(f"{font_pt}pt")

        # Hover data
        hover_base.append(letter)
        hover_freq.append(f"{freqs[idx]:.0%}")
        hover_ic.append(f"{height:.3f}")
        hover_pos.append(str(pos))

        y_bottom += height

# Plot
p = figure(
    width=4800,
    height=2700,
    title="CREB1 Binding Motif · sequence-logo-basic · bokeh · pyplots.ai",
    x_axis_label="Position",
    y_axis_label="Information content (bits)",
    toolbar_location="right",
    x_range=Range1d(0.3, 10.7),
    y_range=Range1d(-0.02, y_top),
)

# Colored rectangles — the "stretched glyph" background
rect_source = ColumnDataSource(
    data={
        "x": rect_x,
        "y": rect_y,
        "width": rect_w,
        "height": rect_h,
        "color": rect_color,
        "base": hover_base,
        "freq": hover_freq,
        "ic": hover_ic,
        "pos": hover_pos,
    }
)
rects = p.rect(
    x="x",
    y="y",
    width="width",
    height="height",
    source=rect_source,
    fill_color="color",
    fill_alpha=0.92,
    line_color="white",
    line_width=1.5,
)

# HoverTool — distinctive Bokeh interactive feature
hover_tool = HoverTool(
    renderers=[rects],
    tooltips=[("Position", "@pos"), ("Base", "@base"), ("Frequency", "@freq"), ("IC contribution", "@ic bits")],
)
p.add_tools(hover_tool)

# White letter glyphs on top of colored rectangles (stretched to fill)
text_source = ColumnDataSource(data={"x": text_x, "y": text_y, "text": text_letter, "size": text_size})
p.text(
    x="x",
    y="y",
    text="text",
    source=text_source,
    text_color="white",
    text_font_size="size",
    text_font_style="bold",
    text_align="center",
    text_baseline="middle",
)

# Legend: colored squares for each base
legend_items = []
for base in bases:
    src = ColumnDataSource(data={"x": [-100], "y": [-100]})
    r = p.rect(
        x="x", y="y", width=0.01, height=0.01, source=src, fill_color=base_colors[base], line_color=base_colors[base]
    )
    legend_items.append(LegendItem(label=base, renderers=[r]))

legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="24pt",
    glyph_width=40,
    glyph_height=40,
    spacing=12,
    padding=20,
    margin=20,
    background_fill_alpha=0.8,
    border_line_alpha=0,
)
p.add_layout(legend, "right")

# Style
p.title.text_font_size = "36pt"
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "24pt"
p.yaxis.major_label_text_font_size = "24pt"

p.xaxis.ticker = positions
p.xaxis.major_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.outline_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.background_fill_color = "#FAFAFA"

# Save
export_png(p, filename="plot.png")
output_file("plot.html", title="sequence-logo-basic · bokeh · pyplots.ai")
save(p)

"""pyplots.ai
sequence-logo-basic: Sequence Logo for Motif Visualization
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 70/100 | Created: 2026-03-06
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

# Build letter stacks: colored letter glyphs sized by information content
text_x, text_y, text_letter, text_color_list, text_size = [], [], [], [], []
hover_x, hover_y, hover_w, hover_h = [], [], [], []
hover_base, hover_freq, hover_ic, hover_pos = [], [], [], []

# Y-range: tight fit around actual data
max_ic = float(np.max(information_content))
y_top = max_ic * 1.05 + 0.02

# Font scaling: plot area height ~2200px for 2700px canvas
# 1 IC unit in pixels ≈ 2200 / y_top. 1pt ≈ 1.33px.
# A capital letter occupies ~72% of font em-height.
# target_px = height_in_ic * (2200 / y_top)
# font_pt = target_px / (1.33 * 0.72)
PX_PER_IC = 2200.0 / y_top
PT_SCALE = PX_PER_IC / (1.33 * 0.72)

for i, pos in enumerate(positions):
    ic = information_content[i]
    freqs = frequencies[i]
    sorted_indices = np.argsort(freqs)
    y_bottom = 0.0

    for idx in sorted_indices:
        letter = bases[idx]
        height = freqs[idx] * ic
        if height < 0.001:
            y_bottom += height
            continue

        text_x.append(pos)
        text_y.append(y_bottom + height / 2)
        text_letter.append(letter)
        text_color_list.append(base_colors[letter])
        font_pt = max(16, min(int(height * PT_SCALE * 0.85), 220))
        text_size.append(f"{font_pt}pt")

        # Invisible hover targets
        hover_x.append(pos)
        hover_y.append(y_bottom + height / 2)
        hover_w.append(0.85)
        hover_h.append(height)
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

# Invisible rectangles for hover interaction
hover_source = ColumnDataSource(
    data={
        "x": hover_x,
        "y": hover_y,
        "width": hover_w,
        "height": hover_h,
        "base": hover_base,
        "freq": hover_freq,
        "ic": hover_ic,
        "pos": hover_pos,
    }
)
hover_rects = p.rect(x="x", y="y", width="width", height="height", source=hover_source, fill_alpha=0, line_alpha=0)

# HoverTool — distinctive Bokeh interactive feature
hover_tool = HoverTool(
    renderers=[hover_rects],
    tooltips=[("Position", "@pos"), ("Base", "@base"), ("Frequency", "@freq"), ("IC contribution", "@ic bits")],
)
p.add_tools(hover_tool)

# Colored letter glyphs (the core visualization)
text_source = ColumnDataSource(
    data={"x": text_x, "y": text_y, "text": text_letter, "color": text_color_list, "size": text_size}
)
p.text(
    x="x",
    y="y",
    text="text",
    source=text_source,
    text_color="color",
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

"""pyplots.ai
energy-level-atomic: Atomic Energy Level Diagram
Library: bokeh 3.8.2 | Python 3.14.3
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import Arrow, ColumnDataSource, HoverTool, Label, NormalHead, Range1d
from bokeh.plotting import figure


# Data - Hydrogen atom energy levels (E_n = -13.6 / n² eV)
levels = [1, 2, 3, 4, 5, 6]
energies = {n: -13.6 / n**2 for n in levels}

# Visual y-positions: sqrt compression for nonlinear mapping
visual_y = {}
for n in levels:
    e = energies[n]
    visual_y[n] = -np.sqrt(abs(e)) * np.sign(-e)

ionization_visual_y = 0.0

# Transitions: (upper_level, lower_level, color, label)
# Lyman series (n -> 1, ultraviolet) - well-differentiated purple gradient
lyman = [(2, 1, "#3C1874", "Lyα 121.6 nm"), (3, 1, "#7D3AC1", "Lyβ 102.6 nm"), (4, 1, "#C76BE0", "Lyγ 97.3 nm")]

# Balmer series (n -> 2, visible light)
balmer = [
    (3, 2, "#C0392B", "Hα 656.3 nm"),
    (4, 2, "#2980B9", "Hβ 486.1 nm"),
    (5, 2, "#6C3483", "Hγ 434.0 nm"),
    (6, 2, "#512E5F", "Hδ 410.2 nm"),
]

# Paschen series (n -> 3, infrared)
paschen = [(4, 3, "#D35400", "Paα 1875 nm"), (5, 3, "#922B21", "Paβ 1282 nm"), (6, 3, "#641E16", "Paγ 1094 nm")]

# Layout positions
level_x0, level_x1 = -1.0, 1.0
lyman_x_start = -2.8
balmer_x_start = 1.8
paschen_x_start = 4.4
arrow_spacing = 0.55

# Custom y-axis tick positions and labels
tick_energies = [0, -0.5, -1.0, -1.5, -3.4, -5.0, -10.0, -13.6]
tick_visual = [-np.sqrt(abs(e)) * np.sign(-e) if e != 0 else 0.0 for e in tick_energies]
tick_labels = [f"{e:.1f}" for e in tick_energies]

# Energy level data as ColumnDataSource (Bokeh best practice)
level_source = ColumnDataSource(
    data={
        "x0": [level_x0] * len(levels),
        "y0": [visual_y[n] for n in levels],
        "x1": [level_x1] * len(levels),
        "y1": [visual_y[n] for n in levels],
        "quantum_n": [f"n = {n}" for n in levels],
        "energy": [f"{energies[n]:.2f} eV" for n in levels],
        "degeneracy": [f"{n**2}-fold" for n in levels],
    }
)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="energy-level-atomic · bokeh · pyplots.ai",
    x_range=Range1d(-5.0, 7.5),
    y_range=Range1d(visual_y[1] - 0.3, ionization_visual_y + 0.8),
    toolbar_location=None,
)

# Custom y-axis
p.yaxis.ticker = tick_visual
p.yaxis.major_label_overrides = dict(zip(tick_visual, tick_labels, strict=True))
p.yaxis.axis_label = "Energy (eV)"

# Energy level lines via ColumnDataSource
level_glyph = p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=level_source, line_width=6, line_color="#306998")

# HoverTool for interactive HTML output
hover = HoverTool(
    renderers=[level_glyph], tooltips=[("Level", "@quantum_n"), ("Energy", "@energy"), ("Degeneracy", "@degeneracy")]
)
p.add_tools(hover)

# Level labels
for n in levels:
    vy = visual_y[n]
    e = energies[n]
    y_off = 18 if n == 6 else (-18 if n == 5 else 0)
    p.add_layout(
        Label(
            x=level_x1 + 0.15,
            y=vy,
            text=f"n={n}  ({e:.2f} eV)",
            text_font_size="22pt",
            text_color="#333333",
            text_baseline="middle",
            y_offset=y_off,
        )
    )

# Ionization limit dashed line
p.segment(
    x0=[p.x_range.start],
    y0=[ionization_visual_y],
    x1=[p.x_range.end],
    y1=[ionization_visual_y],
    line_width=3,
    line_color="#999999",
    line_dash="dashed",
)
p.add_layout(
    Label(
        x=level_x1 + 0.15,
        y=ionization_visual_y + 0.18,
        text="Ionization (0 eV)",
        text_font_size="22pt",
        text_color="#999999",
    )
)

# Draw all transition arrows and labels for each spectral series
all_series = [(lyman, lyman_x_start, "left"), (balmer, balmer_x_start, "right"), (paschen, paschen_x_start, "right")]

for transitions, x_start, label_side in all_series:
    for i, (n_upper, n_lower, color, label_text) in enumerate(transitions):
        x_pos = x_start + i * arrow_spacing
        p.add_layout(
            Arrow(
                end=NormalHead(size=25, fill_color=color, line_color=color),
                x_start=x_pos,
                y_start=visual_y[n_upper],
                x_end=x_pos,
                y_end=visual_y[n_lower],
                line_color=color,
                line_width=4,
            )
        )
        mid_y = (visual_y[n_upper] + visual_y[n_lower]) / 2
        align = "right" if label_side == "left" else "left"
        x_off = -15 if label_side == "left" else 15
        p.add_layout(
            Label(
                x=x_pos,
                y=mid_y,
                text=label_text,
                text_font_size="20pt",
                text_color=color,
                text_align=align,
                x_offset=x_off,
            )
        )

# Series header labels
header_y = ionization_visual_y + 0.55
p.add_layout(
    Label(
        x=lyman_x_start + arrow_spacing,
        y=header_y,
        text="Lyman Series (UV)",
        text_font_size="26pt",
        text_font_style="bold",
        text_color="#3C1874",
        text_align="center",
    )
)
p.add_layout(
    Label(
        x=balmer_x_start + 1.5 * arrow_spacing,
        y=header_y,
        text="Balmer Series (Visible)",
        text_font_size="26pt",
        text_font_style="bold",
        text_color="#C0392B",
        text_align="center",
    )
)
p.add_layout(
    Label(
        x=paschen_x_start + arrow_spacing,
        y=header_y,
        text="Paschen Series (IR)",
        text_font_size="26pt",
        text_font_style="bold",
        text_color="#D35400",
        text_align="center",
    )
)

# Style
p.title.text_font_size = "36pt"
p.title.text_font_style = "normal"
p.yaxis.axis_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "22pt"
p.xaxis.visible = False
p.xgrid.visible = False
p.ygrid.grid_line_alpha = 0.12
p.ygrid.grid_line_width = 1
p.outline_line_color = None
p.background_fill_color = "#FFFFFF"
p.border_fill_color = "#FFFFFF"
p.min_border_left = 130
p.min_border_right = 50
p.min_border_top = 70

# Save
output_file("plot.html", title="Atomic Energy Level Diagram")
save(p)
export_png(p, filename="plot.png")

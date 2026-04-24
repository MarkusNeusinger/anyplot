""" anyplot.ai
ecdf-basic: Basic ECDF Plot
Library: bokeh 3.9.0 | Python 3.14.4
Quality: 87/100 | Updated: 2026-04-24
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Span
from bokeh.plotting import figure


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Okabe-Ito position 1 — always first series

# Data: marathon finish times (minutes) for 300 recreational runners
np.random.seed(42)
n_runners = 300
finish_times = np.random.normal(loc=240, scale=32, size=n_runners)

# ECDF
sorted_times = np.sort(finish_times)
cumulative = np.arange(1, n_runners + 1) / n_runners

# Key percentiles for storytelling
q25, q50, q75 = np.percentile(sorted_times, [25, 50, 75])

source = ColumnDataSource(data={"x": sorted_times, "y": cumulative})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="Marathon Finish Times · ecdf-basic · bokeh · anyplot.ai",
    x_axis_label="Finish Time (minutes)",
    y_axis_label="Cumulative Proportion of Runners",
    y_range=(0, 1.02),
    background_fill_color=PAGE_BG,
    border_fill_color=PAGE_BG,
    toolbar_location=None,
)

# ECDF step line (step-after matches the 1/n jump at each data point)
step_renderer = p.step(x="x", y="y", source=source, line_width=4, line_color=BRAND, mode="after")

# Percentile reference lines (25th, 50th, 75th)
for q_val, q_lbl in [(q25, "25th"), (q50, "50th (median)"), (q75, "75th")]:
    p.add_layout(
        Span(location=q_val, dimension="height", line_color=INK_SOFT, line_dash="dashed", line_width=2, line_alpha=0.55)
    )
    p.add_layout(
        Label(
            x=q_val,
            y=0.03,
            text=f"{q_lbl}: {q_val:.0f} min",
            text_font_size="20pt",
            text_color=INK_SOFT,
            text_font_style="italic",
            x_offset=14,
        )
    )

# Hover tool — bokeh's interactive strength
p.add_tools(
    HoverTool(
        renderers=[step_renderer], tooltips=[("Finish Time", "@x{0.0} min"), ("Cumulative", "@y{0.0%}")], mode="vline"
    )
)

# Typography
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Chrome colors
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Grid: y-only, subtle solid lines; remove box outline
p.outline_line_color = None
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Save
export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html", title="Marathon Finish Times · ecdf-basic · bokeh · anyplot.ai")
save(p)

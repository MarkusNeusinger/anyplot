""" pyplots.ai
scatter-constellation-diagram: Digital Modulation Constellation Diagram
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-17
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem, LinearColorMapper, Span
from bokeh.plotting import figure
from bokeh.resources import Resources
from bokeh.transform import transform


# Data - 16-QAM constellation
np.random.seed(42)

ideal_levels = np.array([-3, -1, 1, 3])
ideal_i, ideal_q = np.meshgrid(ideal_levels, ideal_levels)
ideal_i = ideal_i.flatten()
ideal_q = ideal_q.flatten()

n_symbols = 1000
snr_db = 20
snr_linear = 10 ** (snr_db / 10)
avg_power = np.mean(ideal_levels**2)
noise_std = np.sqrt(avg_power / snr_linear)

symbol_indices = np.random.randint(0, 16, n_symbols)
received_i = ideal_i[symbol_indices] + np.random.normal(0, noise_std, n_symbols)
received_q = ideal_q[symbol_indices] + np.random.normal(0, noise_std, n_symbols)

# EVM calculation per symbol
error_vectors = np.sqrt((received_i - ideal_i[symbol_indices]) ** 2 + (received_q - ideal_q[symbol_indices]) ** 2)
rms_error = np.sqrt(np.mean(error_vectors**2))
max_amplitude = np.sqrt(3**2 + 3**2)
evm_percent = (rms_error / max_amplitude) * 100

# Color mapping by error magnitude for data storytelling
color_mapper = LinearColorMapper(palette="Viridis256", low=0, high=float(np.percentile(error_vectors, 95)))

# Plot - square canvas for equal aspect ratio
p = figure(
    width=3600,
    height=3600,
    title="scatter-constellation-diagram · bokeh · pyplots.ai",
    x_axis_label="In-Phase (I)",
    y_axis_label="Quadrature (Q)",
    x_range=(-4.8, 4.8),
    y_range=(-4.8, 4.8),
    match_aspect=True,
    toolbar_location=None,
)

# Style
p.title.text_font_size = "36pt"
p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

# Remove spines and grid for clean look
p.grid.grid_line_alpha = 0
p.background_fill_color = "#F5F5F5"
p.outline_line_color = None
p.axis.axis_line_color = "#CCCCCC"
p.axis.major_tick_line_color = "#CCCCCC"
p.axis.minor_tick_line_color = None

# Decision boundary grid lines
for level in [-2, 0, 2]:
    p.add_layout(
        Span(location=level, dimension="height", line_color="#AAAAAA", line_dash="dashed", line_width=2, line_alpha=0.5)
    )
    p.add_layout(
        Span(location=level, dimension="width", line_color="#AAAAAA", line_dash="dashed", line_width=2, line_alpha=0.5)
    )

# Received symbols - color-coded by error magnitude
received_source = ColumnDataSource(
    data={
        "i": received_i,
        "q": received_q,
        "error": error_vectors,
        "ideal_i": ideal_i[symbol_indices],
        "ideal_q": ideal_q[symbol_indices],
    }
)
rx_renderer = p.scatter(
    x="i", y="q", source=received_source, size=16, alpha=0.5, color=transform("error", color_mapper), line_color=None
)

# Ideal constellation points
ideal_source = ColumnDataSource(data={"i": ideal_i, "q": ideal_q})
ideal_renderer = p.scatter(
    x="i", y="q", source=ideal_source, size=32, color="#E74C3C", marker="cross", line_width=6, alpha=0.95
)

# Legend
legend = Legend(
    items=[
        LegendItem(label="Received Symbols (color = error)", renderers=[rx_renderer]),
        LegendItem(label="Ideal 16-QAM Points", renderers=[ideal_renderer]),
    ],
    location="top_left",
    label_text_font_size="20pt",
    background_fill_alpha=0.8,
    border_line_color=None,
    padding=15,
    spacing=10,
)
p.add_layout(legend)

# EVM annotation
evm_label = Label(
    x=2.5, y=-4.2, text=f"EVM = {evm_percent:.1f}%", text_font_size="28pt", text_color="#333333", text_font_style="bold"
)
p.add_layout(evm_label)

# HoverTool for interactive HTML version
hover = HoverTool(
    renderers=[rx_renderer],
    tooltips=[("I / Q", "@i{0.00} / @q{0.00}"), ("Ideal", "@ideal_i{0} / @ideal_q{0}"), ("Error", "@error{0.000}")],
)
p.add_tools(hover)

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=Resources(mode="cdn"), title="16-QAM Constellation Diagram")

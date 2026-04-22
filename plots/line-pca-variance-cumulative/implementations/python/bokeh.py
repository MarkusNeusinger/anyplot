""" pyplots.ai
line-pca-variance-cumulative: Cumulative Explained Variance for PCA Component Selection
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 91/100 | Created: 2026-02-17
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import Band, ColumnDataSource, HoverTool, Label, Span
from bokeh.plotting import figure
from sklearn.datasets import load_wine
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# Data - Wine dataset (13 features, good for PCA demonstration)
wine = load_wine()
X = wine.data

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

pca = PCA()
pca.fit(X_scaled)

n_components = np.arange(1, len(pca.explained_variance_ratio_) + 1)
cumulative_variance = np.cumsum(pca.explained_variance_ratio_) * 100
individual_variance = pca.explained_variance_ratio_ * 100

# Threshold crossings
threshold_90 = int(np.argmax(cumulative_variance >= 90) + 1)
threshold_95 = int(np.argmax(cumulative_variance >= 95) + 1)

# Color palette - colorblind-safe with distinct hues
BLUE_PRIMARY = "#306998"
BLUE_LIGHT = "#4A8DB7"
TEAL_THRESHOLD = "#0C7C6E"  # 90% threshold - teal (distinct from purple for CVD)
PURPLE_THRESHOLD = "#7B4FA2"  # 95% threshold - purple
TEXT_DARK = "#2D3436"
TEXT_MID = "#555555"
ACCENT_GRAY = "#888888"

# Sources
source_line = ColumnDataSource(
    data={
        "component": n_components,
        "cumulative": cumulative_variance,
        "individual": individual_variance,
        "base": np.zeros_like(cumulative_variance),
    }
)

source_bars = ColumnDataSource(data={"component": n_components, "individual": individual_variance})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="line-pca-variance-cumulative · bokeh · pyplots.ai",
    x_axis_label="Number of Principal Components",
    y_axis_label="Explained Variance (%)",
    tools="",
    toolbar_location=None,
    y_range=(-2, 112),
    x_range=(0.3, 13.7),
)

# Area fill under cumulative curve (Bokeh Band for visual depth)
band = Band(
    base="component",
    upper="cumulative",
    lower="base",
    source=source_line,
    fill_color=BLUE_PRIMARY,
    fill_alpha=0.07,
    line_color=None,
)
p.add_layout(band)

# Individual variance bars (subtle background)
p.vbar(
    x="component",
    top="individual",
    source=source_bars,
    width=0.5,
    fill_color=BLUE_LIGHT,
    fill_alpha=0.25,
    line_color=BLUE_LIGHT,
    line_alpha=0.4,
    line_width=2,
    legend_label="Individual Variance",
)

# Cumulative variance line
p.line(
    x="component",
    y="cumulative",
    source=source_line,
    line_width=6,
    line_color=BLUE_PRIMARY,
    line_alpha=0.9,
    legend_label="Cumulative Variance",
)

# Markers at each component
p.scatter(
    x="component",
    y="cumulative",
    source=source_line,
    size=22,
    fill_color=BLUE_PRIMARY,
    line_color="white",
    line_width=3,
    fill_alpha=0.95,
)

# Threshold lines
threshold_90_line = Span(
    location=90, dimension="width", line_color=TEAL_THRESHOLD, line_width=3, line_dash="dashed", line_alpha=0.55
)
p.add_layout(threshold_90_line)

threshold_95_line = Span(
    location=95, dimension="width", line_color=PURPLE_THRESHOLD, line_width=3, line_dash="dashed", line_alpha=0.55
)
p.add_layout(threshold_95_line)

# Threshold labels positioned to the right
label_90 = Label(
    x=13.5,
    y=86.5,
    text="90%",
    text_font_size="22pt",
    text_color=TEAL_THRESHOLD,
    text_align="right",
    text_font_style="bold",
)
p.add_layout(label_90)

label_95 = Label(
    x=13.5,
    y=96.2,
    text="95%",
    text_font_size="22pt",
    text_color=PURPLE_THRESHOLD,
    text_align="right",
    text_font_style="bold",
)
p.add_layout(label_95)

# Highlight threshold crossing points with outer glow ring
for th, color in [(threshold_90, TEAL_THRESHOLD), (threshold_95, PURPLE_THRESHOLD)]:
    p.scatter(
        x=[th],
        y=[cumulative_variance[th - 1]],
        size=44,
        fill_color=color,
        fill_alpha=0.15,
        line_color=color,
        line_alpha=0.3,
        line_width=2,
    )
    p.scatter(
        x=[th],
        y=[cumulative_variance[th - 1]],
        size=32,
        fill_color=color,
        line_color="white",
        line_width=4,
        fill_alpha=0.9,
    )

# Annotations for crossing points — repositioned to avoid crowding
# 90% annotation: place to the left and below, away from the dense 8-10 region
label_cross_90 = Label(
    x=threshold_90 - 1.5,
    y=cumulative_variance[threshold_90 - 1] - 10,
    text=f"{threshold_90} components ({cumulative_variance[threshold_90 - 1]:.1f}%)",
    text_font_size="22pt",
    text_color=TEAL_THRESHOLD,
    text_font_style="bold",
    text_align="center",
)
p.add_layout(label_cross_90)

# 95% annotation: place above and to the right
label_cross_95 = Label(
    x=threshold_95 + 1.5,
    y=cumulative_variance[threshold_95 - 1] + 3.5,
    text=f"{threshold_95} components ({cumulative_variance[threshold_95 - 1]:.1f}%)",
    text_font_size="22pt",
    text_color=PURPLE_THRESHOLD,
    text_font_style="bold",
    text_align="center",
)
p.add_layout(label_cross_95)

# HoverTool for HTML export (Bokeh-distinctive interactivity)
hover = HoverTool(
    tooltips=[
        ("Component", "@component"),
        ("Cumulative Variance", "@cumulative{0.1}%"),
        ("Individual Variance", "@individual{0.1}%"),
    ],
    mode="vline",
    renderers=[p.renderers[2]],  # attach to cumulative line
)
p.add_tools(hover)

# Style - Title
p.title.text_font_size = "36pt"
p.title.text_color = TEXT_DARK
p.title.align = "center"

# Style - Axes
p.xaxis.axis_label_text_font_size = "26pt"
p.yaxis.axis_label_text_font_size = "26pt"
p.xaxis.axis_label_text_color = TEXT_DARK
p.yaxis.axis_label_text_color = TEXT_DARK
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"
p.xaxis.major_label_text_color = TEXT_MID
p.yaxis.major_label_text_color = TEXT_MID
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.axis_line_color = ACCENT_GRAY
p.yaxis.axis_line_color = ACCENT_GRAY
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = ACCENT_GRAY
p.yaxis.major_tick_line_color = ACCENT_GRAY

# X-axis integer ticks
p.xaxis.ticker = list(n_components)

# Grid - y-axis dashed, subtle x-grid for readability
p.ygrid.grid_line_alpha = 0.2
p.ygrid.grid_line_dash = "dashed"
p.ygrid.grid_line_color = "#999999"
p.xgrid.grid_line_alpha = 0.08
p.xgrid.grid_line_dash = "dotted"
p.xgrid.grid_line_color = "#999999"

# Legend
p.legend.location = "center_right"
p.legend.label_text_font_size = "24pt"
p.legend.background_fill_alpha = 0.9
p.legend.background_fill_color = "#ffffff"
p.legend.border_line_width = 2
p.legend.border_line_color = "#dddddd"
p.legend.padding = 20
p.legend.margin = 30
p.legend.glyph_height = 35
p.legend.glyph_width = 35
p.legend.spacing = 14

# Background
p.background_fill_color = "#f8f9fa"
p.border_fill_color = "white"
p.outline_line_color = "#dddddd"
p.outline_line_width = 2

# Padding
p.min_border_left = 160
p.min_border_bottom = 130
p.min_border_right = 100
p.min_border_top = 80

# Save as PNG
export_png(p, filename="plot.png")

# Save as HTML for interactive viewing
output_file("plot.html")
save(p)

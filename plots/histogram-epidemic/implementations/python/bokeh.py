""" pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-05
"""

import numpy as np
import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    Label,
    Legend,
    LegendItem,
    LinearAxis,
    NumeralTickFormatter,
    Range1d,
    Span,
)
from bokeh.plotting import figure


# Data - Simulated foodborne illness outbreak over ~90 days
np.random.seed(42)

start_date = pd.Timestamp("2024-01-15")
dates = pd.date_range(start_date, periods=90, freq="D")

# Point-source outbreak with propagated secondary wave
days = np.arange(90)

# Primary wave: sharp peak around day 12 (point source from contaminated event)
confirmed_wave1 = np.random.poisson(lam=np.clip(45 * np.exp(-0.5 * ((days - 12) / 3.5) ** 2), 0.5, None))
# Secondary propagated wave around day 35
confirmed_wave2 = np.random.poisson(lam=np.clip(20 * np.exp(-0.5 * ((days - 35) / 6) ** 2), 0.2, None))
# Low endemic tail
confirmed_tail = np.random.poisson(lam=np.clip(1.5 * np.exp(-0.03 * days), 0.1, None))
confirmed = confirmed_wave1 + confirmed_wave2 + confirmed_tail

# Probable cases: ~30% of confirmed magnitude, slightly delayed
probable = np.random.poisson(
    lam=np.clip(12 * np.exp(-0.5 * ((days - 14) / 4) ** 2) + 7 * np.exp(-0.5 * ((days - 37) / 7) ** 2), 0.1, None)
)

# Suspect cases: smaller, broader distribution
suspect = np.random.poisson(
    lam=np.clip(5 * np.exp(-0.5 * ((days - 13) / 5) ** 2) + 3 * np.exp(-0.5 * ((days - 36) / 8) ** 2), 0.05, None)
)

df = pd.DataFrame({"date": dates, "confirmed": confirmed, "probable": probable, "suspect": suspect})

# Cumulative case count
df["total"] = df["confirmed"] + df["probable"] + df["suspect"]
df["cumulative"] = df["total"].cumsum()

# Convert dates for bokeh
df["date_str"] = df["date"].dt.strftime("%b %d")
bar_width = 0.8 * 24 * 60 * 60 * 1000  # ~0.8 day in ms

# Use vbar_stack with ColumnDataSource
source = ColumnDataSource(
    data={
        "date": df["date"],
        "date_str": df["date_str"],
        "confirmed": df["confirmed"],
        "probable": df["probable"],
        "suspect": df["suspect"],
        "total": df["total"],
        "cumulative": df["cumulative"],
    }
)

# Colorblind-safe palette: blue, teal, light coral (avoids yellow/orange confusion)
colors = ["#306998", "#2CA02C", "#D4726A"]
stack_labels = ["confirmed", "probable", "suspect"]
display_labels = ["Confirmed", "Probable", "Suspect"]

p = figure(
    width=4800,
    height=2700,
    title="histogram-epidemic · bokeh · pyplots.ai",
    x_axis_label="Date of Symptom Onset",
    y_axis_label="New Cases (per day)",
    x_axis_type="datetime",
    toolbar_location=None,
)

# Stacked bars using vbar_stack (idiomatic Bokeh)
renderers = p.vbar_stack(
    stack_labels, x="date", width=bar_width, color=colors, source=source, line_color="white", line_width=0.8, alpha=0.9
)

# Hover tool
hover = HoverTool(
    renderers=list(renderers),
    tooltips=[
        ("Date", "@date_str"),
        ("Confirmed", "@confirmed"),
        ("Probable", "@probable"),
        ("Suspect", "@suspect"),
        ("Total", "@total"),
        ("Cumulative", "@cumulative{0,0}"),
    ],
    mode="vline",
)
p.add_tools(hover)

# Intervention vertical lines with annotations
contamination_date = pd.Timestamp("2024-01-27")
intervention_date = pd.Timestamp("2024-02-05")

span_contamination = Span(
    location=contamination_date,
    dimension="height",
    line_color="#C0392B",
    line_width=3,
    line_dash="dashed",
    line_alpha=0.8,
)
p.add_layout(span_contamination)

span_intervention = Span(
    location=intervention_date,
    dimension="height",
    line_color="#1A9E76",
    line_width=3,
    line_dash="dashed",
    line_alpha=0.8,
)
p.add_layout(span_intervention)

max_cases = int(df["total"].max())

label_contamination = Label(
    x=contamination_date,
    y=max_cases * 0.95,
    text="Source Identified",
    text_font_size="20pt",
    text_color="#C0392B",
    text_font_style="bold",
    x_offset=10,
)
p.add_layout(label_contamination)

label_intervention = Label(
    x=intervention_date,
    y=max_cases * 0.85,
    text="Intervention Began",
    text_font_size="20pt",
    text_color="#1A9E76",
    text_font_style="bold",
    x_offset=10,
)
p.add_layout(label_intervention)

# Secondary y-axis for cumulative line
cumulative_max = int(df["cumulative"].max())
p.extra_y_ranges = {"cumulative": Range1d(start=0, end=cumulative_max * 1.1)}

cumulative_axis = LinearAxis(
    y_range_name="cumulative",
    axis_label="Cumulative Cases",
    axis_label_text_font_size="26pt",
    axis_label_text_color="#444444",
    major_label_text_font_size="20pt",
    major_label_text_color="#555555",
    axis_line_width=2,
    axis_line_color="#AAAAAA",
    minor_tick_line_color=None,
    major_tick_line_color="#AAAAAA",
    formatter=NumeralTickFormatter(format="0,0"),
)
p.add_layout(cumulative_axis, "right")

source_cumulative = ColumnDataSource(data={"date": df["date"], "cumulative": df["cumulative"]})

r_cumulative = p.line(
    x="date",
    y="cumulative",
    source=source_cumulative,
    line_color="#333333",
    line_width=4,
    line_alpha=0.7,
    y_range_name="cumulative",
)

# Legend
legend_items = [LegendItem(label=lbl, renderers=[r]) for lbl, r in zip(display_labels, renderers, strict=False)]
legend_items.append(LegendItem(label=f"Cumulative (total: {cumulative_max:,})", renderers=[r_cumulative]))

legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="22pt",
    label_text_color="#333333",
    glyph_width=50,
    glyph_height=30,
    spacing=14,
    padding=20,
    background_fill_alpha=0.8,
    background_fill_color="white",
    border_line_color="#CCCCCC",
    border_line_alpha=0.5,
)
p.add_layout(legend, "center")

# Typography
p.title.text_font_size = "36pt"
p.title.text_color = "#222222"
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "26pt"
p.yaxis[0].axis_label_text_font_size = "26pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis[0].axis_label_text_color = "#444444"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis[0].major_label_text_font_size = "20pt"
p.xaxis.major_label_text_color = "#555555"
p.yaxis[0].major_label_text_color = "#555555"

# Format primary y-axis
p.yaxis[0].formatter = NumeralTickFormatter(format="0,0")

# Grid
p.xgrid.visible = False
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_color = "#CCCCCC"
p.ygrid.grid_line_width = 1

# Clean frame
p.outline_line_color = None
p.background_fill_color = "white"
p.border_fill_color = "white"
p.xaxis.axis_line_width = 2
p.yaxis[0].axis_line_width = 2
p.xaxis.axis_line_color = "#AAAAAA"
p.yaxis[0].axis_line_color = "#AAAAAA"
p.xaxis.minor_tick_line_color = None
p.yaxis[0].minor_tick_line_color = None
p.xaxis.major_tick_line_color = "#AAAAAA"
p.yaxis[0].major_tick_line_color = "#AAAAAA"

# Axis range
p.y_range.start = 0
p.y_range.end = max_cases * 1.15

# Margins
p.min_border_left = 140
p.min_border_right = 160
p.min_border_bottom = 110
p.min_border_top = 80

# Save
export_png(p, filename="plot.png")
output_file("plot.html", title="histogram-epidemic · bokeh · pyplots.ai")
save(p)

"""anyplot.ai
line-annotated-events: Annotated Line Plot with Event Markers
Library: pygal 3.1.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-16
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, the series line takes the first
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date (2024)"  # role: date
LATENCY = "p95 latency (ms)"  # role: value
EVENT_DATE = "Deploy date"  # role: event_date
EVENT_LABEL = "Deploy"  # role: event_label

# Data: replace this block with your own table, for example df = pd.read_csv("latency.csv").
# One row per day; EVENT_LABEL is filled on the days a deploy happened and empty otherwise.
rng = np.random.default_rng(7)
dates = pd.date_range("2024-01-01", periods=300, freq="D")
deploy_days = {
    38: "v2.4 release",
    71: "CDN migration",
    92: "Cache rewrite",
    190: "DB index rollout",
    247: "v3.0 release",
}
level = np.full(len(dates), 340.0)
level[71:] -= 70  # the CDN migration shortens every request
level[92:190] += 30  # the cache rewrite regresses for a while, then
level[190:] -= 55  # the new database index fixes it
level[247:] += 45  # v3.0 adds heavier pages
weekly = 18 * np.sin(2 * np.pi * np.arange(len(dates)) / 7)
noise = np.convolve(rng.normal(0, 14, len(dates) + 4), np.ones(5) / 5, mode="valid")
labels = pd.Series([deploy_days.get(i) for i in range(len(dates))], dtype="object")
df = pd.DataFrame(
    {
        DATE: dates,
        LATENCY: (level + weekly + noise).round(1),
        EVENT_DATE: pd.Series(dates).where(labels.notna()),
        EVENT_LABEL: labels,
    }
)

# Plot: events are the rows with a label
events = df.dropna(subset=[EVENT_DATE])
y_low = df[LATENCY].min() * 0.9
y_high = df[LATENCY].max() * 1.30
label_heights = (0.0, 0.8)  # event labels alternate between two heights above the data
head_room = df[LATENCY].max() * 1.04

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=60,
    label_font_size=48,
    major_label_font_size=40,
    legend_font_size=40,
    value_font_size=40,
    value_colors=tuple(IMPRINT_PALETTE),
    stroke_width=3,
)

chart = pygal.DateTimeLine(
    width=3200,
    height=1800,
    style=custom_style,
    title="Web Latency Around Deploys · line-annotated-events · python · pygal · anyplot.ai",
    x_title=DATE,
    y_title=LATENCY,
    show_dots=False,
    print_values=True,
    print_values_position="top",
    show_legend=True,
    legend_at_bottom=True,
    legend_box_size=28,
    show_x_guides=False,
    show_y_guides=True,
    margin=60,
    margin_bottom=40,
    range=(y_low, y_high),
    x_label_rotation=0,
    x_value_formatter=lambda d: d.strftime("%b"),
    value_formatter=lambda v: f"{v:.0f}",
    truncate_legend=-1,
    dots_size=9,
    interpolate=None,
)

# Month ticks on the first of each month
chart.x_labels = [d.to_pydatetime() for d in pd.date_range(df[DATE].min(), df[DATE].max(), freq="MS")]

chart.add(
    "p95 latency",
    [(d.to_pydatetime(), v) for d, v in zip(df[DATE], df[LATENCY], strict=True)],
    stroke_style={"width": 4},
    print_values=False,
)

# Events: dashed vertical line from the axis floor to a label height, the label sits on top
for i, (_, row) in enumerate(events.iterrows()):
    when = row[EVENT_DATE].to_pydatetime()
    label = row[EVENT_LABEL]
    top = head_room + label_heights[i % 2] * (y_high - head_room) * 0.55
    chart.add(
        label,
        [{"value": (when, y_low), "formatter": lambda v: ""}, {"value": (when, top), "label": label}],
        stroke_style={"width": 5, "dasharray": "22, 14"},
        show_dots=True,
        dots_size=10,
        print_values=True,
        formatter=lambda v, name=label: name,
        print_values_position="top",
    )

# Output
chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())

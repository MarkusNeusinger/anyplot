"""anyplot.ai
gantt-basic: Basic Gantt Chart
Library: pygal 3.1.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
"""

import os
import re

import cairosvg
import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, one per phase in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BAR_SHARE = 0.6  # share of a row taken by the bar; the rest is the gap between rows
PAD_DAYS = 6  # empty days on each side of the timeline

# Columns: set these to your table's column names
TASK = "Task"  # role: task
START = "Start"  # role: start
END = "End"  # role: end
PHASE = "Phase"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("tasks.csv", parse_dates=[START, END])
df = pd.DataFrame(
    [
        ("Site Survey & Permits", "Site Works", "2026-03-02", "2026-03-27"),
        ("Excavation", "Site Works", "2026-03-23", "2026-04-17"),
        ("Footings & Slab", "Foundation", "2026-04-13", "2026-05-15"),
        ("Basement Walls", "Foundation", "2026-05-04", "2026-05-29"),
        ("Steel Frame Erection", "Structure", "2026-05-25", "2026-07-17"),
        ("Floor Decks & Concrete", "Structure", "2026-06-22", "2026-08-07"),
        ("Roofing", "Envelope", "2026-07-27", "2026-08-21"),
        ("Curtain Wall & Windows", "Envelope", "2026-08-03", "2026-09-25"),
        ("Mechanical & Electrical", "Interiors", "2026-08-24", "2026-10-30"),
        ("Drywall & Finishes", "Interiors", "2026-09-28", "2026-11-20"),
        ("Fit-out & Handover", "Interiors", "2026-11-09", "2026-12-11"),
    ],
    columns=[TASK, PHASE, START, END],
)
df[START] = pd.to_datetime(df[START])
df[END] = pd.to_datetime(df[END])

# Plot: reads only df and the constants above
phases = df[PHASE].drop_duplicates().tolist()
colors = {phase: IMPRINT_PALETTE[i] for i, phase in enumerate(phases)}
tasks = df.sort_values(START, kind="stable").reset_index(drop=True)

t0 = df[START].min() - pd.Timedelta(days=PAD_DAYS)
t1 = df[END].max() + pd.Timedelta(days=PAD_DAYS)
span_days = (t1 - t0).days
n_tasks = len(tasks)

title = "Office Building Construction · gantt-basic · python · pygal · anyplot.ai"
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=round(66 * 67 / len(title)),
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    tooltip_font_size=36,
)

chart = pygal.HorizontalBar(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    show_legend=True,
    legend_at_bottom=False,
    legend_box_size=36,
    print_values=False,
    show_y_guides=False,
    show_x_guides=False,
    show_x_labels=False,
    margin=40,
    margin_bottom=170,
    spacing=20,
    range=(0, 1),
)
chart.x_labels = tasks[TASK].tolist()[::-1]  # pygal draws the first label at the bottom
for phase in phases:
    chart.add(phase, [None] * n_tasks)

svg = chart.render().decode("utf-8")

# Read the plot area pygal laid out, so the bars land on its time axis
plot_group = re.search(r'<g transform="translate\(([\d.]+), ([\d.]+)\)" class="plot">', svg)
plot_bg = re.search(r'<rect [^>]*class="background"[^>]*>', svg[plot_group.end() :])
plot_left, plot_top = float(plot_group.group(1)), float(plot_group.group(2))
plot_w = float(re.search(r'width="([\d.]+)"', plot_bg.group(0)).group(1))
plot_h = float(re.search(r'height="([\d.]+)"', plot_bg.group(0)).group(1))

row_h = plot_h / n_tasks
bar_h = row_h * BAR_SHARE


def x_at(ts):
    return plot_left + (ts - t0).days / span_days * plot_w


elements = []

# Month ticks: dashed guide plus a date label under the plot
for tick in pd.date_range(t0.to_period("M").to_timestamp(), t1, freq="MS"):
    if tick < t0:
        continue
    x = x_at(tick)
    elements.append(
        f'<line x1="{x:.1f}" y1="{plot_top}" x2="{x:.1f}" y2="{plot_top + plot_h}" '
        f'stroke="{INK_MUTED}" stroke-width="2" stroke-dasharray="8,6" opacity="0.7"/>'
    )
    elements.append(
        f'<text x="{x:.1f}" y="{plot_top + plot_h + 52}" font-family="Consolas, monospace" font-size="40" '
        f'fill="{INK}" text-anchor="middle">{tick.strftime("%b %Y")}</text>'
    )
elements.append(
    f'<text x="{plot_left + plot_w / 2:.1f}" y="{plot_top + plot_h + 110}" font-family="Consolas, monospace" '
    f'font-size="44" fill="{INK}" text-anchor="middle">Date</text>'
)

# One bar per task, from its start date to its end date, first task on top
for i, row in tasks.iterrows():
    x_start, x_end = x_at(row[START]), x_at(row[END])
    y_top = plot_top + i * row_h + (row_h - bar_h) / 2
    elements.append(
        f'<rect x="{x_start:.1f}" y="{y_top:.1f}" width="{x_end - x_start:.1f}" height="{bar_h:.1f}" '
        f'fill="{colors[row[PHASE]]}" rx="6" ry="6">'
        f"<title>{row[TASK].replace('&', '&amp;').replace('<', '&lt;')}&#10;{row[START]:%b %d} - {row[END]:%b %d} ({(row[END] - row[START]).days} days)</title>"
        f"</rect>"
    )

svg = svg.replace("</svg>", "\n".join(elements) + "\n</svg>").replace(">No data<", "><")

with open(f"plot-{THEME}.html", "w") as f:
    f.write(svg)
cairosvg.svg2png(bytestring=svg.encode(), write_to=f"plot-{THEME}.png")

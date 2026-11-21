""" anyplot.ai
timeline-basic: Event Timeline
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 83/100 | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, LabelSet, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Save files in the directory where this script is located
os.chdir(Path(__file__).parent)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
EVENT = "Event"  # role: event
PHASE = "Phase"  # role: category

# Data: replace this block with your own table, for example df = pd.read_csv("milestones.csv")
df = pd.DataFrame(
    {
        DATE: pd.to_datetime(
            [
                "2024-01-15",
                "2024-02-01",
                "2024-03-10",
                "2024-04-20",
                "2024-05-15",
                "2024-06-30",
                "2024-07-25",
                "2024-08-15",
                "2024-09-10",
                "2024-10-01",
            ]
        ),
        EVENT: [
            "Project Kickoff",
            "Requirements Complete",
            "Design Review",
            "Prototype Ready",
            "Alpha Release",
            "Beta Testing",
            "Bug Fix Sprint",
            "Performance Audit",
            "Security Review",
            "v1.0 Launch",
        ],
        PHASE: [
            "Planning",
            "Planning",
            "Design",
            "Development",
            "Development",
            "Testing",
            "Testing",
            "Testing",
            "Release",
            "Release",
        ],
    }
)

# Plot: reads only df and the constants above
phases = list(df[PHASE].unique())
phase_color = {phase: IMPRINT_PALETTE[i] for i, phase in enumerate(phases)}

# Labels alternate above (+) and below (-) the axis; the marker keeps its date
df = df.sort_values(DATE).reset_index(drop=True)
df["side"] = [1 if i % 2 == 0 else -1 for i in range(len(df))]
df["level"] = df["side"] * 0.6
df["label_offset"] = df["side"] * 62
df["color"] = df[PHASE].map(phase_color)

pad = pd.Timedelta(days=(df[DATE].max() - df[DATE].min()).days * 0.06)
source = ColumnDataSource(df)

p = figure(
    width=3200,
    height=1800,
    title="timeline-basic · python · bokeh · anyplot.ai",
    x_axis_type="datetime",
    x_axis_label=DATE,
    x_range=Range1d(df[DATE].min() - pad, df[DATE].max() + pad),
    y_range=Range1d(-1.15, 1.85),
    tools="",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=130,
    min_border_top=110,
    min_border_right=130,
)

# Central time axis
p.line(x=[df[DATE].min() - pad, df[DATE].max() + pad], y=[0, 0], line_width=6, line_color=INK_SOFT, line_alpha=0.6)

# Connectors from the axis to each marker
p.segment(x0=DATE, y0=0, x1=DATE, y1="level", source=source, line_width=3, line_color="color", line_alpha=0.8)

# Markers: one glyph per category so the legend names each phase
for phase in phases:
    p.scatter(
        x=DATE,
        y="level",
        source=ColumnDataSource(df[df[PHASE] == phase]),
        size=42,
        color=phase_color[phase],
        marker="circle",
        line_color=PAGE_BG,
        line_width=4,
        legend_label=str(phase),
    )

# Event labels, above or below their markers
p.add_layout(
    LabelSet(
        x=DATE,
        y="level",
        text=EVENT,
        source=source,
        y_offset="label_offset",
        text_align="center",
        text_baseline="middle",
        text_font_size="28pt",
        text_color=INK,
    )
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"

p.xaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.formatter = DatetimeTickFormatter(months="%b %Y", days="%d %b", years="%Y")
p.xaxis.axis_line_color = INK_SOFT
p.xaxis.axis_line_width = 2
p.xaxis.major_tick_line_color = INK_SOFT
p.xaxis.major_tick_line_width = 2
p.xaxis.minor_tick_line_color = None

p.yaxis.visible = False
p.ygrid.visible = False
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.legend.location = "top_left"
p.legend.title = PHASE
p.legend.title_text_font_size = "34pt"
p.legend.title_text_color = INK
p.legend.label_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.border_line_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.95
p.legend.padding = 20
p.legend.spacing = 10

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
W, H = 3200, 1800
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

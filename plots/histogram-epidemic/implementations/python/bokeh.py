"""anyplot.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-06-02
"""

import os
import sys


# Prevent this file (bokeh.py) from shadowing the installed bokeh package when
# Python prepends the script's directory to sys.path at startup.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
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
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint categorical palette: position 1 is always the first series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
ONSET_DATE = "Date of symptom onset"  # role: onset_date
CASE_COUNT = "New cases (per day)"  # role: case_count
CASE_TYPE = "Case classification"  # role: case_type
EVENT_DATE = "Event date"  # role: events
EVENT_LABEL = "Event"  # role: extra

# Data: replace this block with your own tables, for example df = pd.read_csv("cases.csv")
# One row per day and case classification, plus the interventions as two extra columns.
np.random.seed(42)
days = np.arange(90)
dates = pd.date_range("2024-01-15", periods=90, freq="D")

# Primary wave (point source ~day 12), secondary propagated wave (~day 35), low endemic tail
confirmed = (
    np.random.poisson(lam=np.clip(45 * np.exp(-0.5 * ((days - 12) / 3.5) ** 2), 0.5, None))
    + np.random.poisson(lam=np.clip(20 * np.exp(-0.5 * ((days - 35) / 6) ** 2), 0.2, None))
    + np.random.poisson(lam=np.clip(1.5 * np.exp(-0.03 * days), 0.1, None))
)
probable = np.random.poisson(
    lam=np.clip(12 * np.exp(-0.5 * ((days - 14) / 4) ** 2) + 7 * np.exp(-0.5 * ((days - 37) / 7) ** 2), 0.1, None)
)
suspect = np.random.poisson(
    lam=np.clip(5 * np.exp(-0.5 * ((days - 13) / 5) ** 2) + 3 * np.exp(-0.5 * ((days - 36) / 8) ** 2), 0.05, None)
)

df = pd.concat(
    [
        pd.DataFrame({ONSET_DATE: dates, CASE_TYPE: name, CASE_COUNT: counts})
        for name, counts in (("Confirmed", confirmed), ("Probable", probable), ("Suspect", suspect))
    ],
    ignore_index=True,
)
# Interventions ride along as two extra columns, filled on their own rows only
df[EVENT_DATE] = pd.NaT
df[EVENT_LABEL] = None
df.loc[[0, 1], EVENT_DATE] = pd.to_datetime(["2024-01-27", "2024-02-05"])
df.loc[[0, 1], EVENT_LABEL] = ["Source Identified", "Intervention Began"]

# Plot: reads only df and the constants above
events = df[[EVENT_DATE, EVENT_LABEL]].dropna().reset_index(drop=True)
table = df.pivot_table(index=ONSET_DATE, columns=CASE_TYPE, values=CASE_COUNT, aggfunc="sum", sort=False).sort_index()
groups = list(table.columns)
TOTAL = "_total"
CUMULATIVE = "_cumulative"
DATE_TEXT = "_date_text"
table[TOTAL] = table[groups].sum(axis=1)
table[CUMULATIVE] = table[TOTAL].cumsum()
table[DATE_TEXT] = table.index.strftime("%b %d")
source = ColumnDataSource(table.reset_index())

peak = float(table[TOTAL].max())
cumulative_max = float(table[CUMULATIVE].iloc[-1])
bin_ms = table.index.to_series().diff().median().total_seconds() * 1000  # one full bin: adjacent bars

title = "histogram-epidemic · python · bokeh · anyplot.ai"

p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label=ONSET_DATE,
    y_axis_label=CASE_COUNT,
    x_axis_type="datetime",
    toolbar_location=None,  # the default toolbar would shrink the screenshot below 1800 px
    min_border_bottom=160,  # room for 34pt tick + 42pt axis label
    min_border_left=180,
    min_border_top=110,
    min_border_right=200,  # extra room for the secondary-axis label
)

# Stacked bars, one stack layer per case classification
renderers = p.vbar_stack(
    groups,
    x=ONSET_DATE,
    width=bin_ms,
    color=[IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(len(groups))],
    source=source,
    line_color=PAGE_BG,
    line_width=1,
    alpha=0.9,
)

p.add_tools(
    HoverTool(
        renderers=list(renderers),
        tooltips=[("Date", f"@{DATE_TEXT}"), ("Total", f"@{TOTAL}"), ("Cumulative", f"@{CUMULATIVE}{{0,0}}")],
        mode="vline",
    )
)

# Intervention events: dashed vertical lines with an annotation each (first = source, in red)
for i, row in events.iterrows():
    color = IMPRINT_PALETTE[4] if i == 0 else INK_SOFT
    p.add_layout(
        Span(
            location=row[EVENT_DATE],
            dimension="height",
            line_color=color,
            line_width=3,
            line_dash="dashed",
            line_alpha=0.8,
        )
    )
    p.add_layout(
        Label(
            x=row[EVENT_DATE],
            y=peak * (0.95 - 0.13 * i),
            text=str(row[EVENT_LABEL]),
            text_font_size="28pt",
            text_color=color,
            text_font_style="bold",
            x_offset=10,
        )
    )

# Secondary y-axis: cumulative cases
p.extra_y_ranges = {"cumulative": Range1d(start=0, end=cumulative_max * 1.55)}
p.add_layout(
    LinearAxis(
        y_range_name="cumulative",
        axis_label="Cumulative cases",
        axis_label_text_font_size="42pt",
        axis_label_text_color=INK,
        major_label_text_font_size="34pt",
        major_label_text_color=INK_SOFT,
        axis_line_color=INK_SOFT,
        minor_tick_line_color=None,
        major_tick_line_color=INK_SOFT,
        formatter=NumeralTickFormatter(format="0,0"),
    ),
    "right",
)
r_cumulative = p.line(
    x=ONSET_DATE, y=CUMULATIVE, source=source, line_color=INK, line_width=3, line_alpha=0.55, y_range_name="cumulative"
)

# Legend
legend_items = [LegendItem(label=str(g), renderers=[r]) for g, r in zip(groups, renderers, strict=True)]
legend_items.append(LegendItem(label=f"Cumulative (total: {cumulative_max:,.0f})", renderers=[r_cumulative]))
p.add_layout(
    Legend(
        items=legend_items,
        location="top_right",
        title=CASE_TYPE,
        title_text_font_size="34pt",
        title_text_color=INK,
        label_text_font_size="34pt",
        label_text_color=INK_SOFT,
        glyph_width=50,
        glyph_height=30,
        spacing=14,
        padding=20,
        background_fill_alpha=0.9,
        background_fill_color=ELEVATED_BG,
        border_line_color=INK_SOFT,
        border_line_alpha=0.5,
    ),
    "center",
)

# Typography
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.text_font_style = "bold"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis[0].axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis[0].axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis[0].major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis[0].major_label_text_color = INK_SOFT
p.yaxis[0].formatter = NumeralTickFormatter(format="0,0")

# Grid
p.xgrid.visible = False
p.ygrid.grid_line_alpha = 0.15
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_width = 1

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.xaxis.axis_line_color = INK_SOFT
p.yaxis[0].axis_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis[0].minor_tick_line_color = None
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis[0].major_tick_line_color = INK_SOFT

p.y_range.start = 0  # bars rise from zero
p.y_range.end = peak * 1.15

# Save HTML (interactive artifact), then screenshot it with headless Chrome
output_file(f"plot-{THEME}.html", title=title)
save(p)

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
# window-size alone is eaten by browser chrome: pin the viewport exactly
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
# paint the page in the theme colour so the anti-aliased canvas edge shows no white line
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Pin the saved PNG to the exact target size
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.size != (W, H):
    canvas = Image.new("RGB", (W, H), PAGE_BG)
    canvas.paste(img, ((W - img.size[0]) // 2, (H - img.size[1]) // 2))
    canvas.save(f"plot-{THEME}.png")

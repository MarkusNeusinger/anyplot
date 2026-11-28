"""anyplot.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: bokeh 3.10.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-28
"""

import os
import time
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet, Legend, LegendItem, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
# Ordered Likert scale, disagree to agree: five steps of an Imprint diverging marks ramp, red pole for
# disagree, the ramp's grey midpoint for neutral, brand green pole for agree (semantic exception)
LIKERT_RAMP = [(0.0, "#AE3030"), (0.5, "#6B6A63" if THEME == "light" else "#686762"), (1.0, "#009E73")]


def ramp_color(stops, t):
    """The hex at t (0 to 1) along (position, hex) stops, blended linearly in sRGB."""
    (p0, c0), (p1, c1) = next((a, b) for a, b in pairwise(stops) if t <= b[0])
    share = (t - p0) / (p1 - p0)
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


def label_ink(fill):
    """Light or dark ink, whichever reads better on the fill (relative luminance)."""
    r, g, b = (int(fill[i : i + 2], 16) / 255 for i in (1, 3, 5))
    return "#1A1A17" if 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.3 else "#F0EFE8"


LEVEL_COLORS = [ramp_color(LIKERT_RAMP, k / 4) for k in range(5)]
LEVEL_INK = [label_ink(c) for c in LEVEL_COLORS]
MIN_LABEL_PCT = 10  # segments narrower than this share stay unlabeled

# Columns: set these to your table's column names
QUESTION = "Question"  # role: question
STRONGLY_DISAGREE = "Strongly Disagree"  # role: strongly_disagree
DISAGREE = "Disagree"  # role: disagree
NEUTRAL = "Neutral"  # role: neutral
AGREE = "Agree"  # role: agree
STRONGLY_AGREE = "Strongly Agree"  # role: strongly_agree

# Data: replace this block with your own table, for example df = pd.read_csv("survey.csv")
# Employee engagement survey, 10 questions on a 5-point Likert scale (percent of responses)
df = pd.DataFrame(
    {
        QUESTION: [
            "I feel valued at work",
            "My manager provides feedback",
            "I have growth opportunities",
            "Work-life balance is good",
            "I understand company goals",
            "My team communicates well",
            "I have the tools I need",
            "I would recommend this company",
            "Meetings are productive",
            "My contributions are recognized",
        ],
        STRONGLY_DISAGREE: [5, 12, 18, 8, 3, 6, 10, 15, 22, 7],
        DISAGREE: [10, 15, 20, 12, 8, 10, 14, 18, 25, 12],
        NEUTRAL: [15, 18, 22, 15, 12, 14, 16, 17, 20, 15],
        AGREE: [40, 30, 25, 35, 42, 38, 32, 28, 20, 36],
        STRONGLY_AGREE: [30, 25, 15, 30, 35, 32, 28, 22, 13, 30],
    }
)

# Plot: reads only df and the constants above
levels = [STRONGLY_DISAGREE, DISAGREE, NEUTRAL, AGREE, STRONGLY_AGREE]
mid = len(levels) // 2

# Sort by net agreement (agree side minus disagree side); the last row is drawn on top
net = df[levels[mid + 1 :]].sum(axis=1) - df[levels[:mid]].sum(axis=1)
df = df.loc[net.sort_values(kind="stable").index].reset_index(drop=True)
net = df[levels[mid + 1 :]].sum(axis=1) - df[levels[:mid]].sum(axis=1)
questions = [str(q) for q in df[QUESTION]]

# Segment edges around a shared midpoint: the neutral segment is split evenly across zero
widths = np.nan_to_num(df[levels].to_numpy(dtype=float))
half = widths[:, mid] / 2
lefts = np.zeros_like(widths)
rights = np.zeros_like(widths)
for i in range(len(levels)):
    if i < mid:
        rights[:, i] = -(half + widths[:, i + 1 : mid].sum(axis=1))
        lefts[:, i] = rights[:, i] - widths[:, i]
    elif i == mid:
        lefts[:, i] = -half
        rights[:, i] = half
    else:
        lefts[:, i] = half + widths[:, mid + 1 : i].sum(axis=1)
        rights[:, i] = lefts[:, i] + widths[:, i]

span = rights.max() - lefts.min()
net_x = rights.max() + 0.03 * span

p = figure(
    width=3200,
    height=1800,
    y_range=questions,
    x_range=(lefts.min() - 0.04 * span, net_x + 0.12 * span),
    title="bar-diverging-likert · python · bokeh · anyplot.ai",
    toolbar_location=None,
    min_border_bottom=180,
    min_border_left=800,
    min_border_top=120,
    min_border_right=60,
)

legend_items = []
for i, level in enumerate(levels):
    values = df[level]
    source = ColumnDataSource(
        {"question": questions, "left": lefts[:, i], "right": rights[:, i], "value": values, "level": [level] * len(df)}
    )
    renderer = p.hbar(
        y="question",
        left="left",
        right="right",
        height=0.72,
        source=source,
        color=LEVEL_COLORS[i],
        line_color=PAGE_BG,
        line_width=2,
        alpha=0.92,
    )
    legend_items.append(LegendItem(label=level, renderers=[renderer]))
    p.add_tools(
        HoverTool(
            renderers=[renderer], tooltips=[(QUESTION, "@question"), ("Response", "@level"), ("Percentage", "@value%")]
        )
    )

    # Percentage labels inside the segments that have room for them
    fits = (values >= MIN_LABEL_PCT).to_numpy()
    if fits.any():
        label_source = ColumnDataSource(
            {
                "x": ((lefts[:, i] + rights[:, i]) / 2)[fits],
                "y": [q for q, ok in zip(questions, fits, strict=True) if ok],
                "text": [f"{v:g}%" for v in values[fits]],
            }
        )
        p.add_layout(
            LabelSet(
                x="x",
                y="y",
                text="text",
                source=label_source,
                text_align="center",
                text_baseline="middle",
                text_font_size="30pt",
                text_color=LEVEL_INK[i],
                text_font_style="bold",
            )
        )

# Zero line: the shared midpoint of every bar
p.add_layout(Span(location=0, dimension="height", line_color=INK, line_width=2.5, line_alpha=0.5, level="underlay"))

# Net agreement on the right margin: green when positive, red when negative
net_source = ColumnDataSource(
    {
        "x": [net_x] * len(df),
        "y": questions,
        "text": [f"{v:+g}%" for v in net],
        "color": [IMPRINT_PALETTE[0] if v >= 0 else IMPRINT_PALETTE[4] for v in net],
    }
)
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=net_source,
        text_align="left",
        text_baseline="middle",
        text_font_size="24pt",
        text_color="color",
        text_font_style="bold",
    )
)

# Legend below the plot, one entry per Likert level in scale order
p.add_layout(
    Legend(
        items=legend_items,
        orientation="horizontal",
        location="center",
        label_text_font_size="30pt",
        label_text_color=INK_SOFT,
        label_standoff=16,
        spacing=55,
        padding=22,
        margin=18,
        background_fill_color=ELEVATED_BG,
        background_fill_alpha=0.9,
        border_line_color=INK_SOFT,
        border_line_alpha=0.35,
        glyph_height=42,
        glyph_width=42,
        click_policy="hide",
    ),
    "below",
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.text_font_style = "bold"

p.xaxis.axis_label = "← Disagree          Percentage of responses          Agree →"
p.xaxis.axis_label_text_font_size = "38pt"
p.xaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "32pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.12
p.ygrid.grid_line_alpha = 0.0

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Save: interactive HTML, then a headless Chrome screenshot of it
output_file(f"plot-{THEME}.html")
save(p, title="bar-diverging-likert · python · bokeh · anyplot.ai")

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
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

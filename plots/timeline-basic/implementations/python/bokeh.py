""" anyplot.ai
timeline-basic: Event Timeline
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-11
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Save files in the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
os.chdir(SCRIPT_DIR)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
IMPRINT = [
    "#009E73",  # brand green
    "#C475FD",  # vermillion
    "#4467A3",  # blue
    "#BD8233",  # reddish purple
    "#AE3030",  # orange
]

# Data - Software project milestones
events = [
    ("2024-01-15", "Project Kickoff", "Planning"),
    ("2024-02-01", "Requirements Complete", "Planning"),
    ("2024-03-10", "Design Review", "Design"),
    ("2024-04-20", "Prototype Ready", "Development"),
    ("2024-05-15", "Alpha Release", "Development"),
    ("2024-06-30", "Beta Testing", "Testing"),
    ("2024-07-25", "Bug Fix Sprint", "Testing"),
    ("2024-08-15", "Performance Audit", "Testing"),
    ("2024-09-10", "Security Review", "Release"),
    ("2024-10-01", "v1.0 Launch", "Release"),
]

df = pd.DataFrame(events, columns=["date", "event", "category"])
df["date"] = pd.to_datetime(df["date"])

# Assign alternating y positions for label readability (above/below axis)
df["y_pos"] = [0.6 if i % 2 == 0 else -0.6 for i in range(len(df))]

# Map categories to Okabe-Ito colors
categories = df["category"].unique().tolist()
color_map = {cat: IMPRINT[i % len(IMPRINT)] for i, cat in enumerate(categories)}
df["color"] = df["category"].map(color_map)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="timeline-basic · bokeh · anyplot.ai",
    x_axis_type="datetime",
    y_range=(-1.5, 1.5),
    tools="",
    toolbar_location=None,
)

# Draw the central timeline axis (horizontal line)
p.line(
    x=[df["date"].min() - pd.Timedelta(days=10), df["date"].max() + pd.Timedelta(days=10)],
    y=[0, 0],
    line_width=6,
    line_color=INK_SOFT,
    line_alpha=0.6,
)

# Draw vertical connector lines for each event
for _, row in df.iterrows():
    p.line(x=[row["date"], row["date"]], y=[0, row["y_pos"]], line_width=3, line_color=row["color"], line_alpha=0.8)

# Plot event markers with category colors
for cat in categories:
    cat_df = df[df["category"] == cat]
    cat_source = ColumnDataSource(cat_df)
    p.scatter(
        x="date",
        y="y_pos",
        source=cat_source,
        size=35,
        color=color_map[cat],
        alpha=0.9,
        marker="circle",
        legend_label=cat,
        line_color=PAGE_BG,
        line_width=3,
    )

# Add event labels with proper positioning
for _, row in df.iterrows():
    y_offset = 80 if row["y_pos"] > 0 else -80
    baseline = "bottom" if row["y_pos"] > 0 else "top"
    label = Label(
        x=row["date"],
        y=row["y_pos"],
        text=row["event"],
        text_font_size="20pt",
        text_color=INK,
        text_align="center",
        text_baseline=baseline,
        y_offset=y_offset,
    )
    p.add_layout(label)

# Style the plot
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.title.align = "center"

p.xaxis.axis_label = "Date"
p.xaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_orientation = 0.4
p.xaxis.axis_line_color = INK_SOFT
p.xaxis.axis_line_width = 2
p.xaxis.major_tick_line_color = INK_SOFT
p.xaxis.major_tick_line_width = 2
p.xaxis.minor_tick_line_width = 1

p.yaxis.visible = False
p.ygrid.visible = False
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Configure legend
p.legend.location = "top_left"
p.legend.title = "Phase"
p.legend.title_text_font_size = "22pt"
p.legend.title_text_color = INK
p.legend.label_text_font_size = "18pt"
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 30
p.legend.glyph_width = 30
p.legend.border_line_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.95
p.legend.padding = 15
p.legend.spacing = 10

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
W, H = 4800, 2700
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

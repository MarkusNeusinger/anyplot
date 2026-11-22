"""anyplot.ai
network-transport-static: Static Transport Network Diagram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-18
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import Arrow, ColumnDataSource, Label, LabelSet, Range1d, VeeHead
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per route type in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
TYPE_NAMES = {"RE": "Regional Express (RE)", "S": "S-Bahn Local (S)", "EX": "Express (EX)"}
NODE_GAP = 60  # data units kept free between a station centre and an arrow end
PAIR_SPACING = 70  # data units between parallel routes of the same station pair
LABEL_OFFSET = 40  # data units between an edge and its label

# Columns: set these to your table's column names
ORIGIN = "Origin"  # role: routes
DESTINATION = "Destination"  # role: routes
ROUTE = "Route"  # role: routes
DEPARTURE = "Departure"  # role: routes
ARRIVAL = "Arrival"  # role: routes
STATION_ID = "Station ID"  # role: stations
STATION = "Station"  # role: stations
X_POS = "X position"  # role: stations
Y_POS = "Y position"  # role: stations

# Data: replace this block with your own tables, for example df = pd.read_csv("routes.csv")
nodes = pd.DataFrame(
    {
        STATION_ID: list("ABCDEFGHIJKL"),
        STATION: [
            "Central Station",
            "North Terminal",
            "East Junction",
            "South Hub",
            "Airport",
            "University",
            "Industrial Park",
            "Harbor",
            "Stadium",
            "Tech Campus",
            "Medical Center",
            "Downtown",
        ],
        X_POS: [300, 842, 1565, 842, 2450, 2287, 3100, 300, 300, 2900, 2739, 2050],
        Y_POS: [1000, 1592, 1000, 408, 1500, 566, 1000, 1750, 250, 1592, 408, 1200],
    }
).set_index(STATION_ID, drop=False)

df = pd.DataFrame(
    [
        ("A", "B", "RE 10", "06:00", "06:25"),
        ("A", "D", "RE 20", "06:15", "06:35"),
        ("A", "C", "RE 30", "06:30", "07:00"),
        ("B", "H", "S1", "06:35", "06:50"),
        ("B", "E", "RE 10", "06:40", "07:15"),
        ("C", "L", "RE 30", "07:05", "07:20"),
        ("C", "F", "RE 40", "07:10", "07:35"),
        ("D", "I", "S2", "06:45", "07:00"),
        ("D", "F", "RE 20", "06:50", "07:25"),
        ("E", "J", "RE 10", "07:25", "07:40"),
        ("F", "G", "RE 40", "07:45", "08:10"),
        ("F", "K", "RE 20", "07:35", "07:55"),
        ("L", "E", "EX 1", "07:30", "07:50"),
        ("L", "G", "RE 30", "07:25", "08:00"),
        ("J", "G", "RE 10", "07:50", "08:15"),
        ("K", "G", "RE 20", "08:05", "08:25"),
        ("A", "L", "EX 1", "07:00", "07:20"),
        ("H", "A", "S1", "05:30", "05:55"),
        ("I", "A", "S2", "05:45", "06:10"),
        ("B", "A", "RE 11", "07:00", "07:25"),
        ("F", "D", "RE 21", "07:40", "08:15"),
    ],
    columns=[ORIGIN, DESTINATION, ROUTE, DEPARTURE, ARRIVAL],
)

# Plot: reads only df, nodes and the constants above
route_type = df[ROUTE].str.split(" ").str[0].str.rstrip("0123456789")
types = list(route_type.unique())
type_color = {t: IMPRINT_PALETTE[i] for i, t in enumerate(types)}

# Parallel routes of one station pair get separate offset edges
pair = pd.Series([tuple(sorted(p)) for p in zip(df[ORIGIN], df[DESTINATION], strict=True)], index=df.index)
pair_rank = df.groupby(pair, sort=False).cumcount()
pair_size = df.groupby(pair, sort=False)[ROUTE].transform("size")

# Ranges come from the station coordinates, padded by a tenth of the span
x_pad = (nodes[X_POS].max() - nodes[X_POS].min()) * 0.1
y_pad = (nodes[Y_POS].max() - nodes[Y_POS].min()) * 0.1

p = figure(
    width=3200,
    height=1800,
    title="network-transport-static · python · bokeh · anyplot.ai",
    x_range=Range1d(nodes[X_POS].min() - x_pad, nodes[X_POS].max() + x_pad),
    y_range=Range1d(nodes[Y_POS].min() - y_pad, nodes[Y_POS].max() + y_pad),
    tools="",
    toolbar_location=None,
    min_border_left=60,
    min_border_right=60,
    min_border_top=110,
    min_border_bottom=60,
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.align = "center"
p.xgrid.visible = False
p.ygrid.visible = False
p.xaxis.visible = False
p.yaxis.visible = False
p.outline_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG

# Routes: one arrow and one label per row
for i, row in df.iterrows():
    src = nodes.loc[row[ORIGIN]]
    tgt = nodes.loc[row[DESTINATION]]
    dx, dy = tgt[X_POS] - src[X_POS], tgt[Y_POS] - src[Y_POS]
    length = np.hypot(dx, dy)
    nx, ny = dx / length, dy / length
    perp_x, perp_y = -ny, nx

    shift = (pair_rank[i] - (pair_size[i] - 1) / 2) * PAIR_SPACING
    start_x = src[X_POS] + nx * NODE_GAP + perp_x * shift
    start_y = src[Y_POS] + ny * NODE_GAP + perp_y * shift
    end_x = tgt[X_POS] - nx * NODE_GAP + perp_x * shift
    end_y = tgt[Y_POS] - ny * NODE_GAP + perp_y * shift
    color = type_color[route_type[i]]

    p.add_layout(
        Arrow(
            end=VeeHead(size=30, fill_color=color, line_color=color),
            x_start=start_x,
            y_start=start_y,
            x_end=end_x,
            y_end=end_y,
            line_color=color,
            line_width=5,
            line_alpha=0.85,
        )
    )

    # Label sits beside its own edge, on the outer side of a parallel pair
    side = -1 if shift < 0 else 1
    angle = np.arctan2(dy, dx)
    if angle > np.pi / 2:
        angle -= np.pi
    elif angle < -np.pi / 2:
        angle += np.pi
    p.add_layout(
        Label(
            x=(start_x + end_x) / 2 + perp_x * LABEL_OFFSET * side,
            y=(start_y + end_y) / 2 + perp_y * LABEL_OFFSET * side,
            text=f"{row[ROUTE]} | {row[DEPARTURE]}→{row[ARRIVAL]}",
            text_font_size="18pt",
            text_color=color,
            text_font_style="bold",
            text_align="center",
            text_baseline="middle",
            angle=angle,
            background_fill_color=ELEVATED_BG,
            background_fill_alpha=0.9,
        )
    )

# Stations: nodes with names below
station_source = ColumnDataSource(nodes.reset_index(drop=True))
p.scatter(x=X_POS, y=Y_POS, source=station_source, size=64, fill_color=ELEVATED_BG, line_color=INK_SOFT, line_width=5)
# Stations in the leftmost column take their name to the left, where no edge runs
edge_col = nodes[X_POS] == nodes[X_POS].min()
for rows, align, x_off, y_off, base in (
    (nodes[~edge_col], "center", 0, -48, "top"),
    (nodes[edge_col], "right", -50, 0, "middle"),
):
    p.add_layout(
        LabelSet(
            x=X_POS,
            y=Y_POS,
            text=STATION,
            source=ColumnDataSource(rows.reset_index(drop=True)),
            text_font_size="20pt",
            text_font_style="bold",
            text_color=INK,
            text_align=align,
            text_baseline=base,
            x_offset=x_off,
            y_offset=y_off,
            background_fill_color=PAGE_BG,
            background_fill_alpha=0.85,
        )
    )

# Legend: one empty scatter per route type carries the swatch
for t in types:
    p.scatter(
        x=[np.nan],
        y=[np.nan],
        size=30,
        fill_color=type_color[t],
        line_color=type_color[t],
        legend_label=TYPE_NAMES.get(t, t),
    )
p.legend.location = "bottom_right"
p.legend.label_text_font_size = "24pt"
p.legend.label_text_color = INK
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.padding = 18
p.legend.spacing = 10

# Save HTML and PNG
output_file(f"plot-{THEME}.html")
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

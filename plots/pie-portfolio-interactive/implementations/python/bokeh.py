""" anyplot.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-27
"""

import os
import sys


# Remove the script's own directory from sys.path so "bokeh" resolves to the
# installed package, not this file (which shares the name).
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _this_dir]

import numpy as np
import pandas as pd
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, CustomJS, HoverTool, LabelSet, Legend, LegendItem
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

# anyplot categorical palette
ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Data — 10-holding portfolio across 4 asset classes
np.random.seed(42)

data = {
    "asset": [
        "Apple Inc.",
        "Microsoft",
        "Google",
        "Int'l Equities",
        "US Treasury 10Y",
        "Corporate Bonds",
        "Gold ETF",
        "Real Estate Fund",
        "Commodities",
        "Cash",
    ],
    "weight": [18, 15, 12, 10, 15, 10, 5, 8, 3, 4],
    "category": [
        "Equities",
        "Equities",
        "Equities",
        "Equities",
        "Fixed Income",
        "Fixed Income",
        "Alternatives",
        "Alternatives",
        "Alternatives",
        "Cash",
    ],
    "value": [180000, 150000, 120000, 100000, 150000, 100000, 50000, 80000, 30000, 40000],
}

df = pd.DataFrame(data)

# Wedge angles
df["angle"] = df["weight"] / df["weight"].sum() * 2 * np.pi
df["end_angle"] = df["angle"].cumsum() - np.pi / 2
df["start_angle"] = df["end_angle"] - df["angle"]
df["mid_angle"] = (df["start_angle"] + df["end_angle"]) / 2

# Semantic color mapping: green=growth, blue=stable, ochre=commodity, muted=neutral cash
category_colors = {
    "Equities": ANYPLOT_PALETTE[0],  # #009E73 green — growth
    "Fixed Income": ANYPLOT_PALETTE[2],  # #4467A3 blue  — stability
    "Alternatives": ANYPLOT_PALETTE[3],  # #BD8233 ochre — commodities/real assets
    "Cash": INK_MUTED,  # muted neutral — rest/reserve
}
df["color"] = df["category"].map(category_colors)

# Label positions around the outer ring
label_radius = 0.90
df["label_x"] = label_radius * np.cos(df["mid_angle"])
df["label_y"] = label_radius * np.sin(df["mid_angle"])

source = ColumnDataSource(df)

# Title — 53 chars, ratio = 1.0, default 50pt fits
title = "pie-portfolio-interactive · python · bokeh · anyplot.ai"
n = len(title)
ratio = 67 / n if n > 67 else 1.0
title_pt = max(34, round(50 * ratio))

# Figure — square 2400×2400, toolbar_location=None so PNG is exactly 2400×2400
W, H = 2400, 2400
p = figure(
    width=W,
    height=H,
    title=title,
    x_range=(-1.35, 1.35),
    y_range=(-1.35, 1.35),
    tools="hover,tap",
    toolbar_location=None,
)

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.axis.visible = False
p.grid.visible = False

# Donut wedges
p.annular_wedge(
    x=0,
    y=0,
    inner_radius=0.37,
    outer_radius=0.69,
    start_angle="start_angle",
    end_angle="end_angle",
    color="color",
    alpha=0.92,
    source=source,
    line_color=PAGE_BG,
    line_width=4,
    hover_fill_alpha=1.0,
    hover_line_color=INK,
    hover_line_width=6,
)

# Asset name labels outside the ring
p.add_layout(
    LabelSet(
        x="label_x",
        y="label_y",
        text="asset",
        source=source,
        text_font_size="21pt",
        text_align="center",
        text_baseline="middle",
        text_color=INK,
    )
)

# Hover tooltip
hover = p.select(type=HoverTool)
hover.tooltips = [
    ("Asset", "@asset"),
    ("Category", "@category"),
    ("Weight", "@weight{0.0}%"),
    ("Value", "$@value{0,0}"),
]
hover.mode = "mouse"

# Category legend (dummy glyphs placed off-canvas)
legend_items = []
for category, color in category_colors.items():
    dummy = ColumnDataSource(data={"x": [9999], "y": [9999]})
    r = p.scatter(x="x", y="y", size=20, color=color, source=dummy, marker="square")
    legend_items.append(LegendItem(label=category, renderers=[r]))

legend = Legend(items=legend_items, location="center")
legend.label_text_font_size = "28pt"
legend.label_text_color = INK_SOFT
legend.glyph_width = 38
legend.glyph_height = 38
legend.spacing = 16
legend.padding = 24
legend.background_fill_color = ELEVATED_BG
legend.background_fill_alpha = 0.92
legend.border_line_color = INK_SOFT
legend.border_line_width = 1
p.add_layout(legend, "right")

# Title styling
p.title.text_font_size = f"{title_pt}pt"
p.title.text_color = INK
p.title.align = "center"

# Center labels — total portfolio value (two LabelSets: header + value)
total_value = int(df["value"].sum())
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=ColumnDataSource(data={"x": [0], "y": [0.11], "text": ["Total Portfolio"]}),
        text_font_size="23pt",
        text_align="center",
        text_baseline="middle",
        text_color=INK_SOFT,
    )
)
p.add_layout(
    LabelSet(
        x="x",
        y="y",
        text="text",
        source=ColumnDataSource(data={"x": [0], "y": [-0.08], "text": [f"${total_value:,.0f}"]}),
        text_font_size="30pt",
        text_align="center",
        text_baseline="middle",
        text_color=INK,
        text_font_style="bold",
    )
)

# Drill-down JS callback: click a wedge → detail panel with back-to-overview button
callback = CustomJS(
    args={"source": source},
    code="""
    const indices = source.selected.indices;
    if (indices.length === 0) return;
    const i = indices[0];
    const d = source.data;
    let panel = document.getElementById('ap-detail');
    if (!panel) {
        panel = document.createElement('div');
        panel.id = 'ap-detail';
        panel.style.cssText = [
            'position:fixed', 'top:24px', 'right:24px',
            'background:#FFFDF6', 'border:1.5px solid #4A4A44',
            'padding:24px 28px', 'border-radius:10px',
            'font-family:system-ui,sans-serif', 'z-index:1000',
            'min-width:250px', 'box-shadow:0 6px 20px rgba(0,0,0,0.18)'
        ].join(';');
        document.body.appendChild(panel);
    }
    panel.innerHTML =
        '<div style="font-size:19px;font-weight:600;color:#1A1A17;margin-bottom:14px">' + d['asset'][i] + '</div>' +
        '<div style="font-size:15px;color:#4A4A44;margin:6px 0"><span style="font-weight:600">Category:</span> ' + d['category'][i] + '</div>' +
        '<div style="font-size:15px;color:#4A4A44;margin:6px 0"><span style="font-weight:600">Weight:</span> ' + d['weight'][i] + '%</div>' +
        '<div style="font-size:15px;color:#4A4A44;margin:6px 0"><span style="font-weight:600">Value:</span> $' + d['value'][i].toLocaleString() + '</div>' +
        '<button id="ap-back" style="margin-top:16px;padding:8px 16px;background:#009E73;color:#fff;' +
        'border:none;border-radius:5px;cursor:pointer;font-size:14px;font-weight:500">' +
        '&#x2190; Back to Overview</button>';
    document.getElementById('ap-back').addEventListener('click', function() {
        document.getElementById('ap-detail').remove();
        source.selected.indices = [];
        source.change.emit();
    });
""",
)
source.selected.js_on_change("indices", callback)

# Save HTML
output_file(f"plot-{THEME}.html", title="Interactive Portfolio Allocation Chart")
save(p)

# Save PNG: pass a pre-configured webdriver to export_png so it uses our Chrome
# instead of probing /usr/bin/chromedriver (which is a broken snap shim on this host).
opts = Options()
for arg in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--hide-scrollbars"):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
export_png(p, filename=f"plot-{THEME}.png", webdriver=driver)
driver.quit()

"""anyplot.ai
timeseries-decomposition: Time Series Decomposition Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-14
"""

import os
import sys
from pathlib import Path


# Remove current directory from sys.path to avoid collision with this file
script_dir = str(Path(__file__).parent)
sys.path = [p for p in sys.path if p != script_dir and p != ""]

import cairosvg  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402
from statsmodels.tsa.seasonal import seasonal_decompose  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: one position per component, in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
PERIOD = 12  # seasonal cycle length in observations (monthly data, yearly cycle)
UNIT = "ppm"  # shared y-axis title, the panel titles name the components
CHAR_PX = 38  # tuned so the plot areas start at the same x
LABEL_EVERY = 6  # one date tick every this many observations

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CO2 = "CO₂ (ppm)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("series.csv", parse_dates=["Date"])
np.random.seed(42)
n_months = 72
df = pd.DataFrame(
    {
        DATE: pd.date_range("2020-01-01", periods=n_months, freq="ME"),
        CO2: (
            np.linspace(410, 430, n_months)
            + 3 * np.sin(2 * np.pi * np.arange(n_months) / 12)
            + np.random.normal(0, 0.5, n_months)
        ),
    }
)

# Plot: additive decomposition of the series held in df
series = df.set_index(DATE)[CO2].interpolate(limit_direction="both")  # the method needs a gap-free series
period = max(2, min(PERIOD, len(series) // 2))  # two full cycles are the minimum
decomposition = seasonal_decompose(series, model="additive", period=period)

components = [
    ("Original series", decomposition.observed.to_numpy(), UNIT),
    ("Trend", decomposition.trend.to_numpy(), UNIT),
    ("Seasonal", decomposition.seasonal.to_numpy(), UNIT),
    ("Residual", decomposition.resid.to_numpy(), UNIT),
]

x_labels = [d.strftime("%Y-%m") if i % LABEL_EVERY == 0 else "" for i, d in enumerate(df[DATE])]

# Canvas: 3200 x 1800 px, four stacked panels below a title band
total_width, total_height = 3200, 1800
title_height = 110
chart_height = (total_height - title_height) // 4
title_text = "timeseries-decomposition · python · pygal · anyplot.ai"

# Equal left margins keep the plot areas, and so every date, aligned across panels
tick_chars = [max(len(f"{np.nanmin(d):.1f}"), len(f"{np.nanmax(d):.1f}")) + 1 for _, d, _ in components]

charts = []
for idx, (name, data, y_title) in enumerate(components):
    clean = [None if np.isnan(v) else float(v) for v in data]
    lo, hi = np.nanmin(data), np.nanmax(data)
    pad = (hi - lo) * 0.12

    panel_style = Style(
        background=PAGE_BG,
        plot_background=PAGE_BG,
        foreground=INK,
        foreground_strong=INK,
        foreground_subtle=INK_MUTED,
        colors=(IMPRINT_PALETTE[idx],),
        font_family="sans-serif",
        title_font_size=40,
        label_font_size=30,
        major_label_font_size=30,
        legend_font_size=30,
        value_font_size=30,
        stroke_width=4,
    )

    chart = pygal.Line(
        width=total_width,
        height=chart_height,
        style=panel_style,
        title=name,
        y_title=y_title,
        x_title=DATE if idx == len(components) - 1 else None,
        show_legend=False,
        show_y_guides=True,
        show_x_guides=False,
        show_dots=False,
        range=(lo - pad, hi + pad),
        truncate_label=-1,
        x_label_rotation=0,
        y_labels_major_count=4,
        value_formatter=lambda v: f"{v:.1f}",
        margin_left=(max(tick_chars) - tick_chars[idx]) * CHAR_PX,
        show_minor_y_labels=False,
    )
    # Dates only under the bottom panel; the time axis is shared by all four
    chart.x_labels = x_labels if idx == len(components) - 1 else [""] * len(df)
    chart.add(name, clean)
    charts.append(chart)

# Stack the four panels as nested SVG under a title band, one document for the PNG
rendered = [c.render(is_unicode=True) for c in charts]
panel_svgs = [svg[svg.index("<svg") :] for svg in rendered]  # drop the XML declaration
nested = "\n".join(
    svg.replace(
        "<svg ", f'<svg x="0" y="{title_height + i * chart_height}" width="{total_width}" height="{chart_height}" ', 1
    )
    for i, svg in enumerate(panel_svgs)
)
stacked_svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{total_height}">
<rect width="{total_width}" height="{total_height}" fill="{PAGE_BG}"/>
<text x="{total_width // 2}" y="78" text-anchor="middle" font-family="sans-serif" font-size="60" font-weight="bold" fill="{INK}">{title_text}</text>
{nested}
</svg>"""
cairosvg.svg2png(bytestring=stacked_svg.encode(), write_to=f"plot-{THEME}.png")

# Interactive HTML: the four panels as inline SVG
panels = "\n".join(f'<div class="chart">{svg}</div>' for svg in panel_svgs)
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title_text}</title>
    <style>
        body {{ font-family: sans-serif; background: {PAGE_BG}; margin: 20px; color: {INK}; }}
        h1 {{ text-align: center; color: {INK}; font-size: 28px; margin-bottom: 20px; }}
        .charts {{ display: flex; flex-direction: column; max-width: 1200px; margin: 0 auto; }}
        .chart {{ width: 100%; margin-bottom: 10px; }}
        .chart svg {{ width: 100%; height: auto; }}
    </style>
</head>
<body>
    <h1>{title_text}</h1>
    <div class="charts">
{panels}
    </div>
</body>
</html>"""
with open(f"plot-{THEME}.html", "w") as f:
    f.write(html_content)

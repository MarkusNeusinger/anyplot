"""anyplot.ai
band-basic: Basic Band Plot
Library: altair 6.1.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-29
"""

import importlib
import os
import sys


# Drop script directory from sys.path so the `altair` package resolves, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")
np = importlib.import_module("numpy")
pd = importlib.import_module("pandas")

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: position 1 for the central line, position 3 for the band fill
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TIME = "Time (s)"  # role: x
LOWER = "Lower 95% bound (mV)"  # role: y_lower
UPPER = "Upper 95% bound (mV)"  # role: y_upper
CENTER = "Signal (mV)"  # role: y_center

# Data: replace this block with your own table, for example df = pd.read_csv("measurements.csv")
# Oscilloscope voltage with a sinusoidal signal and uncertainty that grows with sensor drift
t = np.linspace(0, 10, 100)
signal = 2 * np.sin(t) + 0.5 * t
half_width = 1.96 * (0.5 + 0.15 * t)
df = pd.DataFrame({TIME: t, LOWER: signal - half_width, UPPER: signal + half_width, CENTER: signal})

# Plot: reads only df and the constants above
ESCAPE = str.maketrans({".": "\\.", "[": "\\[", "]": "\\]", ":": "\\:"})
time_field, lower_field, upper_field, center_field = (c.translate(ESCAPE) for c in (TIME, LOWER, UPPER, CENTER))
x_enc = alt.X(
    time_field, type="quantitative", title=TIME, scale=alt.Scale(domain=[df[TIME].min(), df[TIME].max()], nice=False)
)

band = (
    alt.Chart(df)
    .mark_area(opacity=0.25, color=IMPRINT_PALETTE[2], interpolate="monotone")
    .encode(x=x_enc, y=alt.Y(lower_field, type="quantitative", title=CENTER), y2=alt.Y2(upper_field))
)

line = (
    alt.Chart(df)
    .mark_line(strokeWidth=3, color=IMPRINT_PALETTE[0], interpolate="monotone")
    .encode(
        x=x_enc,
        y=alt.Y(center_field, type="quantitative", title=CENTER),
        tooltip=[
            alt.Tooltip(time_field, type="quantitative", title=TIME, format=".1f"),
            alt.Tooltip(center_field, type="quantitative", title=CENTER, format=".2f"),
            alt.Tooltip(lower_field, type="quantitative", title=LOWER, format=".2f"),
            alt.Tooltip(upper_field, type="quantitative", title=UPPER, format=".2f"),
        ],
    )
)

title = "band-basic · python · altair · anyplot.ai"
title_fs = max(11, round(16 * min(1.0, 67 / len(title))))

chart = (
    alt.layer(band, line)
    .properties(
        width=800,
        height=450,
        autosize=alt.AutoSizeParams(type="fit", contains="padding"),
        padding=10,
        background=PAGE_BG,
        title=alt.Title(title, fontSize=title_fs, color=INK),
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        labelFontSize=10,
        titleFontSize=12,
        labelColor=INK_SOFT,
        titleColor=INK,
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.12,
    )
    .configure_axisX(grid=False)
)

# Save
chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

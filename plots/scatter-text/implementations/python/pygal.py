"""anyplot.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: pygal 3.1.0 | Python 3.13.13
Quality: 83/100 | Created: 2026-05-17
"""

import os

import pandas as pd
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
# Label text must stay legible on both pages: the brand green is used on the dark page,
# a darker shade of it on the light page.
LABEL_COLOR = "#007A58" if THEME == "light" else "#2FD3A5"

# Imprint palette
IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
PRICE = "Price Competitiveness"  # role: x
FEATURES = "Feature Completeness"  # role: y
PRODUCT = "Product"  # role: label

# Data: replace this block with your own table, for example df = pd.read_csv("products.csv")
df = pd.DataFrame(
    {
        PRICE: [2.1, 3.5, 4.2, 1.8, 3.9, 2.7, 4.6, 1.2, 3.3, 4.8],
        FEATURES: [3.2, 2.8, 4.1, 4.5, 1.9, 3.7, 3.3, 2.1, 4.8, 2.5],
        PRODUCT: [
            "Budget Start-up Kit",
            "Standard Pro",
            "Premium Suite",
            "Full Enterprise",
            "Lite Essentials",
            "Growth Package",
            "Elite Plus",
            "Basic Tier",
            "Advanced Max",
            "Performance Edge",
        ],
    }
)

# Plot
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=(LABEL_COLOR,) + IMPRINT_PALETTE[1:],
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=48,
    value_label_font_size=48,
    stroke_width=2.5,
)

pad_x = (df[PRICE].max() - df[PRICE].min()) * 0.15
pad_y = (df[FEATURES].max() - df[FEATURES].min()) * 0.15

# pygal draws the label text inside its dot loop, so the dots stay on at a negligible
# size; the CSS centres each label on its (x, y) and colours it for the page.
label_css = (
    f"inline:.text-overlay text.label{{text-anchor:middle !important;fill:{LABEL_COLOR} !important;font-weight:600}}"
    ".dots .dot{opacity:0 !important}"
)

chart = pygal.XY(
    css=["file://style.css", "file://graph.css", label_css],
    style=custom_style,
    width=3200,
    height=1800,
    title="scatter-text · python · pygal · anyplot.ai",
    x_title=PRICE,
    y_title=FEATURES,
    show_legend=False,
    show_dots=True,
    dots_size=0.1,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
    print_labels=True,
    print_values=False,
    xrange=(df[PRICE].min() - pad_x, df[PRICE].max() + pad_x),
    range=(df[FEATURES].min() - pad_y, df[FEATURES].max() + pad_y),
)


chart.add(
    "Products",
    [{"value": (x, y), "label": name} for x, y, name in zip(df[PRICE], df[FEATURES], df[PRODUCT], strict=True)],
)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())

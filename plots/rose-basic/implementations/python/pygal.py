""" anyplot.ai
rose-basic: Basic Rose Chart
Library: pygal 3.1.3 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-27
"""

import os
from math import pi

import pandas as pd
from pygal.graph.radar import Radar
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions, first is the brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
ARC_STEPS = 20  # points sampled along each wedge's outer arc for a smooth curve
HEADROOM = 1.03  # share of the largest value kept free beyond the longest wedge

# Columns: set these to your table's column names
MONTH = "Month"  # role: category
RAINFALL = "Rainfall (mm)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("rainfall.csv")
df = pd.DataFrame(
    {
        MONTH: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        RAINFALL: [145, 115, 95, 65, 45, 35, 20, 25, 50, 90, 135, 155],
    }
)


# Plot
class RoseChart(Radar):
    """Radar subclass: pie-slice wedges instead of a star polygon, value labels above the fill."""

    def _plot(self):
        delta = 2 * pi / self._len if self._len else 0
        half = delta / 2
        for serie in self.series:
            serie_node = self.svg.serie(serie)
            for i, value in enumerate(serie.values):
                theta_start = self._x_pos[i] - half
                wedge = [self.view((0, theta_start))] + [
                    self.view((value, theta_start + delta * k / ARC_STEPS)) for k in range(ARC_STEPS + 1)
                ]
                self.svg.line(serie_node["plot"], wedge, close=True, class_="line reactive")
        labels = self.svg.node(self.nodes["plot"], class_="axis y web")
        for axis in self.nodes["plot"].findall("g[@class='axis y web']"):
            for guides in axis:
                for text in guides.findall("text"):
                    guides.remove(text)
                    labels.append(text)


custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=56,
    stroke_width=3,
    opacity=0.7,
    opacity_hover=0.88,
)

chart = RoseChart(
    width=2400,
    height=2400,
    style=custom_style,
    title="rose-basic · python · pygal · anyplot.ai",
    fill=True,
    stroke=True,
    show_dots=False,
    show_legend=False,
    show_x_guides=True,
    show_y_guides=True,
    range=(0, df[RAINFALL].max() * HEADROOM),
    margin=70,
    value_formatter=lambda v: f"{v:.0f} mm",
)

chart.x_labels = df[MONTH].tolist()
chart.add(RAINFALL, df[RAINFALL].tolist())

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())

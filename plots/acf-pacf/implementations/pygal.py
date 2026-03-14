"""pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: pygal 3.1.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-14
"""

import io
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pygal
from PIL import Image
from pygal.style import Style
from statsmodels.tsa.stattools import acf, pacf


# Data - Synthetic monthly airline-style passenger data with trend and seasonality
np.random.seed(42)
n_obs = 200
t = np.arange(n_obs)
trend = 0.05 * t
seasonal = 10 * np.sin(2 * np.pi * t / 12)
noise = np.random.normal(0, 2, n_obs)
passengers = 100 + trend + seasonal + noise

# Compute ACF and PACF
n_lags = 36
acf_values = acf(passengers, nlags=n_lags, fft=True)
pacf_values = pacf(passengers, nlags=n_lags, method="ywm")
conf_bound = 1.96 / np.sqrt(n_obs)

# Style
custom_style = Style(
    background="white",
    plot_background="#FAFAFA",
    foreground="#2C3E50",
    foreground_strong="#2C3E50",
    foreground_subtle="#ECECEC",
    colors=("#306998",),
    title_font_size=52,
    label_font_size=28,
    major_label_font_size=28,
    legend_font_size=24,
    value_font_size=20,
    font_family="sans-serif",
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    value_font_family="sans-serif",
)

highlight_color = "#306998"
muted_color = "#A8C4D8"
conf_line_color = "#E74C3C"

# Y-axis ranges tailored to actual data
acf_min, acf_max = -0.45, 1.05
pacf_min, pacf_max = -0.45, 0.95


def inject_confidence_lines(svg_bytes, conf_val, y_min, y_max):
    """Inject precise horizontal dashed confidence lines into pygal SVG.

    Parses the SVG to find the plot group's transform and background rect,
    then adds lines at exact data coordinates within the plot coordinate system.
    """
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    root = ET.fromstring(svg_bytes)
    ns = "http://www.w3.org/2000/svg"

    # Find <g class="plot"> group (lines are added in its local coordinate system)
    plot_group = None
    for g in root.iter(f"{{{ns}}}g"):
        if g.get("class", "") == "plot":
            plot_group = g
            break

    if plot_group is None:
        return svg_bytes

    # Find background rect inside the plot group for plot dimensions
    plot_w, plot_h = None, None
    for rect in plot_group.iter(f"{{{ns}}}rect"):
        if rect.get("class", "") == "background":
            plot_w = float(rect.get("width"))
            plot_h = float(rect.get("height"))
            break

    if plot_w is None:
        return svg_bytes

    # Calculate y pixel positions in the plot's local coordinate system
    y_range = y_max - y_min
    upper_y = (y_max - conf_val) / y_range * plot_h
    lower_y = (y_max + conf_val) / y_range * plot_h

    # Add lines inside the plot group for precise coordinate alignment
    for line_y in [upper_y, lower_y]:
        line_elem = ET.SubElement(plot_group, f"{{{ns}}}line")
        line_elem.set("x1", "0")
        line_elem.set("y1", f"{line_y:.1f}")
        line_elem.set("x2", str(plot_w))
        line_elem.set("y2", f"{line_y:.1f}")
        line_elem.set("stroke", conf_line_color)
        line_elem.set("stroke-width", "4")
        line_elem.set("stroke-dasharray", "24,14")
        line_elem.set("opacity", "0.9")

    return ET.tostring(root)


# ACF chart - with main title via pygal's native title parameter
acf_chart = pygal.Bar(
    width=4800,
    height=1350,
    style=custom_style,
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    x_title="",
    y_title="ACF",
    title="acf-pacf \u00b7 pygal \u00b7 pyplots.ai",
    margin=20,
    margin_bottom=10,
    margin_top=20,
    margin_left=100,
    margin_right=50,
    spacing=4,
    range=(acf_min, acf_max),
    truncate_label=-1,
    print_values=False,
    show_minor_x_labels=False,
    x_labels_major_every=5,
)

acf_lags = list(range(n_lags + 1))
acf_chart.x_labels = [str(i) for i in acf_lags]

acf_bar_data = []
for v in acf_values:
    color = highlight_color if abs(v) > conf_bound else muted_color
    acf_bar_data.append({"value": round(v, 4), "color": color})
acf_chart.add("ACF", acf_bar_data)

# PACF chart
pacf_chart = pygal.Bar(
    width=4800,
    height=1350,
    style=custom_style,
    show_legend=False,
    show_y_guides=True,
    show_x_guides=False,
    x_title="Lag",
    y_title="PACF",
    title="",
    margin=20,
    margin_bottom=60,
    margin_top=10,
    margin_left=100,
    margin_right=50,
    spacing=4,
    range=(pacf_min, pacf_max),
    truncate_label=-1,
    print_values=False,
    show_minor_x_labels=False,
    x_labels_major_every=5,
)

pacf_lags = list(range(1, n_lags + 1))
pacf_chart.x_labels = [str(i) for i in pacf_lags]

pacf_bar_data = []
for v in pacf_values[1:]:
    color = highlight_color if abs(v) > conf_bound else muted_color
    pacf_bar_data.append({"value": round(v, 4), "color": color})
pacf_chart.add("PACF", pacf_bar_data)

# Render SVGs, inject confidence lines, convert to PNG
acf_svg = acf_chart.render()
acf_svg_with_ci = inject_confidence_lines(acf_svg, conf_bound, acf_min, acf_max)
pacf_svg = pacf_chart.render()
pacf_svg_with_ci = inject_confidence_lines(pacf_svg, conf_bound, pacf_min, pacf_max)

# Convert modified SVGs to PNG via cairosvg (pygal's render engine)
acf_png = cairosvg.svg2png(bytestring=acf_svg_with_ci, output_width=4800, output_height=1350)
pacf_png = cairosvg.svg2png(bytestring=pacf_svg_with_ci, output_width=4800, output_height=1350)

# Stack the two charts vertically (minimal PIL usage - composition only)
acf_img = Image.open(io.BytesIO(acf_png))
pacf_img = Image.open(io.BytesIO(pacf_png))
combined = Image.new("RGB", (4800, 2700), "white")
combined.paste(acf_img, (0, 0))
combined.paste(pacf_img, (0, 1350))
combined.save("plot.png", dpi=(300, 300))

# HTML version with interactive SVGs
acf_svg_str = acf_chart.render(is_unicode=True).replace('<?xml version="1.0" encoding="utf-8"?>', "")
pacf_svg_str = pacf_chart.render(is_unicode=True).replace('<?xml version="1.0" encoding="utf-8"?>', "")

html_content = (
    "<!DOCTYPE html>\n<html>\n<head>\n"
    "    <title>acf-pacf · pygal · pyplots.ai</title>\n"
    "    <style>\n"
    "        body { font-family: sans-serif; background: white; margin: 0; padding: 20px; }\n"
    "        .container { max-width: 1200px; margin: 0 auto; }\n"
    "        .chart { width: 100%%; margin: 10px 0; }\n"
    "    </style>\n</head>\n<body>\n"
    "    <div class='container'>\n"
    "        <div class='chart'>" + acf_svg_str + "</div>\n"
    "        <div class='chart'>" + pacf_svg_str + "</div>\n"
    "    </div>\n</body>\n</html>"
)

with open("plot.html", "w") as f:
    f.write(html_content)

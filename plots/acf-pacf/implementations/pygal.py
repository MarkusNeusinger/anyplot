"""pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: pygal 3.1.0 | Python 3.14.3
"""

import io
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pygal
from PIL import Image, ImageDraw
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
highlight_color = "#306998"
muted_color = "#A8C4D8"
conf_line_color = "#C0392B"

custom_style = Style(
    background="white",
    plot_background="#F7F9FB",
    foreground="#2C3E50",
    foreground_strong="#2C3E50",
    foreground_subtle="#DEE2E6",
    colors=(highlight_color,),
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

# Y-axis ranges tailored to actual data
acf_min, acf_max = -0.45, 1.05
pacf_min, pacf_max = -0.45, 0.95

# Common chart config for narrower stem-like bars
common_config = {
    "width": 4800,
    "height": 1350,
    "style": custom_style,
    "show_legend": False,
    "show_y_guides": True,
    "show_x_guides": False,
    "margin": 20,
    "margin_left": 100,
    "margin_right": 50,
    "spacing": 30,
    "truncate_label": -1,
    "print_values": False,
    "show_minor_x_labels": False,
    "x_labels_major_every": 4,
}

# ACF chart
acf_chart = pygal.Bar(
    **common_config,
    x_title="",
    y_title="ACF",
    title="acf-pacf \u00b7 pygal \u00b7 pyplots.ai",
    margin_bottom=15,
    margin_top=20,
    range=(acf_min, acf_max),
)
acf_chart.x_labels = [str(i) for i in range(n_lags + 1)]
acf_chart.add(
    "ACF",
    [{"value": round(v, 4), "color": highlight_color if abs(v) > conf_bound else muted_color} for v in acf_values],
)

# PACF chart
pacf_chart = pygal.Bar(
    **common_config, x_title="Lag", y_title="PACF", title="", margin_bottom=60, margin_top=5, range=(pacf_min, pacf_max)
)
pacf_chart.x_labels = [str(i) for i in range(1, n_lags + 1)]
pacf_chart.add(
    "PACF",
    [{"value": round(v, 4), "color": highlight_color if abs(v) > conf_bound else muted_color} for v in pacf_values[1:]],
)

# Render SVGs and inject confidence lines inline (pygal has no native reference lines)
ns = "http://www.w3.org/2000/svg"
ET.register_namespace("", ns)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

charts_svg = [(acf_chart.render(), acf_min, acf_max), (pacf_chart.render(), pacf_min, pacf_max)]
png_images = []

for svg_bytes, y_min, y_max in charts_svg:
    root = ET.fromstring(svg_bytes)
    plot_group = next((g for g in root.iter(f"{{{ns}}}g") if g.get("class", "") == "plot"), None)
    if plot_group is not None:
        bg_rect = next((r for r in plot_group.iter(f"{{{ns}}}rect") if r.get("class", "") == "background"), None)
        if bg_rect is not None:
            pw, ph = float(bg_rect.get("width")), float(bg_rect.get("height"))
            y_range = y_max - y_min
            for cv in [conf_bound, -conf_bound]:
                ly = (y_max - cv) / y_range * ph
                line = ET.SubElement(plot_group, f"{{{ns}}}line")
                line.set("x1", "0")
                line.set("y1", f"{ly:.1f}")
                line.set("x2", str(pw))
                line.set("y2", f"{ly:.1f}")
                line.set("stroke", conf_line_color)
                line.set("stroke-width", "3.5")
                line.set("stroke-dasharray", "20,12")
                line.set("opacity", "0.85")

    modified_svg = ET.tostring(root)
    png_images.append(cairosvg.svg2png(bytestring=modified_svg, output_width=4800, output_height=1350))

# Compose final image with seamless stacking
acf_img = Image.open(io.BytesIO(png_images[0]))
pacf_img = Image.open(io.BytesIO(png_images[1]))
combined = Image.new("RGB", (4800, 2700), "white")
combined.paste(acf_img, (0, 0))
combined.paste(pacf_img, (0, 1350))

# Draw subtle divider line between charts to create clean visual separation
draw = ImageDraw.Draw(combined)
draw.line([(100, 1350), (4750, 1350)], fill="#DEE2E6", width=2)

combined.save("plot.png", dpi=(300, 300))

# HTML version with interactive SVGs
acf_svg_str = acf_chart.render(is_unicode=True).replace('<?xml version="1.0" encoding="utf-8"?>', "")
pacf_svg_str = pacf_chart.render(is_unicode=True).replace('<?xml version="1.0" encoding="utf-8"?>', "")

html_content = (
    "<!DOCTYPE html>\n<html>\n<head>\n"
    "    <title>acf-pacf \u00b7 pygal \u00b7 pyplots.ai</title>\n"
    "    <style>\n"
    "        body { font-family: sans-serif; background: white; margin: 0; padding: 20px; }\n"
    "        .container { max-width: 1200px; margin: 0 auto; }\n"
    "        .chart { width: 100%; margin: 10px 0; }\n"
    "    </style>\n</head>\n<body>\n"
    "    <div class='container'>\n"
    "        <div class='chart'>" + acf_svg_str + "</div>\n"
    "        <div class='chart'>" + pacf_svg_str + "</div>\n"
    "    </div>\n</body>\n</html>"
)

with open("plot.html", "w") as f:
    f.write(html_content)

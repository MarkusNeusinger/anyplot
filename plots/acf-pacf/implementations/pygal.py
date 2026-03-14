""" pyplots.ai
acf-pacf: Autocorrelation and Partial Autocorrelation (ACF/PACF) Plot
Library: pygal 3.1.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-14
"""

import io
import xml.etree.ElementTree as ET

import cairosvg
import numpy as np
import pygal
from PIL import Image, ImageDraw, ImageFont
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

# Color palette - refined for publication quality
highlight_color = "#306998"
muted_color = "#B8D4E8"
conf_line_color = "#C0392B"
bg_color = "#FAFAFA"
text_color = "#1A1A2E"
grid_color = "#E8ECF0"
zero_line_color = "#95A5A6"

custom_style = Style(
    background="white",
    plot_background=bg_color,
    foreground=text_color,
    foreground_strong=text_color,
    foreground_subtle=grid_color,
    colors=(highlight_color,),
    title_font_size=48,
    label_font_size=30,
    major_label_font_size=30,
    legend_font_size=24,
    value_font_size=18,
    font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    title_font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    label_font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    value_font_family="'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
)

# Y-axis ranges tailored to actual data with slight padding
acf_min, acf_max = -0.5, 1.1
pacf_min, pacf_max = -0.5, 1.0

# Common chart config - high spacing for narrow stem-like bars
common_config = {
    "width": 4800,
    "height": 1300,
    "style": custom_style,
    "show_legend": False,
    "show_y_guides": True,
    "show_x_guides": False,
    "margin": 25,
    "margin_left": 120,
    "margin_right": 60,
    "spacing": 100,
    "truncate_label": -1,
    "print_values": False,
    "show_minor_x_labels": False,
    "x_labels_major_every": 4,
    "rounded_bars": 2,
    "y_labels_major_count": 5,
}

# ACF chart
acf_chart = pygal.Bar(
    **common_config,
    x_title="",
    y_title="ACF",
    title="acf-pacf · pygal · pyplots.ai",
    margin_bottom=10,
    margin_top=30,
    range=(acf_min, acf_max),
)
acf_chart.x_labels = [str(i) for i in range(n_lags + 1)]
acf_chart.add(
    "ACF",
    [{"value": round(v, 4), "color": highlight_color if abs(v) > conf_bound else muted_color} for v in acf_values],
)

# PACF chart
pacf_chart = pygal.Bar(
    **common_config, x_title="Lag", y_title="PACF", title="", margin_bottom=70, margin_top=5, range=(pacf_min, pacf_max)
)
pacf_chart.x_labels = [str(i) for i in range(1, n_lags + 1)]
pacf_chart.add(
    "PACF",
    [{"value": round(v, 4), "color": highlight_color if abs(v) > conf_bound else muted_color} for v in pacf_values[1:]],
)

# Render SVGs and inject confidence lines (pygal lacks native reference lines)
ns = "http://www.w3.org/2000/svg"
ET.register_namespace("", ns)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

png_images = []
for chart, y_min, y_max in [(acf_chart, acf_min, acf_max), (pacf_chart, pacf_min, pacf_max)]:
    root = ET.fromstring(chart.render())
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
                line.set("stroke-width", "3")
                line.set("stroke-dasharray", "18,10")
                line.set("opacity", "0.75")
            # Zero baseline emphasis
            zy = (y_max - 0) / y_range * ph
            zline = ET.SubElement(plot_group, f"{{{ns}}}line")
            zline.set("x1", "0")
            zline.set("y1", f"{zy:.1f}")
            zline.set("x2", str(pw))
            zline.set("y2", f"{zy:.1f}")
            zline.set("stroke", zero_line_color)
            zline.set("stroke-width", "2.5")
            zline.set("opacity", "0.6")

    png_images.append(cairosvg.svg2png(bytestring=ET.tostring(root), output_width=4800, output_height=1300))

# Compose final image
acf_img = Image.open(io.BytesIO(png_images[0]))
pacf_img = Image.open(io.BytesIO(png_images[1]))
combined = Image.new("RGB", (4800, 2700), "white")
combined.paste(acf_img, (0, 50))
combined.paste(pacf_img, (0, 1350))

# Subtle divider line between charts
draw = ImageDraw.Draw(combined)
draw.line([(120, 1350), (4740, 1350)], fill="#DEE2E6", width=2)

# Confidence bound annotation - positioned in upper-right margin area
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
except OSError:
    font = ImageFont.load_default()
draw.text((4200, 68), f"95% CI: ±{conf_bound:.3f}", fill=conf_line_color, font=font)

combined.save("plot.png", dpi=(300, 300))

# HTML version with interactive SVGs
acf_svg = acf_chart.render(is_unicode=True).replace('<?xml version="1.0" encoding="utf-8"?>', "")
pacf_svg = pacf_chart.render(is_unicode=True).replace('<?xml version="1.0" encoding="utf-8"?>', "")

html_content = (
    "<!DOCTYPE html>\n<html>\n<head>\n"
    "    <title>acf-pacf · pygal · pyplots.ai</title>\n"
    "    <style>\n"
    "        body { font-family: 'Helvetica Neue', sans-serif; background: white; margin: 0; padding: 20px; }\n"
    "        .container { max-width: 1200px; margin: 0 auto; }\n"
    "        .chart { width: 100%; margin: 10px 0; }\n"
    "    </style>\n</head>\n<body>\n"
    "    <div class='container'>\n"
    f"        <div class='chart'>{acf_svg}</div>\n"
    f"        <div class='chart'>{pacf_svg}</div>\n"
    "    </div>\n</body>\n</html>"
)

with open("plot.html", "w") as f:
    f.write(html_content)

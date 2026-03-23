""" pyplots.ai
titration-curve: Acid-Base Titration Curve
Library: pygal 3.1.0 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-21
"""

import io

import cairosvg
import numpy as np
import pygal
from PIL import Image, ImageDraw, ImageFont
from pygal.style import Style


# Data — 25 mL of 0.1 M HCl titrated with 0.1 M NaOH
ca, va = 0.1, 25.0
cb = 0.1
equivalence_vol = va * ca / cb  # 25 mL

volume_ml = np.linspace(0.01, 50.0, 500)

ph = np.empty_like(volume_ml)
for i, v in enumerate(volume_ml):
    moles_h = ca * va - cb * v
    total_vol = va + v
    if moles_h > 1e-10:
        ph[i] = -np.log10(moles_h / total_vol)
    elif moles_h < -1e-10:
        oh_conc = -moles_h / total_vol
        ph[i] = 14.0 + np.log10(oh_conc)
    else:
        ph[i] = 7.0

# Derivative dpH/dV
dpH_dV = np.gradient(ph, volume_ml)
dpH_dV = np.clip(dpH_dV, 0, None)

# Equivalence point — known analytically for strong acid/strong base
eq_vol = equivalence_vol  # 25.0 mL
eq_ph = 7.0

# Colors
line_blue = "#306998"
deriv_orange = "#D35400"
eq_red = "#C0392B"
bg_canvas = "#FAFCFF"
bg_plot = "#F0F4F8"
text_dark = "#1A1F36"
grid_subtle = "#D5DAE2"
buffer_fill = "#306998"  # semi-transparent blue for buffer/transition zone

# Shared style settings
_style_common = {
    "background": bg_canvas,
    "plot_background": bg_plot,
    "foreground": text_dark,
    "foreground_strong": text_dark,
    "foreground_subtle": "#E2E6EA",
    "title_font_size": 56,
    "label_font_size": 34,
    "major_label_font_size": 32,
    "legend_font_size": 40,
    "value_font_size": 22,
    "stroke_width": 4,
    "font_family": "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    "title_font_family": "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    "label_font_family": "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    "value_font_family": "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    "legend_font_family": "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif",
    "opacity": 1.0,
    "opacity_hover": 0.85,
}

ph_style = Style(**_style_common, colors=(line_blue, eq_red, "#7F8C8D"))
deriv_style = Style(**_style_common, colors=(deriv_orange, eq_red))

# Subsample for performance
step = 3
curve_pts = [(float(volume_ml[i]), float(ph[i])) for i in range(0, len(volume_ml), step)]
deriv_pts = [(float(volume_ml[i]), float(dpH_dV[i])) for i in range(0, len(volume_ml), step)]

# Equivalence point vertical dashed line (for both panels)
eq_line_ph = [(float(eq_vol), 0.0), (float(eq_vol), 14.0)]

# pH 7 reference line
ref_ph7 = [(0.0, 7.0), (50.0, 7.0)]

# pH chart (upper panel)
ph_chart = pygal.XY(
    style=ph_style,
    width=4800,
    height=1800,
    title="titration-curve · pygal · pyplots.ai",
    x_title="Volume of NaOH added (mL)",
    y_title="pH",
    show_dots=False,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=True,
    range=(0.0, 14.0),
    xrange=(0.0, 50.0),
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=30,
    truncate_legend=-1,
    margin=30,
    margin_top=80,
    margin_left=160,
    margin_right=90,
    margin_bottom=140,
    tooltip_fancy_mode=True,
    tooltip_border_radius=8,
    x_value_formatter=lambda x: f"{x:.1f}",
    y_value_formatter=lambda y: f"{y:.1f}",
)

ph_chart.add(
    "pH (0.1 M HCl + 0.1 M NaOH)",
    curve_pts,
    show_dots=False,
    stroke_style={"width": 6, "linecap": "round", "linejoin": "round"},
)

ph_chart.add(
    f"Equivalence Point ({eq_vol:.1f} mL, pH {eq_ph:.1f})",
    eq_line_ph,
    show_dots=True,
    dots_size=8,
    stroke_style={"width": 3, "dasharray": "14,8"},
)

ph_chart.add("pH 7 Reference", ref_ph7, show_dots=False, stroke_style={"width": 2, "dasharray": "6,6"})

# Derivative chart (lower panel)
eq_line_deriv = [(float(eq_vol), 0.0), (float(eq_vol), float(np.max(dpH_dV) * 1.05))]

deriv_chart = pygal.XY(
    style=deriv_style,
    width=4800,
    height=900,
    title="",
    x_title="Volume of NaOH added (mL)",
    y_title="dpH/dV",
    show_dots=False,
    dots_size=0,
    show_x_guides=False,
    show_y_guides=True,
    xrange=(0.0, 50.0),
    legend_at_bottom=True,
    legend_at_bottom_columns=2,
    legend_box_size=30,
    truncate_legend=-1,
    margin=30,
    margin_top=20,
    margin_left=160,
    margin_right=90,
    margin_bottom=140,
    tooltip_fancy_mode=True,
    tooltip_border_radius=8,
    x_value_formatter=lambda x: f"{x:.1f}",
    y_value_formatter=lambda y: f"{y:.2f}",
)

deriv_chart.add(
    "dpH/dV (derivative)",
    deriv_pts,
    show_dots=False,
    stroke_style={"width": 5, "linecap": "round", "linejoin": "round"},
)

deriv_chart.add(
    f"Equivalence ({eq_vol:.1f} mL)",
    eq_line_deriv,
    show_dots=True,
    dots_size=8,
    stroke_style={"width": 3, "dasharray": "14,8"},
)

# Render to PNG and compose
ph_png = cairosvg.svg2png(bytestring=ph_chart.render(), output_width=4800, output_height=1800)
deriv_png = cairosvg.svg2png(bytestring=deriv_chart.render(), output_width=4800, output_height=900)

ph_img = Image.open(io.BytesIO(ph_png))
deriv_img = Image.open(io.BytesIO(deriv_png))
combined = Image.new("RGB", (4800, 2700), bg_canvas)
combined.paste(ph_img, (0, 0))
combined.paste(deriv_img, (0, 1800))

# Buffer/transition zone shading on the pH panel
# For strong acid/strong base: shade the steep transition zone (~20-30 mL)
# Map data coordinates to pixel coordinates on the pH panel
# pH panel plot area approx: x from ~320 to ~4710, y from ~150 to ~1580
plot_x_left, plot_x_right = 320, 4710
plot_y_top, plot_y_bottom = 150, 1580
x_data_min, x_data_max = 0.0, 50.0
y_data_min, y_data_max = 0.0, 14.0


def data_to_px(vx, vy):
    px = plot_x_left + (vx - x_data_min) / (x_data_max - x_data_min) * (plot_x_right - plot_x_left)
    py = plot_y_bottom - (vy - y_data_min) / (y_data_max - y_data_min) * (plot_y_bottom - plot_y_top)
    return int(px), int(py)


# Draw semi-transparent buffer zone overlay
buffer_overlay = Image.new("RGBA", (4800, 2700), (0, 0, 0, 0))
buf_draw = ImageDraw.Draw(buffer_overlay)

# Transition zone: 20-30 mL (the steep part of the S-curve)
buf_x1, _ = data_to_px(20.0, 0)
buf_x2, _ = data_to_px(30.0, 0)
_, buf_y1 = data_to_px(0, 14.0)
_, buf_y2 = data_to_px(0, 0.0)
buf_draw.rectangle([(buf_x1, buf_y1), (buf_x2, buf_y2)], fill=(48, 105, 152, 28))

# Label the shaded zone
try:
    font_zone = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
except OSError:
    font_zone = ImageFont.load_default()
_, label_y = data_to_px(0, 3.0)
buf_draw.text((buf_x1 + 16, label_y), "Transition\nZone", fill=(48, 105, 152, 160), font=font_zone)

combined = Image.alpha_composite(combined.convert("RGBA"), buffer_overlay).convert("RGB")

# Panel divider
draw = ImageDraw.Draw(combined)
draw.line([(160, 1800), (4710, 1800)], fill="#B0BEC5", width=2)

# Annotation overlay
try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
    font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
except OSError:
    font_title = ImageFont.load_default()
    font_body = font_title

ann_x, ann_y = 3200, 120
ann_w, ann_h = 1500, 160
draw.rounded_rectangle(
    [(ann_x, ann_y), (ann_x + ann_w, ann_y + ann_h)], radius=16, fill="#FFFFFF", outline=grid_subtle, width=2
)
draw.text((ann_x + 24, ann_y + 18), f"Equivalence: {eq_vol:.1f} mL, pH {eq_ph:.1f}", fill=eq_red, font=font_title)
draw.text((ann_x + 24, ann_y + 80), "25 mL of 0.1 M HCl titrated with 0.1 M NaOH", fill="#5D6D7E", font=font_body)

combined.save("plot.png", dpi=(300, 300))

# HTML version with interactive SVG
ph_svg = ph_chart.render(is_unicode=True).replace('<?xml version="1.0" encoding="utf-8"?>', "")
deriv_svg = deriv_chart.render(is_unicode=True).replace('<?xml version="1.0" encoding="utf-8"?>', "")

html_content = (
    "<!DOCTYPE html>\n<html>\n<head>\n"
    "    <title>titration-curve · pygal · pyplots.ai</title>\n"
    "    <style>\n"
    f"        body {{ font-family: 'Helvetica Neue', sans-serif; background: {bg_canvas};"
    " margin: 0; padding: 40px 20px; }\n"
    "        .container { max-width: 1200px; margin: 0 auto; }\n"
    "        .chart { width: 100%; margin: 8px 0; }\n"
    "        .divider { border: none; border-top: 1px solid #CFD8DC; margin: 0; }\n"
    "        .info { text-align: center; color: #5D6D7E; font-size: 14px; margin-top: 12px; }\n"
    "    </style>\n</head>\n<body>\n"
    "    <div class='container'>\n"
    f"        <div class='chart'>{ph_svg}</div>\n"
    "        <hr class='divider'/>\n"
    f"        <div class='chart'>{deriv_svg}</div>\n"
    "        <p class='info'>Hover over data points for pH and volume details</p>\n"
    "    </div>\n</body>\n</html>"
)

with open("plot.html", "w") as f:
    f.write(html_content)

""" pyplots.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: pygal 3.1.0 | Python 3.14.3
Quality: 77/100 | Created: 2026-03-20
"""

import re

import cairosvg
import pygal
from pygal.style import Style


# Data — Manufacturing defect analysis (sorted descending by count)
categories = ["Scratches", "Dents", "Misalignment", "Cracks", "Discoloration", "Warping", "Contamination", "Burrs"]
counts = [142, 98, 84, 56, 42, 31, 18, 9]

# Cumulative percentages
total = sum(counts)
cumulative_pct = []
running = 0
for c in counts:
    running += c
    cumulative_pct.append(round(running / total * 100, 1))

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#2C3E50",
    foreground_strong="#2C3E50",
    foreground_subtle="#E8E8E8",
    colors=("#306998",),
    title_font_size=52,
    label_font_size=32,
    major_label_font_size=32,
    value_font_size=28,
    value_label_font_size=28,
    legend_font_size=32,
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    value_font_family="sans-serif",
)

# Bar chart with generous right margin for secondary y-axis
chart = pygal.Bar(
    width=4800,
    height=2700,
    title="bar-pareto · pygal · pyplots.ai",
    x_title="Defect Type",
    y_title="Frequency",
    style=custom_style,
    show_legend=False,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: f"{x:,.0f}",
    show_y_guides=True,
    show_x_guides=False,
    margin=20,
    margin_bottom=100,
    margin_left=120,
    margin_right=380,
    spacing=18,
    rounded_bars=4,
    truncate_label=-1,
    x_label_rotation=20,
    js=[],
)

chart.x_labels = categories
chart.add("Defect Count", counts)

# Render SVG
svg_str = chart.render().decode("utf-8")

# Extract bar rect positions
bar_pattern = r'<rect\s[^>]*class="rect reactive tooltip-trigger"[^>]*/>'
bar_matches = re.findall(bar_pattern, svg_str)

bar_centers_x = []
bar_tops_y = []
bar_bottoms_y = []

for bar_svg in bar_matches:
    x_m = re.search(r'\bx="([^"]+)"', bar_svg)
    y_m = re.search(r'\by="([^"]+)"', bar_svg)
    w_m = re.search(r'\bwidth="([^"]+)"', bar_svg)
    h_m = re.search(r'\bheight="([^"]+)"', bar_svg)
    if x_m and y_m and w_m and h_m:
        x = float(x_m.group(1))
        y = float(y_m.group(1))
        w = float(w_m.group(1))
        h = float(h_m.group(1))
        bar_centers_x.append(x + w / 2)
        bar_tops_y.append(y)
        bar_bottoms_y.append(y + h)

# Compute coordinate mapping from bar data
y_base = max(bar_bottoms_y)
pixels_per_count = (y_base - min(bar_tops_y)) / max(counts)

# Find the highest y-axis label value from SVG text elements
y_label_values = [int(m) for m in re.findall(r"<text[^>]*>(\d+)</text>", svg_str)]
y_axis_max = max(v for v in y_label_values if v <= 200) if y_label_values else 140

# Plot area top corresponds to y_axis_max on the count scale
y_plot_top = y_base - pixels_per_count * y_axis_max

# Map cumulative 0-100% to the full plot area height
plot_height = y_base - y_plot_top
cum_points = []
for i, pct in enumerate(cumulative_pct):
    cx = bar_centers_x[i]
    cy = y_base - (pct / 100.0) * plot_height
    cum_points.append((cx, cy))

# Build cumulative line SVG
points_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in cum_points)
line_color = "#C0392B"

cumulative_svg = f'''
<g id="cumulative-overlay">
  <polyline points="{points_str}"
    fill="none" stroke="{line_color}" stroke-width="5"
    stroke-linecap="round" stroke-linejoin="round" />
'''

# Dots and labels at each data point
for i, (cx, cy) in enumerate(cum_points):
    pct_val = cumulative_pct[i]
    lx = cx + 16
    ly = cy - 16
    anchor = "start"
    # Last two points: put label to the left to avoid right-edge clipping
    if i >= len(cum_points) - 2:
        lx = cx - 16
        anchor = "end"
    cumulative_svg += f'''
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="9"
    fill="{line_color}" stroke="white" stroke-width="2.5" />
  <text x="{lx:.1f}" y="{ly:.1f}"
    text-anchor="{anchor}" fill="{line_color}"
    font-size="26" font-family="sans-serif" font-weight="bold">{pct_val:.0f}%</text>
'''

cumulative_svg += "</g>"

# 80% reference line
y_80 = y_base - 0.80 * plot_height
x_left = bar_centers_x[0] - 60
x_right = bar_centers_x[-1] + 60

ref_line_svg = f'''
<g id="reference-80">
  <line x1="{x_left:.1f}" y1="{y_80:.1f}" x2="{x_right:.1f}" y2="{y_80:.1f}"
    stroke="#999999" stroke-width="3" stroke-dasharray="18,10" />
</g>
'''

# Secondary y-axis on the right
right_edge = bar_centers_x[-1] + 80
sec_axis_svg = '<g id="secondary-y-axis">'

for pct in [0, 20, 40, 60, 80, 100]:
    y_pos = y_base - (pct / 100.0) * plot_height
    sec_axis_svg += f'''
  <line x1="{right_edge:.1f}" y1="{y_pos:.1f}"
    x2="{right_edge + 8:.1f}" y2="{y_pos:.1f}"
    stroke="{line_color}" stroke-width="2" />
  <text x="{right_edge + 16:.1f}" y="{y_pos + 9:.1f}"
    fill="{line_color}" font-size="28" font-family="sans-serif"
    text-anchor="start">{pct}%</text>
'''

# Vertical axis line
sec_axis_svg += f'''
  <line x1="{right_edge:.1f}" y1="{y_base:.1f}"
    x2="{right_edge:.1f}" y2="{y_plot_top:.1f}"
    stroke="{line_color}" stroke-width="2" />
'''

# Rotated axis title
mid_y = (y_base + y_plot_top) / 2
title_x = right_edge + 100
sec_axis_svg += f'''
  <text x="{title_x:.1f}" y="{mid_y:.1f}"
    fill="{line_color}" font-size="32" font-family="sans-serif"
    text-anchor="middle"
    transform="rotate(-90, {title_x:.1f}, {mid_y:.1f})">Cumulative %</text>
'''
sec_axis_svg += "</g>"

# Legend centered below the plot area
legend_cx = (bar_centers_x[0] + bar_centers_x[-1]) / 2
legend_y = y_base + 78

legend_svg = f'''
<g id="pareto-legend">
  <rect x="{legend_cx - 340:.1f}" y="{legend_y - 13:.1f}"
    width="26" height="26" rx="3" fill="#306998" />
  <text x="{legend_cx - 306:.1f}" y="{legend_y + 9:.1f}"
    fill="#2C3E50" font-size="28" font-family="sans-serif">Defect Count</text>

  <line x1="{legend_cx - 80:.1f}" y1="{legend_y:.1f}"
    x2="{legend_cx - 36:.1f}" y2="{legend_y:.1f}"
    stroke="{line_color}" stroke-width="4" />
  <circle cx="{legend_cx - 58:.1f}" cy="{legend_y:.1f}" r="6"
    fill="{line_color}" stroke="white" stroke-width="1.5" />
  <text x="{legend_cx - 24:.1f}" y="{legend_y + 9:.1f}"
    fill="#2C3E50" font-size="28" font-family="sans-serif">Cumulative %</text>

  <line x1="{legend_cx + 180:.1f}" y1="{legend_y:.1f}"
    x2="{legend_cx + 224:.1f}" y2="{legend_y:.1f}"
    stroke="#999999" stroke-width="3" stroke-dasharray="10,6" />
  <text x="{legend_cx + 236:.1f}" y="{legend_y + 9:.1f}"
    fill="#2C3E50" font-size="28" font-family="sans-serif">80% Threshold</text>
</g>
'''

# Inject SVG elements
injection = cumulative_svg + ref_line_svg + sec_axis_svg + legend_svg
svg_str = svg_str.replace("</svg>", injection + "\n</svg>")

# Save
cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), write_to="plot.png", output_width=4800, output_height=2700)
chart.render_to_file("plot.html")

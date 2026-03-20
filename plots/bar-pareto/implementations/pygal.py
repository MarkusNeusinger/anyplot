"""pyplots.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: pygal 3.1.0 | Python 3.14.3
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

# 80% threshold boundary — bars in the "vital few" (cumulative ≤ 80%)
vital_few_count = sum(1 for p in cumulative_pct if p <= 80.0)

# Colors
color_vital = "#306998"
color_trivial = "#93B5CF"
line_color = "#C0392B"
threshold_color = "#7F8C8D"

custom_style = Style(
    background="white",
    plot_background="#FAFBFC",
    foreground="#2C3E50",
    foreground_strong="#2C3E50",
    foreground_subtle="#E0E0E0",
    colors=(color_vital,),
    title_font_size=52,
    label_font_size=30,
    major_label_font_size=30,
    value_font_size=26,
    value_label_font_size=26,
    legend_font_size=30,
    title_font_family="sans-serif",
    label_font_family="sans-serif",
    value_font_family="sans-serif",
)

chart = pygal.Bar(
    width=4800,
    height=2700,
    title="bar-pareto · pygal · pyplots.ai",
    x_title="Defect Type",
    y_title="Frequency (Count)",
    style=custom_style,
    show_legend=False,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: f"{x:,.0f}",
    show_y_guides=True,
    show_x_guides=False,
    margin=20,
    margin_bottom=120,
    margin_left=120,
    margin_right=380,
    spacing=18,
    rounded_bars=6,
    truncate_label=-1,
    x_label_rotation=15,
    js=[],
)

chart.x_labels = categories
chart.add("Defect Count", counts)

# Render SVG
svg_str = chart.render().decode("utf-8")

# Recolor trivial-many bars by adding inline style override to CSS class colors
bar_rects = list(re.finditer(r'<rect\s[^>]*class="rect reactive tooltip-trigger"[^>]*/>', svg_str))
# Process in reverse order to preserve string positions
for i in reversed(range(len(bar_rects))):
    if i >= vital_few_count:
        m = bar_rects[i]
        old_rect = m.group(0)
        new_rect = old_rect.replace(
            'class="rect reactive tooltip-trigger"',
            f'class="rect reactive tooltip-trigger" style="fill:{color_trivial};stroke:{color_trivial}"',
        )
        svg_str = svg_str[: m.start()] + new_rect + svg_str[m.end() :]

# Extract bar rect positions for overlay placement
bar_matches_pos = re.findall(r'<rect\s[^>]*class="rect reactive tooltip-trigger"[^>]*/>', svg_str)

bar_centers_x = []
bar_tops_y = []
bar_bottoms_y = []

for bar_svg in bar_matches_pos:
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

# Coordinate mapping from bar geometry
y_base = max(bar_bottoms_y)
pixels_per_count = (y_base - min(bar_tops_y)) / max(counts)

# Find highest y-axis value to determine plot top
y_label_values = [int(m) for m in re.findall(r"<text[^>]*>(\d+)</text>", svg_str)]
y_axis_max = max(v for v in y_label_values if v <= 200) if y_label_values else 140

y_plot_top = y_base - pixels_per_count * y_axis_max
plot_height = y_base - y_plot_top

# Map cumulative percentages to pixel coordinates
cum_points = []
for i, pct in enumerate(cumulative_pct):
    cx = bar_centers_x[i]
    cy = y_base - (pct / 100.0) * plot_height
    cum_points.append((cx, cy))

# 80% reference line
y_80 = y_base - 0.80 * plot_height
x_left = bar_centers_x[0] - 80
x_right = bar_centers_x[-1] + 80

ref_line_svg = f'''
<g id="reference-80">
  <line x1="{x_left:.1f}" y1="{y_80:.1f}" x2="{x_right:.1f}" y2="{y_80:.1f}"
    stroke="{threshold_color}" stroke-width="3" stroke-dasharray="18,10"
    opacity="0.6" />
</g>
'''

# Cumulative line with dots
points_str = " ".join(f"{x:.1f},{y:.1f}" for x, y in cum_points)

cumulative_svg = f'''
<g id="cumulative-overlay">
  <polyline points="{points_str}"
    fill="none" stroke="{line_color}" stroke-width="5"
    stroke-linecap="round" stroke-linejoin="round" />
'''

for i, (cx, cy) in enumerate(cum_points):
    pct_val = cumulative_pct[i]
    bar_top = bar_tops_y[i]
    # Default: label to the right of dot, above
    lx = cx + 22
    ly = cy - 24
    anchor = "start"
    # If cumulative dot is near bar top, push label well above both
    if abs(cy - bar_top) < 60:
        ly = min(cy - 44, bar_top - 34)
    # Last two: label to the left to avoid right-edge clipping
    if i >= len(cum_points) - 2:
        lx = cx - 22
        anchor = "end"
    # First point: place below-left to avoid "142" value label at bar top
    if i == 0:
        lx = cx - 24
        ly = cy + 38
        anchor = "end"
    # Second point: offset further right to avoid "98" value label
    if i == 1:
        lx = cx + 28
        ly = cy - 28
    cumulative_svg += f'''
  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="10"
    fill="{line_color}" stroke="white" stroke-width="3" />
  <text x="{lx:.1f}" y="{ly:.1f}"
    text-anchor="{anchor}" fill="{line_color}"
    font-size="26" font-family="sans-serif" font-weight="bold">{pct_val:.0f}%</text>
'''

cumulative_svg += "</g>"

# Secondary y-axis on the right
right_edge = bar_centers_x[-1] + 80
sec_axis_svg = '<g id="secondary-y-axis">'

for pct in [0, 20, 40, 60, 80, 100]:
    y_pos = y_base - (pct / 100.0) * plot_height
    sec_axis_svg += f'''
  <line x1="{right_edge:.1f}" y1="{y_pos:.1f}"
    x2="{right_edge + 10:.1f}" y2="{y_pos:.1f}"
    stroke="{line_color}" stroke-width="2" />
  <text x="{right_edge + 18:.1f}" y="{y_pos + 10:.1f}"
    fill="{line_color}" font-size="28" font-family="sans-serif"
    text-anchor="start">{pct}%</text>
'''

sec_axis_svg += f'''
  <line x1="{right_edge:.1f}" y1="{y_base:.1f}"
    x2="{right_edge:.1f}" y2="{y_plot_top:.1f}"
    stroke="{line_color}" stroke-width="2" />
'''

mid_y = (y_base + y_plot_top) / 2
title_x = right_edge + 108
sec_axis_svg += f'''
  <text x="{title_x:.1f}" y="{mid_y:.1f}"
    fill="{line_color}" font-size="32" font-family="sans-serif"
    text-anchor="middle"
    transform="rotate(-90, {title_x:.1f}, {mid_y:.1f})">Cumulative %</text>
'''
sec_axis_svg += "</g>"

# Legend centered below the plot area
legend_cx = (bar_centers_x[0] + bar_centers_x[-1]) / 2
legend_y = y_base + 90

legend_svg = f'''
<g id="pareto-legend">
  <rect x="{legend_cx - 480:.1f}" y="{legend_y - 13:.1f}"
    width="26" height="26" rx="4" fill="{color_vital}" />
  <text x="{legend_cx - 446:.1f}" y="{legend_y + 9:.1f}"
    fill="#2C3E50" font-size="28" font-family="sans-serif">Vital Few</text>

  <rect x="{legend_cx - 280:.1f}" y="{legend_y - 13:.1f}"
    width="26" height="26" rx="4" fill="{color_trivial}" />
  <text x="{legend_cx - 246:.1f}" y="{legend_y + 9:.1f}"
    fill="#2C3E50" font-size="28" font-family="sans-serif">Trivial Many</text>

  <line x1="{legend_cx - 30:.1f}" y1="{legend_y:.1f}"
    x2="{legend_cx + 14:.1f}" y2="{legend_y:.1f}"
    stroke="{line_color}" stroke-width="4" />
  <circle cx="{legend_cx - 8:.1f}" cy="{legend_y:.1f}" r="6"
    fill="{line_color}" stroke="white" stroke-width="1.5" />
  <text x="{legend_cx + 26:.1f}" y="{legend_y + 9:.1f}"
    fill="#2C3E50" font-size="28" font-family="sans-serif">Cumulative %</text>

  <line x1="{legend_cx + 230:.1f}" y1="{legend_y:.1f}"
    x2="{legend_cx + 274:.1f}" y2="{legend_y:.1f}"
    stroke="{threshold_color}" stroke-width="3" stroke-dasharray="10,6" />
  <text x="{legend_cx + 286:.1f}" y="{legend_y + 9:.1f}"
    fill="#2C3E50" font-size="28" font-family="sans-serif">80% Threshold</text>
</g>
'''

# Inject all SVG overlays
injection = ref_line_svg + cumulative_svg + sec_axis_svg + legend_svg
svg_str = svg_str.replace("</svg>", injection + "\n</svg>")

# Save
cairosvg.svg2png(bytestring=svg_str.encode("utf-8"), write_to="plot.png", output_width=4800, output_height=2700)
chart.render_to_file("plot.html")

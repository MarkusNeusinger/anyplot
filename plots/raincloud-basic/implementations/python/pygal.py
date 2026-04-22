""" pyplots.ai
raincloud-basic: Basic Raincloud Plot
Library: pygal 3.1.0 | Python 3.14
Quality: 85/100 | Created: 2025-12-25
"""

import re

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data - Reaction times (ms) for different treatment groups
np.random.seed(42)
data = {
    "Control": np.concatenate([np.random.normal(450, 80, 60), [650, 680, 250]]),
    "Treatment A": np.concatenate([np.random.normal(380, 60, 55), [550, 200]]),
    "Treatment B": np.concatenate([np.random.normal(320, 50, 50), [480, 180]]),
}

# Colorblind-safe palette
group_colors = ["#306998", "#FFD43B", "#4CAF50"]

# Build color sequence: per group = rain, box_outline, median_line
series_colors = []
for gc in group_colors:
    series_colors.extend([gc, gc, gc])

custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#aaaaaa",
    guide_stroke_color="#e0e0e0",
    guide_stroke_dasharray="4,4",
    colors=tuple(series_colors),
    title_font_size=84,
    label_font_size=54,
    major_label_font_size=48,
    legend_font_size=48,
    value_font_size=40,
    tooltip_font_size=36,
    opacity=0.60,
    opacity_hover=0.85,
)

# Compute global data range for tighter x-axis
all_vals = np.concatenate(list(data.values()))
x_lo = max(100, int(all_vals.min() - 30))
x_hi = int(all_vals.max() + 30)

chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="raincloud-basic · pygal · pyplots.ai",
    x_title="Reaction Time (ms)",
    y_title="Treatment Group",
    show_legend=False,
    stroke=True,
    fill=False,
    dots_size=0,
    show_x_guides=True,
    show_y_guides=False,
    xrange=(x_lo, x_hi),
    range=(-0.2, 4.2),
    margin=40,
    margin_left=340,
    margin_right=100,
    margin_top=120,
    margin_bottom=120,
    explicit_size=True,
)

# Raincloud layout parameters
cloud_height = 0.32
rain_offset = -0.35
n_kde_points = 80
box_hw = 0.14

# Store cloud and box data for SVG injection
cloud_polygons = []
box_rects = []
medians = {}

for i, (category, values) in enumerate(data.items()):
    center_y = i + 1
    values = np.array(values)

    # Half-Violin KDE (cloud) - Silverman bandwidth
    n = len(values)
    std = np.std(values)
    iqr_val = np.percentile(values, 75) - np.percentile(values, 25)
    bandwidth = 0.9 * min(std, iqr_val / 1.34) * n ** (-0.2)

    x_min, x_max = values.min(), values.max()
    padding = (x_max - x_min) * 0.08
    x_kde = np.linspace(x_min - padding, x_max + padding, n_kde_points)

    density = np.zeros_like(x_kde)
    for v in values:
        density += np.exp(-0.5 * ((x_kde - v) / bandwidth) ** 2)
    density /= n * bandwidth * np.sqrt(2 * np.pi)

    # Trim KDE tails at 8% of peak for cleaner cloud edges
    peak = density.max()
    above = np.where(density > peak * 0.08)[0]
    x_kde = x_kde[above[0] : above[-1] + 1]
    density = density[above[0] : above[-1] + 1]

    density_scaled = density / density.max() * cloud_height

    # Cloud polygon in data coordinates
    poly_data = [(float(x_kde[0]), float(center_y))]
    poly_data += [(float(x), float(center_y + d)) for x, d in zip(x_kde, density_scaled, strict=True)]
    poly_data.append((float(x_kde[-1]), float(center_y)))
    cloud_polygons.append((group_colors[i], poly_data))

    # Rain (jittered points below baseline)
    np.random.seed(42 + i)
    jitter = np.random.uniform(-0.08, 0.08, len(values))
    rain_points = [
        {"value": (float(v), center_y + rain_offset + float(j)), "label": f"{category}: {v:.0f} ms"}
        for j, v in zip(jitter, values, strict=True)
    ]
    chart.add(f"{category} rain", rain_points, stroke=False, fill=False, dots_size=28)

    # Box plot statistics
    median = float(np.median(values))
    q1 = float(np.percentile(values, 25))
    q3 = float(np.percentile(values, 75))
    iqr = q3 - q1
    whisker_low = float(max(values.min(), q1 - 1.5 * iqr))
    whisker_high = float(min(values.max(), q3 + 1.5 * iqr))
    medians[category] = median

    box_rects.append((group_colors[i], q1, q3, center_y - box_hw, center_y + box_hw))

    # Box outline + whiskers as single path
    box_path = [
        (whisker_low, center_y - box_hw * 0.6),
        (whisker_low, center_y + box_hw * 0.6),
        (whisker_low, center_y),
        (q1, center_y),
        (q1, center_y - box_hw),
        (q3, center_y - box_hw),
        (q3, center_y + box_hw),
        (q1, center_y + box_hw),
        (q1, center_y - box_hw),
        (q1, center_y),
        (q3, center_y),
        (q3, center_y + box_hw),
        (q3, center_y - box_hw),
        (q3, center_y),
        (whisker_high, center_y),
        (whisker_high, center_y - box_hw * 0.6),
        (whisker_high, center_y + box_hw * 0.6),
    ]
    chart.add("", box_path, stroke=True, fill=False, show_dots=False, stroke_style={"width": 10})

    # Median line
    median_line = [(median, center_y - box_hw * 1.1), (median, center_y + box_hw * 1.1)]
    chart.add("", median_line, stroke=True, fill=False, show_dots=False, stroke_style={"width": 12})

chart.y_labels = [
    {"value": 0, "label": ""},
    {"value": 1, "label": "Control"},
    {"value": 2, "label": "Treatment A"},
    {"value": 3, "label": "Treatment B"},
    {"value": 4, "label": ""},
]

# Render base SVG
base_svg = chart.render().decode("utf-8")

# --- SVG post-processing: derive coordinate mapping from two known data points ---
# Find SVG pixel positions for two known data-space x-values by searching rendered circle/path coords.
# Instead of hardcoded coefficients, we extract the plot area dimensions from the SVG viewBox.

# Extract plot group translate
tx_match = re.search(r'class="plot\b[^"]*"[^>]*transform="translate\(([0-9.]+),\s*([0-9.]+)\)"', base_svg)
if not tx_match:
    tx_match = re.search(r'translate\(([0-9.]+),\s*([0-9.]+)\)[^"]*"[^>]*class="plot', base_svg)
plot_tx = float(tx_match.group(1)) if tx_match else 706
plot_ty = float(tx_match.group(2)) if tx_match else 214

# Find plot area rect dimensions inside the plot group
plot_rect_match = re.search(
    r'class="plot\b.*?<rect[^>]*class="background"[^>]*'
    r'width="([0-9.]+)"[^>]*height="([0-9.]+)"',
    base_svg,
    re.DOTALL,
)
if plot_rect_match:
    plot_w = float(plot_rect_match.group(1))
    plot_h = float(plot_rect_match.group(2))
else:
    plot_w = 4800 - plot_tx - 100
    plot_h = 2700 - plot_ty - 120

# Linear mapping from data coords to plot-local SVG pixel coords
x_data_lo, x_data_hi = x_lo, x_hi
y_data_lo, y_data_hi = -0.2, 4.2

x_scale = plot_w / (x_data_hi - x_data_lo)
x_offset = -x_data_lo * x_scale
y_scale = -plot_h / (y_data_hi - y_data_lo)
y_offset = -y_data_hi * y_scale

# Inject cloud polygons inside the plot group
clouds_svg = '<g id="clouds">'
for color, poly in cloud_polygons:
    points = " ".join(f"{(px * x_scale + x_offset):.1f},{(py * y_scale + y_offset):.1f}" for px, py in poly)
    clouds_svg += f'<polygon points="{points}" fill="{color}" opacity="0.75" stroke="none"/>'
clouds_svg += "</g>"

# Insert clouds after the second background rect (inside plot group)
bg_marker = 'class="background"'
first_bg = base_svg.find(bg_marker)
second_bg = base_svg.find(bg_marker, first_bg + 1)
if second_bg > 0:
    bg_end = base_svg.find("/>", second_bg) + 2
    base_svg = base_svg[:bg_end] + clouds_svg + base_svg[bg_end:]

# Box fill rectangles with light tinted fill for better contrast on white
diff = medians["Control"] - medians["Treatment B"]
box_fills_svg = '<g id="box-fills">'
for color, q1, q3, y_lo, y_hi in box_rects:
    bx = q1 * x_scale + x_offset + plot_tx
    by = y_hi * y_scale + y_offset + plot_ty
    bw = (q3 - q1) * x_scale
    bh = (y_lo - y_hi) * y_scale
    box_fills_svg += (
        f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{abs(bh):.1f}"'
        f' fill="{color}" fill-opacity="0.12" stroke="{color}" stroke-width="5"/>'
    )
box_fills_svg += "</g>"

# Annotation elements
annotations_svg = '<g id="annotations">'
for i, name in enumerate(data):
    med = medians[name]
    center_y = i + 1
    mx = med * x_scale + x_offset + plot_tx
    my = center_y * y_scale + y_offset + plot_ty
    label_y = (center_y + 0.42) * y_scale + y_offset + plot_ty
    annotations_svg += (
        f'<line x1="{mx:.0f}" y1="{my:.0f}" x2="{mx:.0f}" y2="{label_y + 10:.0f}"'
        f' stroke="{group_colors[i]}" stroke-width="2" stroke-dasharray="6,4" opacity="0.6"/>'
        f'<text x="{mx:.0f}" y="{label_y:.0f}" text-anchor="middle"'
        f' font-size="38" font-weight="bold" font-family="DejaVu Sans, sans-serif"'
        f' fill="{group_colors[i]}">{med:.0f} ms</text>'
    )

# Insight callout
cx = 580 * x_scale + x_offset + plot_tx
cy = 3.8 * y_scale + y_offset + plot_ty
annotations_svg += (
    f'<rect x="{cx - 200:.0f}" y="{cy - 42:.0f}" width="400" height="90"'
    f' rx="12" ry="12" fill="white" stroke="#4CAF50" stroke-width="3" opacity="0.92"/>'
    f'<text x="{cx:.0f}" y="{cy + 12:.0f}" text-anchor="middle"'
    f' font-size="34" font-weight="bold" font-family="DejaVu Sans, sans-serif"'
    f' fill="#333333">&#x25BC; {diff:.0f} ms faster</text>'
)

# Dashed arrow from callout to Treatment B annotation
tb_x = medians["Treatment B"] * x_scale + x_offset + plot_tx
tb_y = (3 + 0.42) * y_scale + y_offset + plot_ty
annotations_svg += (
    f'<line x1="{cx - 200:.0f}" y1="{cy + 10:.0f}"'
    f' x2="{tb_x + 50:.0f}" y2="{tb_y - 5:.0f}"'
    f' stroke="#4CAF50" stroke-width="2.5" stroke-dasharray="8,5" opacity="0.7"/>'
)

annotations_svg += "</g>"

# Inject fills and annotations before closing </svg>
svg_out = base_svg.replace("</svg>", f"{box_fills_svg}\n{annotations_svg}\n</svg>")

# Save outputs
with open("plot.svg", "w") as f:
    f.write(svg_out)

cairosvg.svg2png(bytestring=svg_out.encode("utf-8"), write_to="plot.png")

with open("plot.html", "w") as f:
    f.write("""<!DOCTYPE html>
<html>
<head>
    <title>raincloud-basic · pygal · pyplots.ai</title>
    <style>
        body { margin: 0; padding: 20px; background: #f5f5f5; font-family: sans-serif; }
        .container { max-width: 100%; margin: 0 auto; }
        object { width: 100%; height: auto; }
    </style>
</head>
<body>
    <div class="container">
        <object type="image/svg+xml" data="plot.svg">
            Raincloud plot not supported
        </object>
    </div>
</body>
</html>""")

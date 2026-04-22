""" pyplots.ai
histogram-2d: 2D Histogram Heatmap
Library: pygal 3.1.0 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-25
"""

import sys


sys.path = [p for p in sys.path if "implementations" not in p]

import cairosvg  # noqa: E402
import numpy as np  # noqa: E402
import pygal  # noqa: E402
from pygal.style import Style  # noqa: E402


# Data: Bivariate normal representing customer age vs purchase frequency
np.random.seed(42)

# Cluster 1: younger customers with higher purchase frequency
n_points = 5000
mean = [35, 12]
cov = [[100, 35], [35, 25]]
data = np.random.multivariate_normal(mean, cov, n_points)
x = data[:, 0]
y = data[:, 1]

# Cluster 2: older customers, fewer purchases (negative correlation)
n_points2 = 2000
mean2 = [55, 8]
cov2 = [[64, -20], [-20, 16]]
data2 = np.random.multivariate_normal(mean2, cov2, n_points2)
x = np.concatenate([x, data2[:, 0]])
y = np.concatenate([y, data2[:, 1]])

# Clip to realistic ranges
x = np.clip(x, 18, 75)
y = np.clip(y, 0, 30)

# Compute 2D histogram
n_bins = 25
counts, x_edges, y_edges = np.histogram2d(x, y, bins=n_bins)
counts = counts.T

# Compute 1D marginal histograms
x_hist, _ = np.histogram(x, bins=n_bins, range=(x_edges[0], x_edges[-1]))
y_hist, _ = np.histogram(y, bins=n_bins, range=(y_edges[0], y_edges[-1]))

# Viridis colormap
viridis = ["#440154", "#482878", "#3e4a89", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58", "#b5de2b", "#fde725"]

min_val = counts.min()
max_val = counts.max()

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333",
    foreground_strong="#333",
    foreground_subtle="#666",
    title_font_size=64,
    font_family="sans-serif",
)

# Create base chart to get SVG rendering
chart = pygal.Bar(
    width=3600,
    height=3600,
    style=custom_style,
    title="histogram-2d · pygal · pyplots.ai",
    show_legend=False,
    margin=20,
    margin_top=140,
)
chart.add("", [0])

# Render and manually construct SVG with heatmap + marginals
svg_parts = []
svg_parts.append('<?xml version="1.0" encoding="utf-8"?>')
svg_parts.append('<svg xmlns="http://www.w3.org/2000/svg" width="3600" height="3600" viewBox="0 0 3600 3600">')
svg_parts.append('<rect width="3600" height="3600" fill="white"/>')

# Title
svg_parts.append(
    '<text x="1800" y="80" text-anchor="middle" fill="#333" '
    'style="font-size:64px;font-weight:bold;font-family:sans-serif">'
    "histogram-2d · pygal · pyplots.ai</text>"
)

# Layout: main heatmap with marginal histograms
margin_l, margin_t = 280, 180
margin_r, margin_b = 220, 280
marginal_h = 300  # Height/width for marginal histograms
gap = 20

# Main heatmap area
hm_x = margin_l
hm_y = margin_t + marginal_h + gap
hm_w = 3600 - margin_l - margin_r - 120  # Leave room for colorbar
hm_h = 3600 - margin_t - margin_b - marginal_h - gap

cell_w = hm_w / n_bins
cell_h = hm_h / n_bins

# Draw heatmap cells
for i in range(n_bins):
    for j in range(n_bins):
        val = counts[n_bins - 1 - i, j]
        if max_val == min_val:
            t = 1.0
        else:
            t = max(0, min(1, (val - min_val) / (max_val - min_val)))
        pos = t * (len(viridis) - 1)
        idx = int(pos)
        idx2 = min(idx + 1, len(viridis) - 1)
        frac = pos - idx
        c1, c2 = viridis[idx], viridis[idx2]
        r = int(int(c1[1:3], 16) * (1 - frac) + int(c2[1:3], 16) * frac)
        g = int(int(c1[3:5], 16) * (1 - frac) + int(c2[3:5], 16) * frac)
        b = int(int(c1[5:7], 16) * (1 - frac) + int(c2[5:7], 16) * frac)
        color = f"#{r:02x}{g:02x}{b:02x}"
        rx = hm_x + j * cell_w
        ry = hm_y + i * cell_h
        svg_parts.append(
            f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{cell_w + 0.5:.1f}" height="{cell_h + 0.5:.1f}" fill="{color}"/>'
        )

# Heatmap border
svg_parts.append(
    f'<rect x="{hm_x}" y="{hm_y}" width="{hm_w}" height="{hm_h}" fill="none" stroke="#333" stroke-width="2"/>'
)

# X-axis marginal histogram (top)
marg_x_y = margin_t
marg_x_h = marginal_h
x_max = x_hist.max()
for j in range(n_bins):
    bar_h = (x_hist[j] / x_max) * marg_x_h * 0.9 if x_max > 0 else 0
    rx = hm_x + j * cell_w
    ry = marg_x_y + marg_x_h - bar_h
    svg_parts.append(
        f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{cell_w - 1:.1f}" height="{bar_h:.1f}" fill="#306998" opacity="0.7"/>'
    )
svg_parts.append(
    f'<rect x="{hm_x}" y="{marg_x_y}" width="{hm_w}" height="{marg_x_h}" fill="none" stroke="#333" stroke-width="1"/>'
)

# Y-axis marginal histogram (right)
marg_y_x = hm_x + hm_w + gap
marg_y_w = 120
y_max = y_hist.max()
for i in range(n_bins):
    bar_w = (y_hist[n_bins - 1 - i] / y_max) * marg_y_w * 0.9 if y_max > 0 else 0
    rx = marg_y_x
    ry = hm_y + i * cell_h
    svg_parts.append(
        f'<rect x="{rx:.1f}" y="{ry:.1f}" width="{bar_w:.1f}" height="{cell_h - 1:.1f}" fill="#306998" opacity="0.7"/>'
    )
svg_parts.append(
    f'<rect x="{marg_y_x}" y="{hm_y}" width="{marg_y_w}" height="{hm_h}" fill="none" stroke="#333" stroke-width="1"/>'
)

# X-axis ticks and labels
for idx in np.linspace(0, n_bins, 7):
    px = hm_x + idx * cell_w
    py = hm_y + hm_h
    val = x_edges[0] + (x_edges[-1] - x_edges[0]) * idx / n_bins
    svg_parts.append(
        f'<line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{py + 15:.1f}" stroke="#333" stroke-width="2"/>'
    )
    svg_parts.append(
        f'<text x="{px:.1f}" y="{py + 55:.1f}" text-anchor="middle" fill="#333" '
        f'style="font-size:36px;font-family:sans-serif">{val:.0f}</text>'
    )

# X-axis label
svg_parts.append(
    f'<text x="{hm_x + hm_w / 2:.1f}" y="{hm_y + hm_h + 130:.1f}" text-anchor="middle" '
    f'fill="#333" style="font-size:48px;font-weight:bold;font-family:sans-serif">'
    f"Customer Age (years)</text>"
)

# Y-axis ticks and labels
for idx in np.linspace(0, n_bins, 7):
    px = hm_x
    py = hm_y + hm_h - idx * cell_h
    val = y_edges[0] + (y_edges[-1] - y_edges[0]) * idx / n_bins
    svg_parts.append(
        f'<line x1="{px - 15:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="#333" stroke-width="2"/>'
    )
    svg_parts.append(
        f'<text x="{px - 25:.1f}" y="{py + 12:.1f}" text-anchor="end" fill="#333" '
        f'style="font-size:36px;font-family:sans-serif">{val:.0f}</text>'
    )

# Y-axis label (rotated)
ly = hm_y + hm_h / 2
lx = hm_x - 180
svg_parts.append(
    f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" fill="#333" '
    f'style="font-size:48px;font-weight:bold;font-family:sans-serif" '
    f'transform="rotate(-90, {lx:.1f}, {ly:.1f})">Annual Purchases (count)</text>'
)

# Colorbar
cb_x = marg_y_x + marg_y_w + 60
cb_y = hm_y + hm_h * 0.1
cb_w = 50
cb_h = hm_h * 0.8
n_seg = 60
seg_h = cb_h / n_seg

for i in range(n_seg):
    seg_val = min_val + (max_val - min_val) * (n_seg - 1 - i) / (n_seg - 1)
    t = (seg_val - min_val) / (max_val - min_val) if max_val > min_val else 1
    pos = t * (len(viridis) - 1)
    idx = int(pos)
    idx2 = min(idx + 1, len(viridis) - 1)
    frac = pos - idx
    c1, c2 = viridis[idx], viridis[idx2]
    r = int(int(c1[1:3], 16) * (1 - frac) + int(c2[1:3], 16) * frac)
    g = int(int(c1[3:5], 16) * (1 - frac) + int(c2[3:5], 16) * frac)
    b = int(int(c1[5:7], 16) * (1 - frac) + int(c2[5:7], 16) * frac)
    color = f"#{r:02x}{g:02x}{b:02x}"
    svg_parts.append(
        f'<rect x="{cb_x:.1f}" y="{cb_y + i * seg_h:.1f}" width="{cb_w}" height="{seg_h + 1:.1f}" fill="{color}"/>'
    )

svg_parts.append(
    f'<rect x="{cb_x}" y="{cb_y}" width="{cb_w}" height="{cb_h}" fill="none" stroke="#333" stroke-width="2"/>'
)

# Colorbar ticks
for i in range(5):
    frac = i / 4
    tick_val = max_val - frac * (max_val - min_val)
    ty = cb_y + frac * cb_h
    svg_parts.append(
        f'<line x1="{cb_x + cb_w:.1f}" y1="{ty:.1f}" '
        f'x2="{cb_x + cb_w + 10:.1f}" y2="{ty:.1f}" stroke="#333" stroke-width="2"/>'
    )
    svg_parts.append(
        f'<text x="{cb_x + cb_w + 20:.1f}" y="{ty + 12:.1f}" fill="#333" '
        f'style="font-size:36px;font-family:sans-serif">{int(tick_val)}</text>'
    )

# Colorbar label
svg_parts.append(
    f'<text x="{cb_x + cb_w / 2:.1f}" y="{cb_y - 30:.1f}" text-anchor="middle" '
    f'fill="#333" style="font-size:42px;font-weight:bold;font-family:sans-serif">Count</text>'
)

svg_parts.append("</svg>")

# Save SVG
svg_content = "\n".join(svg_parts)
with open("plot.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

# Save PNG
cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to="plot.png")

# Save HTML
html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>histogram-2d - pygal</title>
    <style>
        body {{ margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; background: #f5f5f5; }}
        .chart {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <figure class="chart">
        {svg_content}
    </figure>
</body>
</html>
"""

with open("plot.html", "w", encoding="utf-8") as f:
    f.write(html_content)

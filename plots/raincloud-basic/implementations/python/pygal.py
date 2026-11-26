"""anyplot.ai
raincloud-basic: Basic Raincloud Plot
Library: pygal 3.1.3 | Python 3.14.10
Quality: pending | Updated: 2026-11-26
"""

import os
import re

import cairosvg
import numpy as np
import pandas as pd
import pygal
from pygal.style import Style
from scipy.stats import gaussian_kde


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Box-interior fill: in light mode the off-white reads as a hollow box; in dark
# mode PAGE_BG blends into the canvas, so blend toward INK to keep the box
# distinct from the surrounding plot background.
BOX_FILL = "#FAF8F1" if THEME == "light" else "#2E2E29"

IMPRINT_PALETTE = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Column constants
GROUP = "Treatment Group"  # role: category
REACTION = "Reaction Time (ms)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("reaction_times.csv")
np.random.seed(42)
df = pd.DataFrame(
    {
        GROUP: np.repeat(["Control", "Treatment A", "Treatment B"], 90),
        REACTION: np.concatenate(
            [np.random.normal(450, 80, 90), np.random.normal(380, 60, 90), np.random.normal(320, 50, 90)]
        ),
    }
)

# Plot
groups = list(dict.fromkeys(df[GROUP]))
data = {g: df.loc[df[GROUP] == g, REACTION].dropna().to_numpy() for g in groups}
group_colors = [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(len(groups))]

x_lo = float(np.floor((df[REACTION].min() - 25) / 50) * 50)
x_hi = float(np.ceil((df[REACTION].max() + 25) / 50) * 50)
y_top = float(len(groups) + 1)

# Series order per group: rain, whisker
series_colors = [c for gc in group_colors for c in (gc, gc)]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=tuple(series_colors),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=2.5,
)


CANVAS_W, CANVAS_H = 3200, 1800

chart = pygal.XY(
    width=CANVAS_W,
    height=CANVAS_H,
    style=custom_style,
    title="raincloud-basic · python · pygal · anyplot.ai",
    x_title=REACTION,
    y_title=GROUP,
    show_legend=False,
    stroke=True,
    fill=False,
    dots_size=0,
    show_x_guides=True,
    show_y_guides=False,
    xrange=(x_lo, x_hi),
    range=(0.0, y_top),
    margin=40,
    margin_left=60,
    margin_right=90,
    margin_top=150,
    margin_bottom=160,
    explicit_size=True,
    css=(
        "file://style.css",
        "file://graph.css",
        "inline:.dot { fill-opacity: 0.6 !important; stroke-opacity: 0.6 !important; }",
    ),
)

# Raincloud layout
cloud_height = 0.36
rain_offset = -0.36
rain_spread = 0.10
box_hw = 0.13

rain_xy = []
cloud_polygons = []
box_specs = []

for i, (category, values) in enumerate(data.items()):
    center_y = i + 1

    # Half-violin: Gaussian KDE with a Silverman bandwidth
    bandwidth = 0.9 * min(values.std(), np.subtract(*np.percentile(values, [75, 25])) / 1.34) * len(values) ** -0.2
    pad = (values.max() - values.min()) * 0.08
    x_kde = np.linspace(values.min() - pad, values.max() + pad, 96)
    density = gaussian_kde(values, bw_method=bandwidth / values.std(ddof=1))(x_kde)

    # Trim KDE tails at 5% of peak for cleaner cloud edges
    keep = np.where(density > density.max() * 0.05)[0]
    x_kde = x_kde[keep[0] : keep[-1] + 1]
    density = density[keep[0] : keep[-1] + 1]
    cloud_polygons.append((group_colors[i], center_y, x_kde, density / density.max() * cloud_height))

    # Rain: jittered points below baseline
    jitter = np.random.default_rng(42 + i).uniform(-rain_spread, rain_spread, len(values))
    rain_points = [
        {"value": (float(v), center_y + rain_offset + float(j)), "label": f"{category}: {v:.0f} ms"}
        for j, v in zip(jitter, values, strict=True)
    ]
    rain_xy.extend(p["value"] for p in rain_points)
    chart.add(f"{category} rain", rain_points, stroke=False, fill=False, dots_size=15)

    # Box statistics and whisker line
    q1, median, q3 = (float(q) for q in np.percentile(values, [25, 50, 75]))
    w_lo = float(max(values.min(), q1 - 1.5 * (q3 - q1)))
    w_hi = float(min(values.max(), q3 + 1.5 * (q3 - q1)))
    box_specs.append((group_colors[i], center_y, q1, q3, median))
    chart.add(
        "", [(w_lo, center_y), (w_hi, center_y)], stroke=True, fill=False, show_dots=False, stroke_style={"width": 4}
    )

chart.y_labels = [{"value": 0.0, "label": ""}]
chart.y_labels += [{"value": float(i + 1), "label": str(g)} for i, g in enumerate(groups)]
chart.y_labels.append({"value": y_top, "label": ""})

# Translucent rain dots (alpha 0.6)

base_svg = chart.render().decode("utf-8")

# pygal's own mapping, read back from the rain circles it drew (data -> plot-local pixels)
circles = np.array(re.findall(r'<circle cx="([0-9.]+)" cy="([0-9.]+)" r="15"', base_svg), dtype=float)
rain_xy = np.array(rain_xy)
x_fit = np.polyfit(rain_xy[:, 0], circles[:, 0], 1)
y_fit = np.polyfit(rain_xy[:, 1], circles[:, 1], 1)
plot_g = re.search(r'<g\s+transform="translate\(([0-9.]+)[,\s]+([0-9.]+)\)"\s+class="plot">', base_svg)
plot_tx, plot_ty = float(plot_g.group(1)), float(plot_g.group(2))

# Clouds: filled polygon, stroke only along the curved top
clouds_svg = '<g class="raincloud-clouds">'
for color, cy, xs, ds in cloud_polygons:
    px = np.array([np.polyval(x_fit, x) for x in xs])
    py = np.array([np.polyval(y_fit, cy + d) for d in ds])
    base = np.polyval(y_fit, cy)
    pts = f"{px[0]:.1f},{base:.1f} " + " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(px, py, strict=True))
    pts += f" {px[-1]:.1f},{base:.1f}"
    curve = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(px, py, strict=True))
    clouds_svg += (
        f'<polygon points="{pts}" fill="{color}" fill-opacity="0.55" stroke="none"/>'
        f'<polyline points="{curve}" fill="none" stroke="{color}" stroke-width="2.5" stroke-opacity="0.9"/>'
    )
clouds_svg += "</g>"

bg_marker = 'class="background"'
first_bg = base_svg.find(bg_marker)
second_bg = base_svg.find(bg_marker, first_bg + 1)
bg_end = base_svg.find("/>", second_bg) + 2
base_svg = base_svg[:bg_end] + clouds_svg + base_svg[bg_end:]

# Boxes with quartile edges and a thick median
boxes_svg = '<g class="raincloud-boxes">'
for color, cy, q1, q3, median in box_specs:
    bx, bx2 = np.polyval(x_fit, q1) + plot_tx, np.polyval(x_fit, q3) + plot_tx
    by, by2 = np.polyval(y_fit, cy + box_hw) + plot_ty, np.polyval(y_fit, cy - box_hw) + plot_ty
    mx = np.polyval(x_fit, median) + plot_tx
    boxes_svg += (
        f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bx2 - bx:.1f}" height="{by2 - by:.1f}" '
        f'fill="{BOX_FILL}" fill-opacity="0.92" stroke="{color}" stroke-width="5"/>'
        f'<line x1="{mx:.1f}" y1="{by:.1f}" x2="{mx:.1f}" y2="{by2:.1f}" '
        f'stroke="{color}" stroke-width="8" stroke-linecap="round"/>'
    )
boxes_svg += "</g>"

svg_out = base_svg.replace("</svg>", f"{boxes_svg}\n</svg>")

# Save outputs
with open(f"plot-{THEME}.svg", "w") as f:
    f.write(svg_out)

cairosvg.svg2png(
    bytestring=svg_out.encode("utf-8"), write_to=f"plot-{THEME}.png", output_width=CANVAS_W, output_height=CANVAS_H
)

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(svg_out.encode("utf-8"))

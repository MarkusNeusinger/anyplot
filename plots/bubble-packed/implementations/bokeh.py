"""pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: bokeh 3.8.2 | Python 3.14.3
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, LabelSet
from bokeh.plotting import figure


np.random.seed(42)

# Data — department budgets (millions)
departments = [
    "Engineering",
    "Marketing",
    "Sales",
    "Operations",
    "HR",
    "Finance",
    "R&D",
    "Legal",
    "IT",
    "Customer Support",
    "Product",
    "Design",
    "QA",
    "Data Science",
    "Security",
]
budgets = [45, 32, 38, 25, 12, 18, 42, 8, 22, 15, 28, 14, 10, 20, 6]
n = len(budgets)

# Radii — area-scaled (sqrt) for accurate visual perception
max_r = 460
vals = np.array(budgets, dtype=float)
radii = np.sqrt(vals / vals.max()) * max_r

# Force-directed circle packing on square canvas
W, H = 3600, 3600
center = np.array([W / 2.0, H / 2.0])
pos = center + (np.random.rand(n, 2) - 0.5) * 600
pad = 12

for step in range(600):
    pos += (center - pos) * 0.012
    total_shift = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            d = pos[j] - pos[i]
            dist = np.linalg.norm(d) + 1e-6
            gap = radii[i] + radii[j] + pad
            if dist < gap:
                s = d / dist * (gap - dist) * 0.5
                pos[i] -= s
                pos[j] += s
                total_shift += gap - dist
    pos[:, 0] = np.clip(pos[:, 0], radii + 50, W - radii - 50)
    pos[:, 1] = np.clip(pos[:, 1], radii + 50, H - radii - 50)
    if step > 200 and total_shift < 1.0:
        break

# Center cluster and compute tight viewing range
x_lo, x_hi = (pos[:, 0] - radii).min(), (pos[:, 0] + radii).max()
y_lo, y_hi = (pos[:, 1] - radii).min(), (pos[:, 1] + radii).max()
pos[:, 0] += (W - (x_lo + x_hi)) / 2
pos[:, 1] += (H - (y_lo + y_hi)) / 2
margin = 150
xr = ((pos[:, 0] - radii).min() - margin, (pos[:, 0] + radii).max() + margin)
yr = ((pos[:, 1] - radii).min() - margin, (pos[:, 1] + radii).max() + margin)

p = figure(
    width=W,
    height=H,
    title="Department Budgets · bubble-packed · bokeh · pyplots.ai",
    x_range=xr,
    y_range=yr,
    tools="",
    toolbar_location=None,
)

# Tier palette — 4 hue families, dark tones for white text, depth-graded alpha
tier_defs = [
    (">$35M", "#1B4F72", 0.92, [i for i in range(n) if budgets[i] > 35]),
    ("$20\u201335M", "#7D6608", 0.88, [i for i in range(n) if 20 <= budgets[i] <= 35]),
    ("$10\u201319M", "#A04000", 0.84, [i for i in range(n) if 10 <= budgets[i] < 20]),
    ("<$10M", "#6C3483", 0.80, [i for i in range(n) if budgets[i] < 10]),
]

# Render circles per tier — separate renderers for native Bokeh legend entries
renderers = []
for tier_name, color, alpha, idx in tier_defs:
    src = ColumnDataSource(
        data={
            "x": pos[idx, 0].tolist(),
            "y": pos[idx, 1].tolist(),
            "radius": radii[idx].tolist(),
            "dept": [departments[i] for i in idx],
            "budget": [f"${budgets[i]}M" for i in idx],
            "tier": [tier_name for _ in idx],
        }
    )
    r = p.circle(
        x="x",
        y="y",
        radius="radius",
        source=src,
        fill_color=color,
        fill_alpha=alpha,
        line_color="white",
        line_width=3,
        legend_label=tier_name,
    )
    renderers.append(r)

# Labels inside circles — font size adapts to radius
brackets = [(340, float("inf"), "24pt", "20pt", 22), (200, 340, "18pt", "15pt", 15), (0, 200, "16pt", "14pt", 12)]
for lo, hi, name_fs, val_fs, y_off in brackets:
    idx = [i for i in range(n) if lo <= radii[i] < hi]
    if not idx:
        continue
    src = ColumnDataSource(
        data={
            "x": pos[idx, 0].tolist(),
            "y": pos[idx, 1].tolist(),
            "name": [departments[i] for i in idx],
            "val": [f"${budgets[i]}M" for i in idx],
        }
    )
    p.add_layout(
        LabelSet(
            x="x",
            y="y",
            text="name",
            source=src,
            text_align="center",
            text_baseline="middle",
            text_font_size=name_fs,
            text_color="white",
            text_font_style="bold",
            y_offset=y_off,
        )
    )
    p.add_layout(
        LabelSet(
            x="x",
            y="y",
            text="val",
            source=src,
            text_align="center",
            text_baseline="middle",
            text_font_size=val_fs,
            text_color="rgba(255,255,255,0.85)",
            y_offset=-y_off,
        )
    )

# Style
p.title.text_font_size = "36pt"
p.title.align = "center"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.background_fill_color = "#f8f9fa"
p.border_fill_color = "#f8f9fa"
p.outline_line_color = None
p.min_border = 40

# Legend — styled tiers with interactive hide toggle
p.legend.location = "top_right"
p.legend.label_text_font_size = "24pt"
p.legend.glyph_height = 50
p.legend.glyph_width = 50
p.legend.background_fill_alpha = 0.85
p.legend.background_fill_color = "#f8f9fa"
p.legend.border_line_color = "#dee2e6"
p.legend.border_line_width = 2
p.legend.padding = 20
p.legend.spacing = 12
p.legend.label_standoff = 12
p.legend.click_policy = "hide"

# HoverTool — Bokeh-distinctive interactivity (active in HTML output)
p.add_tools(
    HoverTool(tooltips=[("Department", "@dept"), ("Budget", "@budget"), ("Tier", "@tier")], renderers=renderers)
)

export_png(p, filename="plot.png")

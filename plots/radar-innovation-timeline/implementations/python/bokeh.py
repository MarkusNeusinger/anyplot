""" pyplots.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-02-18
"""

from collections import defaultdict

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem
from bokeh.plotting import figure


# Data - Technology innovation radar
np.random.seed(42)

sectors = ["AI & ML", "Cloud & Infra", "Sustainability", "Biotech"]
rings = ["Adopt", "Trial", "Assess", "Hold"]

# Ring radii (inner to outer): Adopt is closest (near-term), Hold is farthest (future)
# Wider rings fill more canvas; Adopt ring extra wide for label breathing room
ring_inner = [0, 105, 200, 295]
ring_outer = [105, 200, 295, 390]
ring_mid = [(i + o) / 2 for i, o in zip(ring_inner, ring_outer, strict=True)]

# Marker sizes vary by ring to create visual hierarchy (near-term = larger/bolder)
ring_marker_sizes = [28, 22, 18, 14]

# Innovation items: (name, ring_index, sector_index)
items = [
    # AI & ML (sector 0)
    ("LLM Agents", 0, 0),
    ("RAG Pipelines", 0, 0),
    ("Vision Models", 1, 0),
    ("AI Code Review", 1, 0),
    ("Neuro-Symbolic AI", 2, 0),
    ("Quantum ML", 3, 0),
    ("Autonomous Research", 3, 0),
    # Cloud & Infra (sector 1)
    ("K8s GitOps", 0, 1),
    ("Edge Computing", 0, 1),
    ("WebAssembly", 1, 1),
    ("Serverless GPUs", 1, 1),
    ("eBPF Networking", 2, 1),
    ("Confidential Compute", 2, 1),
    ("Satellite Internet", 3, 1),
    # Sustainability (sector 2)
    ("Carbon Tracking", 0, 2),
    ("Green Cloud", 1, 2),
    ("Circular Supply Chain", 1, 2),
    ("Smart Grid AI", 2, 2),
    ("Ocean Carbon Capture", 3, 2),
    ("Fusion Energy", 3, 2),
    # Biotech (sector 3)
    ("mRNA Therapeutics", 0, 3),
    ("CRISPR Diagnostics", 1, 3),
    ("Digital Twins (Health)", 2, 3),
    ("Organ-on-Chip", 2, 3),
    ("Synthetic Biology", 3, 3),
    ("Brain-Computer Interface", 3, 3),
]

n_sectors = len(sectors)

# Use 270 degrees (three-quarter circle) to leave room for legend/title
total_angle = 3 * np.pi / 2
start_angle = np.pi / 4  # Start at 45 degrees (upper-right gap)

# Sector angular boundaries
sector_width = total_angle / n_sectors
sector_starts = [start_angle + i * sector_width for i in range(n_sectors)]
sector_ends = [start_angle + (i + 1) * sector_width for i in range(n_sectors)]

# Colorblind-safe palette: blue, orange, teal, purple
sector_colors = ["#306998", "#E07B39", "#2A9D8F", "#7B2D8E"]

# Create figure
p = figure(
    width=3600,
    height=3600,
    title="radar-innovation-timeline \u00b7 bokeh \u00b7 pyplots.ai",
    x_range=(-470, 470),
    y_range=(-460, 480),
    tools="",
    toolbar_location=None,
)

# Remove axes and grid
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None
p.background_fill_color = "#FAFAFA"

# Draw ring background fills with subtle gradient-like shading
ring_fills = ["#D8E4F0", "#E5E5E5", "#F0E4D8", "#F0D8E4"]
ring_alphas = [0.8, 0.7, 0.6, 0.5]
for ring_idx in range(len(rings)):
    r_out = ring_outer[ring_idx]
    r_in = ring_inner[ring_idx]
    theta = np.linspace(start_angle, start_angle + total_angle, 200)

    x_out = r_out * np.cos(theta)
    y_out = r_out * np.sin(theta)
    x_in = r_in * np.cos(theta[::-1])
    y_in = r_in * np.sin(theta[::-1])

    p.patch(
        np.concatenate([x_out, x_in]).tolist(),
        np.concatenate([y_out, y_in]).tolist(),
        fill_color=ring_fills[ring_idx],
        fill_alpha=ring_alphas[ring_idx],
        line_color=None,
    )

# Sector-colored subtle overlays per ring-sector cell for visual grouping
for ring_idx in range(len(rings)):
    for sector_idx in range(n_sectors):
        r_out = ring_outer[ring_idx]
        r_in = ring_inner[ring_idx]
        theta_seg = np.linspace(sector_starts[sector_idx], sector_ends[sector_idx], 50)
        x_out = r_out * np.cos(theta_seg)
        y_out = r_out * np.sin(theta_seg)
        x_in = r_in * np.cos(theta_seg[::-1])
        y_in = r_in * np.sin(theta_seg[::-1])
        p.patch(
            np.concatenate([x_out, x_in]).tolist(),
            np.concatenate([y_out, y_in]).tolist(),
            fill_color=sector_colors[sector_idx],
            fill_alpha=0.06,
            line_color=None,
        )

# Draw ring boundary arcs
for r in ring_outer:
    theta = np.linspace(start_angle, start_angle + total_angle, 200)
    p.line(
        (r * np.cos(theta)).tolist(),
        (r * np.sin(theta)).tolist(),
        line_color="#9E9E9E",
        line_width=2.5,
        line_alpha=0.55,
        line_dash=[6, 4],
    )

# Draw sector divider lines
for i in range(n_sectors + 1):
    angle = start_angle + i * sector_width
    p.line(
        [0, ring_outer[-1] * np.cos(angle)],
        [0, ring_outer[-1] * np.sin(angle)],
        line_color="#B0B0B0",
        line_width=2,
        line_alpha=0.6,
    )

# Ring labels along the ending radial boundary (in the gap area, away from items)
end_angle = start_angle + total_angle
label_angle = end_angle + 0.08
for ring_idx, ring_name in enumerate(rings):
    r = ring_mid[ring_idx]
    p.add_layout(
        Label(
            x=r * np.cos(label_angle),
            y=r * np.sin(label_angle),
            text=ring_name,
            text_font_size="22pt",
            text_color="#555555",
            text_font_style="bold",
            text_align="center",
            text_baseline="middle",
            background_fill_color="white",
            background_fill_alpha=0.7,
        )
    )

# Sector header labels along the outer edge
for i, sector_name in enumerate(sectors):
    mid_angle = (sector_starts[i] + sector_ends[i]) / 2
    label_r = ring_outer[-1] + 45
    x_pos = label_r * np.cos(mid_angle)
    y_pos = label_r * np.sin(mid_angle)

    cos_val = np.cos(mid_angle)
    text_align = "center" if abs(cos_val) < 0.3 else ("left" if cos_val > 0 else "right")

    p.add_layout(
        Label(
            x=x_pos,
            y=y_pos,
            text=sector_name,
            text_font_size="28pt",
            text_color=sector_colors[i],
            text_font_style="bold",
            text_align=text_align,
            text_baseline="middle",
        )
    )

# Precompute item positions
# Group items by (ring, sector) for spacing
groups = defaultdict(list)
for idx, (_name, ring_idx, sector_idx) in enumerate(items):
    groups[(ring_idx, sector_idx)].append(idx)

xs, ys, colors, sizes, names, ring_names, sector_names = [], [], [], [], [], [], []

for idx, (name, ring_idx, sector_idx) in enumerate(items):
    group = groups[(ring_idx, sector_idx)]
    pos_in_group = group.index(idx)
    n_in_group = len(group)

    # Distribute items within the sector angular range with wider margins
    s_start = sector_starts[sector_idx]
    margin = sector_width * 0.12
    usable_start = s_start + margin
    usable_end = sector_ends[sector_idx] - margin

    if n_in_group == 1:
        angle = (usable_start + usable_end) / 2
    else:
        angle = usable_start + (usable_end - usable_start) * pos_in_group / (n_in_group - 1)

    # Radial position with jitter
    r_base = ring_mid[ring_idx]
    ring_hw = (ring_outer[ring_idx] - ring_inner[ring_idx]) / 2
    r = r_base + np.random.uniform(-ring_hw * 0.35, ring_hw * 0.35)

    x = r * np.cos(angle)
    y = r * np.sin(angle)

    xs.append(x)
    ys.append(y)
    colors.append(sector_colors[sector_idx])
    sizes.append(ring_marker_sizes[ring_idx])
    names.append(name)
    ring_names.append(rings[ring_idx])
    sector_names.append(sectors[sector_idx])

    # Add item label with per-ring offset; stagger inner ring labels to avoid crowding
    base_offsets = [26, 20, 16, 13]
    if ring_idx == 0 and n_in_group > 1:
        # Alternate labels: even items push outward, odd items push inward
        direction = 1 if pos_in_group % 2 == 0 else -0.6
        label_r_offset = base_offsets[ring_idx] * direction
    else:
        label_r_offset = base_offsets[ring_idx]

    lx = x + label_r_offset * np.cos(angle)
    ly = y + label_r_offset * np.sin(angle)

    cos_val = np.cos(angle)
    text_align = "center" if abs(cos_val) < 0.3 else ("left" if cos_val > 0 else "right")
    sin_val = np.sin(angle)
    text_baseline = "middle" if abs(sin_val) < 0.3 else ("bottom" if sin_val > 0 else "top")

    p.add_layout(
        Label(
            x=lx,
            y=ly,
            text=name,
            text_font_size="16pt",
            text_color="#2A2A2A",
            text_align=text_align,
            text_baseline=text_baseline,
        )
    )

# Use ColumnDataSource for scatter markers (core Bokeh idiom)
source = ColumnDataSource(
    data={"x": xs, "y": ys, "color": colors, "size": sizes, "name": names, "ring": ring_names, "sector": sector_names}
)

# Render markers per sector for legend items
legend_items = []
for si, sector_name in enumerate(sectors):
    indices = [i for i, (_, _, sec_idx) in enumerate(items) if sec_idx == si]
    sector_source = ColumnDataSource(
        data={
            "x": [xs[i] for i in indices],
            "y": [ys[i] for i in indices],
            "color": [colors[i] for i in indices],
            "size": [sizes[i] for i in indices],
            "name": [names[i] for i in indices],
            "ring": [ring_names[i] for i in indices],
            "sector": [sector_names[i] for i in indices],
        }
    )
    renderer = p.scatter(
        "x", "y", source=sector_source, size="size", fill_color="color", line_color="white", line_width=3, alpha=0.9
    )
    legend_items.append(LegendItem(label=sector_name, renderers=[renderer]))

# HoverTool - Bokeh-distinctive interactive feature
hover = HoverTool(
    tooltips=[("Technology", "@name"), ("Horizon", "@ring"), ("Sector", "@sector")], point_policy="snap_to_data"
)
p.add_tools(hover)

# Legend
legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="22pt",
    glyph_height=35,
    glyph_width=35,
    spacing=18,
    padding=25,
    background_fill_color="white",
    background_fill_alpha=0.9,
    border_line_color="#CCCCCC",
    border_line_width=2,
)
p.add_layout(legend, "right")

# Title styling
p.title.text_font_size = "34pt"
p.title.align = "center"
p.title.text_color = "#1A1A1A"

# Save
export_png(p, filename="plot.png")
output_file("plot.html", title="radar-innovation-timeline \u00b7 bokeh \u00b7 pyplots.ai")
save(p)

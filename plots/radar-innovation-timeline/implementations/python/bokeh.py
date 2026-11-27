"""anyplot.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: bokeh 3.10.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")

# Imprint palette — theme-adaptive chrome
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint categorical palette — 8 hues, canonical order, theme-independent
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
NAME = "Technology"  # role: name
RING = "Horizon"  # role: ring
SECTOR = "Sector"  # role: sector

# Data: replace this block with your own table, for example df = pd.read_csv("radar.csv")
# Rows are listed ring by ring within each sector, nearest horizon first.
df = pd.DataFrame(
    [
        ("LLM Agents", "Adopt", "AI & ML"),
        ("RAG Pipelines", "Adopt", "AI & ML"),
        ("Vision Models", "Trial", "AI & ML"),
        ("AI Code Review", "Trial", "AI & ML"),
        ("Neuro-Symbolic AI", "Assess", "AI & ML"),
        ("Quantum ML", "Hold", "AI & ML"),
        ("Autonomous Research", "Hold", "AI & ML"),
        ("K8s GitOps", "Adopt", "Cloud & Infra"),
        ("Edge Computing", "Adopt", "Cloud & Infra"),
        ("WebAssembly", "Trial", "Cloud & Infra"),
        ("Serverless GPUs", "Trial", "Cloud & Infra"),
        ("eBPF Networking", "Assess", "Cloud & Infra"),
        ("Confidential Compute", "Assess", "Cloud & Infra"),
        ("Satellite Internet", "Hold", "Cloud & Infra"),
        ("Carbon Tracking", "Adopt", "Sustainability"),
        ("Green Cloud", "Trial", "Sustainability"),
        ("Circular Supply Chain", "Trial", "Sustainability"),
        ("Smart Grid AI", "Assess", "Sustainability"),
        ("Ocean Carbon Capture", "Hold", "Sustainability"),
        ("Fusion Energy", "Hold", "Sustainability"),
        ("mRNA Therapeutics", "Adopt", "Biotech"),
        ("CRISPR Diagnostics", "Trial", "Biotech"),
        ("Digital Twins (Health)", "Assess", "Biotech"),
        ("Organ-on-Chip", "Assess", "Biotech"),
        ("Synthetic Biology", "Hold", "Biotech"),
        ("Brain-Computer Interface", "Hold", "Biotech"),
    ],
    columns=[NAME, RING, SECTOR],
)

# Plot: reads only df and the constants above
sectors = list(df[SECTOR].unique())
rings = list(df[RING].unique())
n_sectors = len(sectors)
n_rings = len(rings)
sector_colors = [IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i in range(n_sectors)]  # first sector takes #009E73

# Ring geometry: a wider innermost ring holds the crowded nearest horizon
R_MAX = 390
core = 190
ring_outer = [core + (R_MAX - core) / (n_rings - 1) * k for k in range(n_rings)]
ring_inner = [0, *ring_outer[:-1]]
ring_mid = [(i + o) / 2 for i, o in zip(ring_inner, ring_outer, strict=True)]

# Visual hierarchy: near-term items are larger/bolder
ring_marker_sizes = np.linspace(28, 14, n_rings)
label_offsets = np.linspace(15, 11, n_rings)

# 270-degree layout; gap in upper-right holds ring labels and legend
total_angle = 3 * np.pi / 2
start_angle = np.pi / 4
sector_width = total_angle / n_sectors
sector_starts = [start_angle + i * sector_width for i in range(n_sectors)]
sector_ends = [start_angle + (i + 1) * sector_width for i in range(n_sectors)]

# Square canvas 2400×2400 (symmetric radar)
W, H = 2400, 2400

p = figure(
    width=W,
    height=H,
    title="radar-innovation-timeline · python · bokeh · anyplot.ai",
    x_range=(-R_MAX * 1.42, R_MAX * 1.2),
    y_range=(-R_MAX * 1.31, R_MAX * 1.31),
    tools="",
    toolbar_location=None,  # omit toolbar so PNG height matches H exactly
    min_border_top=120,
    min_border_bottom=60,
    min_border_left=60,
    min_border_right=60,
)

# Theme-adaptive chrome
p.axis.visible = False
p.grid.visible = False
p.outline_line_color = None
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.title.text_font_size = "50pt"
p.title.align = "center"
p.title.text_color = INK

# Alternating ring background fills — subtle bands separate time horizons
for ring_idx in range(n_rings):
    r_out = ring_outer[ring_idx]
    r_in = ring_inner[ring_idx]
    theta = np.linspace(start_angle, start_angle + total_angle, 200)
    x_out = r_out * np.cos(theta)
    y_out = r_out * np.sin(theta)
    x_in = r_in * np.cos(theta[::-1])
    y_in = r_in * np.sin(theta[::-1])
    fill_alpha = 0.10 if ring_idx % 2 == 0 else 0.04
    p.patch(
        np.concatenate([x_out, x_in]).tolist(),
        np.concatenate([y_out, y_in]).tolist(),
        fill_color=INK_SOFT,
        fill_alpha=fill_alpha,
        line_color=None,
    )

# Sector-colored overlays per ring-sector cell for visual grouping
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

# Ring boundary arcs (dashed)
for r in ring_outer:
    theta = np.linspace(start_angle, start_angle + total_angle, 200)
    p.line(
        (r * np.cos(theta)).tolist(),
        (r * np.sin(theta)).tolist(),
        line_color=INK_SOFT,
        line_width=2,
        line_alpha=0.4,
        line_dash=[6, 4],
    )

# Sector divider lines from center to outer ring
for i in range(n_sectors + 1):
    angle = start_angle + i * sector_width
    p.line(
        [0, ring_outer[-1] * np.cos(angle)],
        [0, ring_outer[-1] * np.sin(angle)],
        line_color=INK_SOFT,
        line_width=1.5,
        line_alpha=0.45,
    )

# Ring labels in the gap area (upper-right, just beyond the arc end)
end_angle = start_angle + total_angle
label_angle = end_angle + 0.08
for ring_idx, ring_name in enumerate(rings):
    r = ring_mid[ring_idx]
    p.add_layout(
        Label(
            x=r * np.cos(label_angle),
            y=r * np.sin(label_angle),
            text=ring_name,
            text_font_size="30pt",
            text_color=INK_SOFT,
            text_font_style="bold",
            text_align="center",
            text_baseline="middle",
            background_fill_color=ELEVATED_BG,
            background_fill_alpha=0.85,
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
            text_font_size="26pt",
            text_color=sector_colors[i],
            text_font_style="bold",
            text_align=text_align,
            text_baseline="middle",
        )
    )

# Item positions: spread inside each ring-sector cell
np.random.seed(42)
ring_index = {name: i for i, name in enumerate(rings)}
sector_index = {name: i for i, name in enumerate(sectors)}
cell = df.groupby([RING, SECTOR], sort=False)[NAME]
pos_in_cell = cell.cumcount().to_numpy()
cell_size = cell.transform("size").to_numpy()

xs, ys = [], []

for idx, (name, ring_name, sector_name) in enumerate(df[[NAME, RING, SECTOR]].itertuples(index=False)):
    ring_idx = ring_index[ring_name]
    sector_idx = sector_index[sector_name]
    pos_in_group = pos_in_cell[idx]
    n_in_group = cell_size[idx]

    s_start = sector_starts[sector_idx]
    margin = sector_width * 0.15  # wider margin reduces crowding near sector edges
    usable_start = s_start + margin
    usable_end = sector_ends[sector_idx] - margin

    if n_in_group == 1:
        angle = (usable_start + usable_end) / 2
    else:
        angle = usable_start + (usable_end - usable_start) * pos_in_group / (n_in_group - 1)

    r_base = ring_mid[ring_idx]
    ring_hw = (ring_outer[ring_idx] - ring_inner[ring_idx]) / 2
    r = r_base + np.random.uniform(-ring_hw * 0.35, ring_hw * 0.35)

    x = r * np.cos(angle)
    y = r * np.sin(angle)

    xs.append(x)
    ys.append(y)

    # Label placement: always radially outward, away from the apex where sectors converge
    direction = 1
    label_r_offset = label_offsets[ring_idx] * direction

    lx = x + label_r_offset * np.cos(angle)
    ly = y + label_r_offset * np.sin(angle)

    # Anchor the text away from the marker, on the side the label was pushed to
    cos_val = direction * np.cos(angle)
    text_align = "center" if abs(cos_val) < 0.3 else ("left" if cos_val > 0 else "right")
    sin_val = direction * np.sin(angle)
    text_baseline = "middle" if abs(sin_val) < 0.3 else ("bottom" if sin_val > 0 else "top")

    p.add_layout(
        Label(
            x=lx,
            y=ly,
            text=name,
            text_font_size="24pt",
            text_color=INK,
            text_align=text_align,
            text_baseline=text_baseline,
        )
    )

# Scatter markers per sector (needed for per-sector legend items)
legend_items_list = []
placed = df.assign(
    x=xs,
    y=ys,
    size=df[RING].map(dict(zip(rings, ring_marker_sizes, strict=True))),
    color=df[SECTOR].map(dict(zip(sectors, sector_colors, strict=True))),
)
for sector_name in sectors:
    sector_source = ColumnDataSource(placed[placed[SECTOR] == sector_name])
    renderer = p.scatter(
        "x",
        "y",
        source=sector_source,
        size="size",
        fill_color="color",
        line_color=PAGE_BG,  # theme-adaptive marker edge
        line_width=2.5,
        alpha=0.9,
    )
    legend_items_list.append(LegendItem(label=sector_name, renderers=[renderer]))

# HoverTool — Bokeh's distinctive interactive feature
hover = HoverTool(
    tooltips=[(NAME, f"@{{{NAME}}}"), (RING, f"@{{{RING}}}"), (SECTOR, f"@{{{SECTOR}}}")], point_policy="snap_to_data"
)
p.add_tools(hover)

# Legend inside the figure, placed in the upper-right gap area
legend = Legend(
    items=legend_items_list,
    location="top_right",
    label_text_font_size="30pt",
    label_text_color=INK_SOFT,
    glyph_height=40,
    glyph_width=40,
    spacing=16,
    padding=22,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.92,
    border_line_color=INK_SOFT,
    border_line_width=1.5,
)
p.add_layout(legend)  # inside figure, not side panel — fits within 2400×2400 canvas

# Save interactive HTML
output_file(f"plot-{THEME}.html", title="radar-innovation-timeline · python · bokeh · anyplot.ai")
save(p)

# Screenshot with headless Chrome (avoids export_png / chromedriver snap issues)
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H + 200}",  # outer window larger; CDP overrides inner viewport
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
# Force exact viewport via CDP — set_window_size sets the outer window, which
# leaves the inner viewport ~139px shorter than requested on this environment.
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

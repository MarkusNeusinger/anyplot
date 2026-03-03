"""pyplots.ai
alluvial-opinion-flow: Opinion Flow Diagram
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-03
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import Label, Legend, LegendItem
from bokeh.plotting import figure


# Data: Remote work policy opinion survey — 1,000 employees across 4 quarterly waves
# Story: Opinions gradually polarize as the debate matures
waves = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]
opinions = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
colors = {
    "Strongly Agree": "#306998",
    "Agree": "#6BAED6",
    "Neutral": "#A0A0A0",
    "Disagree": "#E8915A",
    "Strongly Disagree": "#C44E52",
}

# Flow transitions between consecutive waves (source, target, respondent_count)
flows_data = [
    # Q1 → Q2
    [
        ("Strongly Agree", "Strongly Agree", 105),
        ("Strongly Agree", "Agree", 15),
        ("Agree", "Strongly Agree", 25),
        ("Agree", "Agree", 230),
        ("Agree", "Neutral", 20),
        ("Agree", "Disagree", 5),
        ("Neutral", "Agree", 35),
        ("Neutral", "Neutral", 190),
        ("Neutral", "Disagree", 20),
        ("Neutral", "Strongly Disagree", 5),
        ("Disagree", "Agree", 5),
        ("Disagree", "Neutral", 30),
        ("Disagree", "Disagree", 175),
        ("Disagree", "Strongly Disagree", 20),
        ("Strongly Disagree", "Neutral", 10),
        ("Strongly Disagree", "Disagree", 15),
        ("Strongly Disagree", "Strongly Disagree", 95),
    ],
    # Q2 → Q3 (polarization intensifies)
    [
        ("Strongly Agree", "Strongly Agree", 120),
        ("Strongly Agree", "Agree", 10),
        ("Agree", "Strongly Agree", 40),
        ("Agree", "Agree", 215),
        ("Agree", "Neutral", 25),
        ("Agree", "Disagree", 5),
        ("Neutral", "Agree", 30),
        ("Neutral", "Neutral", 180),
        ("Neutral", "Disagree", 30),
        ("Neutral", "Strongly Disagree", 10),
        ("Disagree", "Agree", 5),
        ("Disagree", "Neutral", 25),
        ("Disagree", "Disagree", 160),
        ("Disagree", "Strongly Disagree", 25),
        ("Strongly Disagree", "Neutral", 10),
        ("Strongly Disagree", "Disagree", 10),
        ("Strongly Disagree", "Strongly Disagree", 100),
    ],
    # Q3 → Q4 (further polarization)
    [
        ("Strongly Agree", "Strongly Agree", 148),
        ("Strongly Agree", "Agree", 12),
        ("Agree", "Strongly Agree", 35),
        ("Agree", "Agree", 195),
        ("Agree", "Neutral", 25),
        ("Agree", "Disagree", 5),
        ("Neutral", "Agree", 25),
        ("Neutral", "Neutral", 175),
        ("Neutral", "Disagree", 30),
        ("Neutral", "Strongly Disagree", 10),
        ("Disagree", "Agree", 5),
        ("Disagree", "Neutral", 20),
        ("Disagree", "Disagree", 150),
        ("Disagree", "Strongly Disagree", 30),
        ("Strongly Disagree", "Neutral", 10),
        ("Strongly Disagree", "Disagree", 10),
        ("Strongly Disagree", "Strongly Disagree", 115),
    ],
]

# Compute node totals at each wave
node_totals = []
for w_idx in range(len(waves)):
    totals = {}
    if w_idx == 0:
        for op in opinions:
            totals[op] = sum(f[2] for f in flows_data[0] if f[0] == op)
    elif w_idx == len(waves) - 1:
        for op in opinions:
            totals[op] = sum(f[2] for f in flows_data[-1] if f[1] == op)
    else:
        for op in opinions:
            totals[op] = sum(f[2] for f in flows_data[w_idx - 1] if f[1] == op)
    node_totals.append(totals)

# Layout
x_positions = [0, 1.5, 3.0, 4.5]
node_width = 0.14
gap = 18

# Calculate node vertical positions
node_positions = []
for w_idx in range(len(waves)):
    positions = {}
    y_cursor = 0
    for op in opinions:
        height = node_totals[w_idx][op]
        positions[op] = {"y_start": y_cursor, "y_end": y_cursor + height}
        y_cursor += height + gap
    node_positions.append(positions)

max_y = max(node_positions[w][opinions[-1]]["y_end"] for w in range(len(waves)))

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="alluvial-opinion-flow · bokeh · pyplots.ai",
    x_range=(-1.8, 6.8),
    y_range=(-70, max_y + 80),
    tools="",
    toolbar_location=None,
)

# Style
p.title.text_font_size = "32pt"
p.title.align = "center"
p.xgrid.visible = False
p.ygrid.visible = False
p.xaxis.visible = False
p.yaxis.visible = False
p.outline_line_color = None
p.background_fill_color = "#FFFFFF"

# Subtitle
subtitle = Label(
    x=2.25,
    y=max_y + 55,
    text="Remote Work Policy Survey — 1,000 Employees Across 4 Quarters",
    text_font_size="20pt",
    text_align="center",
    text_baseline="top",
    text_color="#666666",
)
p.add_layout(subtitle)

# Precompute all flow ribbon positions for two-pass rendering
flow_ribbons = []

for w_idx, flows in enumerate(flows_data):
    x_start = x_positions[w_idx] + node_width / 2
    x_end = x_positions[w_idx + 1] - node_width / 2

    source_cursors = {op: node_positions[w_idx][op]["y_start"] for op in opinions}
    target_cursors = {op: node_positions[w_idx + 1][op]["y_start"] for op in opinions}

    for from_op, to_op, count in flows:
        if count == 0:
            continue

        y_src_bottom = source_cursors[from_op]
        y_src_top = y_src_bottom + count
        source_cursors[from_op] = y_src_top

        y_tgt_bottom = target_cursors[to_op]
        y_tgt_top = y_tgt_bottom + count
        target_cursors[to_op] = y_tgt_top

        flow_ribbons.append(
            (x_start, x_end, y_src_top, y_src_bottom, y_tgt_top, y_tgt_bottom, colors[from_op], from_op == to_op)
        )

# Render flows: changers first (behind, transparent), then stable on top (opaque)
n_points = 50
t_param = np.linspace(0, 1, n_points)

for ribbon in sorted(flow_ribbons, key=lambda r: r[7]):
    x_s, x_e, yst, ysb, ytt, ytb, color, is_stable = ribbon

    # Cubic bezier control points at 1/3 and 2/3 of x distance
    cx0 = x_s + (x_e - x_s) / 3
    cx1 = x_s + 2 * (x_e - x_s) / 3

    # Top edge bezier
    x_curve = (
        (1 - t_param) ** 3 * x_s
        + 3 * (1 - t_param) ** 2 * t_param * cx0
        + 3 * (1 - t_param) * t_param**2 * cx1
        + t_param**3 * x_e
    )
    y_top = (
        (1 - t_param) ** 3 * yst
        + 3 * (1 - t_param) ** 2 * t_param * yst
        + 3 * (1 - t_param) * t_param**2 * ytt
        + t_param**3 * ytt
    )

    # Bottom edge bezier
    y_bottom = (
        (1 - t_param) ** 3 * ysb
        + 3 * (1 - t_param) ** 2 * t_param * ysb
        + 3 * (1 - t_param) * t_param**2 * ytb
        + t_param**3 * ytb
    )

    # Closed polygon: top curve forward + bottom curve reversed
    xs = list(x_curve) + list(x_curve[::-1])
    ys = list(y_top) + list(y_bottom[::-1])

    # Stable respondents: higher opacity; changers: lower opacity
    fill_alpha = 0.6 if is_stable else 0.2

    p.patch(
        xs, ys, fill_color=color, fill_alpha=fill_alpha, line_color=color, line_alpha=fill_alpha * 0.6, line_width=0.5
    )

# Draw nodes and labels
legend_renderers = {}
for w_idx in range(len(waves)):
    x = x_positions[w_idx]
    for op in opinions:
        y_start = node_positions[w_idx][op]["y_start"]
        y_end = node_positions[w_idx][op]["y_end"]
        height = y_end - y_start

        if height > 0:
            renderer = p.quad(
                left=x - node_width / 2,
                right=x + node_width / 2,
                top=y_end,
                bottom=y_start,
                fill_color=colors[op],
                line_color="white",
                line_width=2,
            )

            if op not in legend_renderers:
                legend_renderers[op] = renderer

            # Node labels: category name + count on first/last columns, count only on middle
            y_mid = (y_start + y_end) / 2
            if w_idx == 0:
                label = Label(
                    x=x - node_width / 2 - 0.05,
                    y=y_mid,
                    text=f"{op} ({int(height)})",
                    text_font_size="18pt",
                    text_baseline="middle",
                    text_align="right",
                    text_color="#333333",
                )
                p.add_layout(label)
            elif w_idx == len(waves) - 1:
                label = Label(
                    x=x + node_width / 2 + 0.05,
                    y=y_mid,
                    text=f"{op} ({int(height)})",
                    text_font_size="18pt",
                    text_baseline="middle",
                    text_color="#333333",
                )
                p.add_layout(label)
            else:
                label = Label(
                    x=x + node_width / 2 + 0.05,
                    y=y_mid,
                    text=str(int(height)),
                    text_font_size="16pt",
                    text_baseline="middle",
                    text_color="#555555",
                )
                p.add_layout(label)

# Wave column headers
for w_idx, wave in enumerate(waves):
    label = Label(
        x=x_positions[w_idx],
        y=-20,
        text=wave,
        text_font_size="24pt",
        text_align="center",
        text_baseline="top",
        text_color="#333333",
        text_font_style="bold",
    )
    p.add_layout(label)

# Legend
legend_items = [LegendItem(label=op, renderers=[legend_renderers[op]]) for op in opinions]
legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="16pt",
    glyph_width=28,
    glyph_height=28,
    spacing=8,
    padding=15,
    background_fill_alpha=0.8,
    background_fill_color="white",
    border_line_color="#cccccc",
)
p.add_layout(legend, "right")

# Opacity legend note
opacity_note = Label(
    x=2.25,
    y=-50,
    text="Solid flows = stable opinion  |  Faded flows = opinion changed",
    text_font_size="16pt",
    text_align="center",
    text_color="#888888",
)
p.add_layout(opacity_note)

# Save
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)

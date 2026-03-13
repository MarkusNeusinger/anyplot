""" pyplots.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: pygal 3.1.0 | Python 3.14.3
Quality: 73/100 | Created: 2026-03-13
"""

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data - Simulated Phase II oncology trial with 25 patients across two arms
np.random.seed(42)

patient_ids = [f"PT-{i:03d}" for i in range(1, 26)]
arms = ["Arm A (Combo)"] * 13 + ["Arm B (Mono)"] * 12

# Generate treatment durations (weeks) - Arm A tends to have longer durations
durations_a = np.random.exponential(scale=28, size=13) + 6
durations_b = np.random.exponential(scale=18, size=12) + 4
durations = np.concatenate([durations_a, durations_b])
durations = np.clip(durations, 4, 60).round(1)

# Event types and their visual properties
event_config = {
    "partial_response": {"symbol": "\u25b2", "color": "#2E8B57", "label": "Partial Response"},
    "complete_response": {"symbol": "\u2605", "color": "#FFD43B", "label": "Complete Response"},
    "progressive_disease": {"symbol": "\u25c6", "color": "#DC143C", "label": "Progressive Disease"},
    "adverse_event": {"symbol": "\u25a0", "color": "#E87D2F", "label": "Adverse Event"},
}

# Generate clinical events for each patient
events = []
for i in range(25):
    patient_events = []
    dur = durations[i]

    # Most patients get a partial response early
    if np.random.random() < 0.75:
        pr_time = np.random.uniform(4, min(12, dur - 1))
        patient_events.append(("partial_response", round(pr_time, 1)))

        # Some convert to complete response
        if np.random.random() < 0.35 and dur > pr_time + 6:
            cr_time = pr_time + np.random.uniform(6, min(16, dur - pr_time - 1))
            patient_events.append(("complete_response", round(cr_time, 1)))

    # Some patients experience progressive disease (often ending treatment)
    if np.random.random() < 0.4:
        pd_time = np.random.uniform(max(8, dur * 0.5), dur)
        patient_events.append(("progressive_disease", round(pd_time, 1)))

    # Occasional adverse events
    if np.random.random() < 0.3:
        ae_time = np.random.uniform(2, min(dur - 1, 20))
        patient_events.append(("adverse_event", round(ae_time, 1)))

    events.append(patient_events)

# Mark ongoing patients (still on treatment at data cutoff)
ongoing = [False] * 25
for i in range(25):
    has_pd = any(e[0] == "progressive_disease" for e in events[i])
    if not has_pd and durations[i] > 30 and np.random.random() < 0.6:
        ongoing[i] = True

# Sort patients by duration (longest first)
sort_idx = np.argsort(-durations)
patient_ids = [patient_ids[i] for i in sort_idx]
arms = [arms[i] for i in sort_idx]
durations = durations[sort_idx]
events = [events[i] for i in sort_idx]
ongoing = [ongoing[i] for i in sort_idx]

# Arm colors - distinct hues for clear differentiation
arm_colors = {"Arm A (Combo)": "#306998", "Arm B (Mono)": "#9370DB"}

# Create pygal HorizontalBar as base structure
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#cccccc",
    colors=("#306998", "#9370DB"),
    title_font_size=56,
    label_font_size=22,
    major_label_font_size=22,
    legend_font_size=26,
    value_font_size=20,
    tooltip_font_size=22,
)

num_patients = len(patient_ids)
max_duration = float(np.ceil(max(durations) / 5) * 5)

chart = pygal.HorizontalBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="swimmer-clinical-timeline \u00b7 pygal \u00b7 pyplots.ai",
    show_legend=False,
    print_values=False,
    show_y_guides=False,
    show_x_guides=False,
    show_x_labels=False,
    margin=50,
    margin_left=50,
    margin_bottom=220,
    spacing=8,
    range=(0, 100),
)

chart.x_labels = patient_ids

# Add placeholder series (legend disabled, we draw our own)
chart.add("", [None] * num_patients)

# Render base SVG
svg_string = chart.render().decode("utf-8")

# Extract plot area coordinates from SVG
PLOT_ORIGIN_X = 400
PLOT_ORIGIN_Y = 130
PLOT_WIDTH = 4300
PLOT_HEIGHT = 2200

row_height = PLOT_HEIGHT / num_patients
bar_height = row_height * 0.6

# Build swimmer bars and event markers
elements = []

for i in range(num_patients):
    arm = arms[i]
    dur = durations[i]
    color = arm_colors[arm]

    # Bar width proportional to duration
    bar_width = (dur / max_duration) * PLOT_WIDTH

    # Y position (first patient at top)
    reversed_i = num_patients - 1 - i
    y_center = PLOT_ORIGIN_Y + (reversed_i + 0.5) * row_height
    y_top = y_center - bar_height / 2

    # Treatment duration bar
    elements.append(
        f'<rect x="{PLOT_ORIGIN_X:.1f}" y="{y_top:.1f}" '
        f'width="{bar_width:.1f}" height="{bar_height:.1f}" '
        f'fill="{color}" rx="3" ry="3" opacity="0.75">'
        f"<title>{patient_ids[i]} | {arm} | {dur:.1f} weeks"
        f"{'  (ongoing)' if ongoing[i] else ''}</title></rect>"
    )

    # Ongoing arrow indicator
    if ongoing[i]:
        arrow_x = PLOT_ORIGIN_X + bar_width
        arrow_size = 14
        elements.append(
            f'<polygon points="{arrow_x:.1f},{y_center - arrow_size:.1f} '
            f"{arrow_x + arrow_size * 2:.1f},{y_center:.1f} "
            f'{arrow_x:.1f},{y_center + arrow_size:.1f}" '
            f'fill="{color}" opacity="0.95"/>'
        )

    # Event markers
    for event_type, event_time in events[i]:
        cfg = event_config[event_type]
        marker_x = PLOT_ORIGIN_X + (event_time / max_duration) * PLOT_WIDTH
        marker_size = 18

        if event_type == "partial_response":
            # Triangle
            elements.append(
                f'<polygon points="{marker_x:.1f},{y_center - marker_size:.1f} '
                f"{marker_x - marker_size * 0.8:.1f},{y_center + marker_size * 0.6:.1f} "
                f'{marker_x + marker_size * 0.8:.1f},{y_center + marker_size * 0.6:.1f}" '
                f'fill="{cfg["color"]}" stroke="white" stroke-width="1.5">'
                f"<title>{cfg['label']} at {event_time:.1f} weeks</title></polygon>"
            )
        elif event_type == "complete_response":
            # Star (5-point)
            points = []
            for j in range(10):
                angle = -np.pi / 2 + j * np.pi / 5
                r = marker_size if j % 2 == 0 else marker_size * 0.45
                px = marker_x + r * np.cos(angle)
                py = y_center + r * np.sin(angle)
                points.append(f"{px:.1f},{py:.1f}")
            elements.append(
                f'<polygon points="{" ".join(points)}" '
                f'fill="{cfg["color"]}" stroke="white" stroke-width="1.5">'
                f"<title>{cfg['label']} at {event_time:.1f} weeks</title></polygon>"
            )
        elif event_type == "progressive_disease":
            # Diamond
            elements.append(
                f'<polygon points="{marker_x:.1f},{y_center - marker_size:.1f} '
                f"{marker_x + marker_size * 0.8:.1f},{y_center:.1f} "
                f"{marker_x:.1f},{y_center + marker_size:.1f} "
                f'{marker_x - marker_size * 0.8:.1f},{y_center:.1f}" '
                f'fill="{cfg["color"]}" stroke="white" stroke-width="1.5">'
                f"<title>{cfg['label']} at {event_time:.1f} weeks</title></polygon>"
            )
        elif event_type == "adverse_event":
            # Square
            half = marker_size * 0.7
            elements.append(
                f'<rect x="{marker_x - half:.1f}" y="{y_center - half:.1f}" '
                f'width="{half * 2:.1f}" height="{half * 2:.1f}" '
                f'fill="{cfg["color"]}" stroke="white" stroke-width="1.5">'
                f"<title>{cfg['label']} at {event_time:.1f} weeks</title></rect>"
            )

# X-axis time markers (weeks)
week_interval = 10
for week in range(0, int(max_duration) + 1, week_interval):
    x_pos = PLOT_ORIGIN_X + (week / max_duration) * PLOT_WIDTH
    # Vertical guide line
    elements.append(
        f'<line x1="{x_pos:.1f}" y1="{PLOT_ORIGIN_Y}" '
        f'x2="{x_pos:.1f}" y2="{PLOT_ORIGIN_Y + PLOT_HEIGHT}" '
        f'stroke="#ddd" stroke-width="1.5" stroke-dasharray="6,4"/>'
    )
    # Week label
    elements.append(
        f'<text x="{x_pos:.1f}" y="{PLOT_ORIGIN_Y + PLOT_HEIGHT + 36}" '
        f'font-family="Consolas, monospace" font-size="24" fill="#333" '
        f'text-anchor="middle">{week}</text>'
    )

# X-axis title
elements.append(
    f'<text x="{PLOT_ORIGIN_X + PLOT_WIDTH / 2}" '
    f'y="{PLOT_ORIGIN_Y + PLOT_HEIGHT + 76}" '
    f'font-family="Consolas, monospace" font-size="30" fill="#333" '
    f'text-anchor="middle">Time on Treatment (Weeks)</text>'
)

# Custom legend below the chart - Row 1: Treatment Arms
legend_y1 = PLOT_ORIGIN_Y + PLOT_HEIGHT + 120
arm_legend = [("#306998", "Arm A (Combo)"), ("#9370DB", "Arm B (Mono)")]
arm_spacing = 320
arm_start_x = PLOT_ORIGIN_X + (PLOT_WIDTH - arm_spacing) / 2
for idx, (color, label) in enumerate(arm_legend):
    x_pos = arm_start_x + idx * arm_spacing
    elements.append(
        f'<rect x="{x_pos - 14:.1f}" y="{legend_y1 - 14:.1f}" '
        f'width="28" height="18" fill="{color}" rx="3" opacity="0.75"/>'
    )
    elements.append(
        f'<text x="{x_pos + 22:.1f}" y="{legend_y1}" '
        f'font-family="Consolas, monospace" font-size="24" fill="#333" '
        f'text-anchor="start">{label}</text>'
    )

# Row 2: Event markers
legend_y2 = legend_y1 + 48
event_legend = [
    ("\u25b2", "#2E8B57", "Partial Response"),
    ("\u2605", "#FFD43B", "Complete Response"),
    ("\u25c6", "#DC143C", "Progressive Disease"),
    ("\u25a0", "#E87D2F", "Adverse Event"),
    ("\u25b6", "#555", "Ongoing"),
]
evt_spacing = 300
total_evt_width = (len(event_legend) - 1) * evt_spacing
evt_start_x = PLOT_ORIGIN_X + (PLOT_WIDTH - total_evt_width) / 2

for idx, (symbol, color, label) in enumerate(event_legend):
    x_pos = evt_start_x + idx * evt_spacing
    elements.append(
        f'<text x="{x_pos:.1f}" y="{legend_y2}" '
        f'font-family="Consolas, monospace" font-size="28" fill="{color}" '
        f'text-anchor="middle">{symbol}</text>'
    )
    elements.append(
        f'<text x="{x_pos + 20:.1f}" y="{legend_y2}" '
        f'font-family="Consolas, monospace" font-size="22" fill="#333" '
        f'text-anchor="start">{label}</text>'
    )

# Inject custom elements before </svg>
all_elements = "\n".join(elements)
svg_output = svg_string.replace("</svg>", f"{all_elements}\n</svg>")

# Remove "No data" text
svg_output = svg_output.replace(">No data<", "><")

# Save
with open("plot.html", "w") as f:
    f.write(svg_output)

cairosvg.svg2png(bytestring=svg_output.encode(), write_to="plot.png")

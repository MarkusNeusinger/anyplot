"""pyplots.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: pygal 3.1.0 | Python 3.14.3
Quality: 73/100 | Created: 2026-03-13
"""

import re

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

# Event types with colorblind-safe palette (Tol's qualitative scheme)
event_config = {
    "partial_response": {"color": "#4477AA", "label": "Partial Response"},
    "complete_response": {"color": "#CCBB44", "label": "Complete Response"},
    "progressive_disease": {"color": "#AA3377", "label": "Progressive Disease"},
    "adverse_event": {"color": "#EE7733", "label": "Adverse Event"},
}

# Generate clinical events for each patient
events = []
for i in range(25):
    patient_events = []
    dur = durations[i]
    if np.random.random() < 0.75:
        pr_time = np.random.uniform(4, min(12, dur - 1))
        patient_events.append(("partial_response", round(pr_time, 1)))
        if np.random.random() < 0.35 and dur > pr_time + 6:
            cr_time = pr_time + np.random.uniform(6, min(16, dur - pr_time - 1))
            patient_events.append(("complete_response", round(cr_time, 1)))
    if np.random.random() < 0.4:
        pd_time = np.random.uniform(max(8, dur * 0.5), dur)
        patient_events.append(("progressive_disease", round(pd_time, 1)))
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

# Sort by duration (longest first for visual hierarchy)
sort_idx = np.argsort(-durations)
patient_ids = [patient_ids[i] for i in sort_idx]
arms = [arms[i] for i in sort_idx]
durations = durations[sort_idx]
events = [events[i] for i in sort_idx]
ongoing = [ongoing[i] for i in sort_idx]

# Arm colors
arm_colors = {"Arm A (Combo)": "#306998", "Arm B (Mono)": "#9370DB"}

# Pygal style with refined aesthetics
custom_style = Style(
    background="white",
    plot_background="#FAFBFC",
    foreground="#333333",
    foreground_strong="#222222",
    foreground_subtle="#E0E0E0",
    colors=("#306998",),
    opacity=".78",
    opacity_hover=".92",
    title_font_size=48,
    label_font_size=22,
    major_label_font_size=24,
    legend_font_size=22,
    value_font_size=18,
    title_font_family="Consolas, monospace",
    label_font_family="Consolas, monospace",
    legend_font_family="Consolas, monospace",
    value_font_family="Consolas, monospace",
)

num_patients = len(patient_ids)
max_duration = float(np.ceil(max(durations) / 10) * 10)

# Create pygal HorizontalBar with real data
chart = pygal.HorizontalBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="swimmer-clinical-timeline \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Time on Treatment (Weeks)",
    show_legend=False,
    print_values=False,
    show_y_guides=True,
    show_x_guides=False,
    margin=50,
    margin_bottom=200,
    spacing=4,
    range=(0, max_duration),
    rounded_bars=4,
    y_labels_major_every=1,
    truncate_label=8,
)

# Pygal HorizontalBar renders bottom-to-top, so reverse data for longest-at-top
reversed_ids = list(reversed(patient_ids))
reversed_arms = list(reversed(arms))
reversed_durs = list(reversed(durations))
reversed_events = list(reversed(events))
reversed_ongoing = list(reversed(ongoing))

chart.x_labels = reversed_ids

# Add real data with per-bar arm colors (pygal renders actual bars)
bar_data = []
for i in range(num_patients):
    bar_data.append(
        {
            "value": float(reversed_durs[i]),
            "color": arm_colors[reversed_arms[i]],
            "label": f"{reversed_ids[i]}: {reversed_durs[i]:.1f} wk ({reversed_arms[i]})",
        }
    )
chart.add("Duration", bar_data)

# Render base SVG with pygal-drawn bars
svg_str = chart.render().decode("utf-8")

# Extract bar positions from rendered SVG using pygal's class attribute
bar_rects = re.findall(
    r'<rect\s+x="([^"]+)"\s+y="([^"]+)"\s+rx="[^"]*"\s+ry="[^"]*"\s+'
    r'width="([^"]+)"\s+height="([^"]+)"\s+class="rect reactive tooltip-trigger"',
    svg_str,
)

# Build bar position list (pygal renders bottom-to-top matching our reversed data)
data_bars = []
for match in bar_rects:
    x, y, w, h = float(match[0]), float(match[1]), float(match[2]), float(match[3])
    data_bars.append({"x": x, "y": y, "width": w, "height": h})

# Sort bars by y descending (bottom-to-top) to match pygal's rendering order
# Pygal renders x_labels[0]/bar_data[0] at the bottom (largest y)
data_bars.sort(key=lambda b: b["y"], reverse=True)

# Build event marker SVG elements
marker_elements = []
marker_size = 30  # Much larger than before (was 18px)

if len(data_bars) == num_patients:
    # Use actual bar positions from pygal's rendered SVG
    for i in range(num_patients):
        bar = data_bars[i]
        bar_x = bar["x"]
        bar_w = bar["width"]
        y_center = bar["y"] + bar["height"] / 2
        dur = reversed_durs[i]

        # Ongoing arrow
        if reversed_ongoing[i]:
            arrow_x = bar_x + bar_w
            arrow_sz = 16
            marker_elements.append(
                f'<polygon points="{arrow_x:.1f},{y_center - arrow_sz:.1f} '
                f"{arrow_x + arrow_sz * 2.2:.1f},{y_center:.1f} "
                f'{arrow_x:.1f},{y_center + arrow_sz:.1f}" '
                f'fill="{arm_colors[reversed_arms[i]]}" opacity="0.95"/>'
            )

        # Event markers
        for event_type, event_time in reversed_events[i]:
            cfg = event_config[event_type]
            mx = bar_x + (event_time / dur) * bar_w
            ms = marker_size

            if event_type == "partial_response":
                # Triangle pointing up
                marker_elements.append(
                    f'<polygon points="{mx:.1f},{y_center - ms:.1f} '
                    f"{mx - ms * 0.85:.1f},{y_center + ms * 0.6:.1f} "
                    f'{mx + ms * 0.85:.1f},{y_center + ms * 0.6:.1f}" '
                    f'fill="{cfg["color"]}" stroke="white" stroke-width="2.5"/>'
                )
            elif event_type == "complete_response":
                # 5-point star
                pts = []
                for j in range(10):
                    angle = -np.pi / 2 + j * np.pi / 5
                    r = ms if j % 2 == 0 else ms * 0.42
                    pts.append(f"{mx + r * np.cos(angle):.1f},{y_center + r * np.sin(angle):.1f}")
                marker_elements.append(
                    f'<polygon points="{" ".join(pts)}" fill="{cfg["color"]}" stroke="white" stroke-width="2.5"/>'
                )
            elif event_type == "progressive_disease":
                # Diamond
                marker_elements.append(
                    f'<polygon points="{mx:.1f},{y_center - ms:.1f} '
                    f"{mx + ms * 0.85:.1f},{y_center:.1f} "
                    f"{mx:.1f},{y_center + ms:.1f} "
                    f'{mx - ms * 0.85:.1f},{y_center:.1f}" '
                    f'fill="{cfg["color"]}" stroke="white" stroke-width="2.5"/>'
                )
            elif event_type == "adverse_event":
                # Square
                half = ms * 0.7
                marker_elements.append(
                    f'<rect x="{mx - half:.1f}" y="{y_center - half:.1f}" '
                    f'width="{half * 2:.1f}" height="{half * 2:.1f}" '
                    f'fill="{cfg["color"]}" stroke="white" stroke-width="2.5" rx="3"/>'
                )

# Custom legend below chart: Row 1 = Arms, Row 2 = Events
# Find chart bottom from the last bar or use estimated position
legend_base_y = 2700 - 160
arm_legend = [("#306998", "Arm A (Combo)"), ("#9370DB", "Arm B (Mono)")]
arm_start_x = 1800
arm_spacing = 420
for idx, (color, label) in enumerate(arm_legend):
    x_pos = arm_start_x + idx * arm_spacing
    marker_elements.append(
        f'<rect x="{x_pos:.1f}" y="{legend_base_y - 12:.1f}" '
        f'width="32" height="20" fill="{color}" rx="3" opacity="0.78"/>'
    )
    marker_elements.append(
        f'<text x="{x_pos + 42:.1f}" y="{legend_base_y + 4:.1f}" '
        f'font-family="Consolas, monospace" font-size="24" fill="#333">{label}</text>'
    )

# Row 2: Event markers legend
legend_y2 = legend_base_y + 48
event_legend = [
    ("\u25b2", "#4477AA", "Partial Response"),
    ("\u2605", "#CCBB44", "Complete Response"),
    ("\u25c6", "#AA3377", "Progressive Disease"),
    ("\u25a0", "#EE7733", "Adverse Event"),
    ("\u25b6", "#555", "Ongoing"),
]
evt_spacing = 320
evt_start_x = 1200
for idx, (symbol, color, label) in enumerate(event_legend):
    x_pos = evt_start_x + idx * evt_spacing
    marker_elements.append(
        f'<text x="{x_pos:.1f}" y="{legend_y2:.1f}" '
        f'font-family="Consolas, monospace" font-size="30" fill="{color}" '
        f'text-anchor="middle">{symbol}</text>'
    )
    marker_elements.append(
        f'<text x="{x_pos + 22:.1f}" y="{legend_y2:.1f}" '
        f'font-family="Consolas, monospace" font-size="22" fill="#333" '
        f'text-anchor="start">{label}</text>'
    )

# Inject markers before </svg>
all_markers = "\n".join(marker_elements)
svg_output = svg_str.replace("</svg>", f"{all_markers}\n</svg>")
svg_output = svg_output.replace(">No data<", "><")

# Save
with open("plot.html", "w") as f:
    f.write(svg_output)

cairosvg.svg2png(bytestring=svg_output.encode(), write_to="plot.png")

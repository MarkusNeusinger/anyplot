""" pyplots.ai
swimmer-clinical-timeline: Swimmer Plot for Clinical Trial Timelines
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-13
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, FactorRange, HoverTool, Label, Legend, LegendItem, Range1d, Span
from bokeh.plotting import figure
from bokeh.resources import CDN


# Data - Simulated Phase II oncology trial with 25 patients across two treatment arms
np.random.seed(42)

n_patients = 25
patient_ids = [f"PT-{i + 1:03d}" for i in range(n_patients)]
arms = np.random.choice(["Arm A (Combo)", "Arm B (Mono)"], size=n_patients, p=[0.52, 0.48])
durations = np.round(np.random.exponential(scale=18, size=n_patients) + 4, 1)
durations = np.clip(durations, 4, 52)

# Generate clinical events for each patient
events_time = []
events_type = []
events_patient = []
events_label = []
ongoing_patients = set()

event_labels = {
    "partial_response": "Partial Response",
    "complete_response": "Complete Response",
    "progressive_disease": "Progressive Disease",
    "adverse_event": "Adverse Event",
}

for i in range(n_patients):
    dur = durations[i]
    patient_events = []

    if np.random.random() < 0.6:
        t = np.round(np.random.uniform(4, min(dur * 0.4, 12)), 1)
        patient_events.append((t, "partial_response"))

    if np.random.random() < 0.3 and dur > 16:
        t = np.round(np.random.uniform(12, min(dur * 0.6, 24)), 1)
        patient_events.append((t, "complete_response"))

    if np.random.random() < 0.35:
        t = np.round(np.random.uniform(2, dur * 0.8), 1)
        patient_events.append((t, "adverse_event"))

    if np.random.random() < 0.4 and dur < 30:
        t = np.round(dur - np.random.uniform(0, 2), 1)
        patient_events.append((t, "progressive_disease"))

    if dur > 25 and not any(e[1] == "progressive_disease" for e in patient_events):
        ongoing_patients.add(i)

    for t, etype in patient_events:
        events_time.append(t)
        events_type.append(etype)
        events_patient.append(patient_ids[i])
        events_label.append(event_labels[etype])

# Sort patients by duration (longest at top)
sort_idx = np.argsort(durations)[::-1]
sorted_patient_ids = [patient_ids[i] for i in sort_idx]
sorted_durations = [durations[i] for i in sort_idx]
sorted_arms = [arms[i] for i in sort_idx]

# Muted, cohesive palette: deep teal for Arm A, warm terracotta for Arm B
arm_colors = {"Arm A (Combo)": "#306998", "Arm B (Mono)": "#C46B4A"}

# Compute median duration for reference line
median_duration = float(np.median(durations))

# Plot
p = figure(
    y_range=FactorRange(*sorted_patient_ids),
    width=4800,
    height=2700,
    title="swimmer-clinical-timeline · bokeh · pyplots.ai",
    x_axis_label="Time on Study (Weeks)",
    toolbar_location="above",
)

# Horizontal bars per treatment arm with hover data
for arm_name, arm_color in arm_colors.items():
    idx = [i for i, a in enumerate(sorted_arms) if a == arm_name]
    source = ColumnDataSource(
        data={
            "y": [sorted_patient_ids[i] for i in idx],
            "right": [sorted_durations[i] for i in idx],
            "arm": [arm_name] * len(idx),
            "dur_str": [f"{sorted_durations[i]:.1f} weeks" for i in idx],
            "status": ["Ongoing" if sort_idx[i] in ongoing_patients else "Completed/Progressed" for i in idx],
        }
    )
    renderer = p.hbar(
        y="y",
        right="right",
        left=0,
        height=0.6,
        color=arm_color,
        alpha=0.88,
        line_color="#ffffff",
        line_width=1,
        source=source,
    )
    # Store renderers for legend
    if arm_name == "Arm A (Combo)":
        bars_a = renderer
    else:
        bars_b = renderer

# Add HoverTool for bars (Bokeh-specific interactivity)
bar_hover = HoverTool(
    renderers=[bars_a, bars_b],
    tooltips=[("Patient", "@y"), ("Treatment", "@arm"), ("Duration", "@dur_str"), ("Status", "@status")],
    point_policy="follow_mouse",
)
p.add_tools(bar_hover)

# Colorblind-safe event marker palette (blue/orange/purple/teal — no red/green)
event_marker_config = {
    "partial_response": {"marker": "triangle", "color": "#009E73", "size": 24},
    "complete_response": {"marker": "star", "color": "#CC79A7", "size": 28},
    "progressive_disease": {"marker": "diamond", "color": "#D55E00", "size": 24},
    "adverse_event": {"marker": "square", "color": "#F0E442", "size": 20},
}

# Plot event markers using scatter() with marker parameter
event_renderers = {}
for etype, config in event_marker_config.items():
    mask = [j for j in range(len(events_type)) if events_type[j] == etype]
    if not mask:
        continue
    source_evt = ColumnDataSource(
        data={
            "x": [events_time[j] for j in mask],
            "y": [events_patient[j] for j in mask],
            "event": [events_label[j] for j in mask],
            "week": [f"Week {events_time[j]:.1f}" for j in mask],
        }
    )
    r = p.scatter(
        x="x",
        y="y",
        source=source_evt,
        marker=config["marker"],
        size=config["size"],
        color=config["color"],
        line_color="#222222",
        line_width=2.5,
    )
    event_renderers[etype] = r

# HoverTool for event markers
evt_hover = HoverTool(
    renderers=list(event_renderers.values()),
    tooltips=[("Patient", "@y"), ("Event", "@event"), ("Time", "@week")],
    point_policy="snap_to_data",
)
p.add_tools(evt_hover)

# Ongoing indicators (right-pointing triangles at bar ends)
ongoing_idx_sorted = [i for i in range(n_patients) if sort_idx[i] in ongoing_patients]
ongoing_r = None
if ongoing_idx_sorted:
    arrow_x = [sorted_durations[i] + 1.0 for i in ongoing_idx_sorted]
    arrow_y = [sorted_patient_ids[i] for i in ongoing_idx_sorted]
    arrow_source = ColumnDataSource(data={"x": arrow_x, "y": arrow_y})
    ongoing_r = p.scatter(
        x="x",
        y="y",
        source=arrow_source,
        marker="triangle",
        size=24,
        color="#555555",
        angle=np.pi / 2 * 3,
        line_color="#555555",
    )

# Median duration reference line for visual storytelling
median_span = Span(
    location=median_duration,
    dimension="height",
    line_color="#888888",
    line_dash="dotted",
    line_width=2.5,
    line_alpha=0.7,
)
p.add_layout(median_span)

# Label for median line
median_label = Label(
    x=median_duration,
    y=2350,
    y_units="screen",
    text=f"Median: {median_duration:.1f} wk",
    text_font_size="20pt",
    text_color="#555555",
    text_font_style="italic",
    x_offset=10,
)
p.add_layout(median_label)

# Style
p.title.text_font_size = "36pt"
p.title.text_color = "#2B2B2B"

p.xaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "20pt"
p.xaxis.axis_label_text_color = "#444444"
p.x_range = Range1d(-0.5, max(sorted_durations) + 4)

p.yaxis.axis_label = "Patient"
p.yaxis.axis_label_text_font_size = "28pt"
p.yaxis.major_label_text_font_size = "18pt"
p.yaxis.axis_label_text_color = "#444444"

p.xgrid.grid_line_color = None
p.ygrid.grid_line_alpha = 0.12
p.ygrid.grid_line_dash = "dashed"
p.ygrid.grid_line_color = "#cccccc"

p.axis.axis_line_color = "#bbbbbb"
p.axis.major_tick_line_color = "#bbbbbb"
p.axis.minor_tick_line_color = None

p.background_fill_color = "#f7f7f7"
p.border_fill_color = "#ffffff"
p.outline_line_color = None

# Legend
legend_items = [
    LegendItem(label="Arm A (Combo)", renderers=[bars_a]),
    LegendItem(label="Arm B (Mono)", renderers=[bars_b]),
]
for etype, label in [
    ("partial_response", "Partial Response"),
    ("complete_response", "Complete Response"),
    ("progressive_disease", "Progressive Disease"),
    ("adverse_event", "Adverse Event"),
]:
    if etype in event_renderers:
        legend_items.append(LegendItem(label=label, renderers=[event_renderers[etype]]))

if ongoing_r is not None:
    legend_items.append(LegendItem(label="Ongoing", renderers=[ongoing_r]))

legend = Legend(items=legend_items, location="center_right", orientation="vertical")
legend.label_text_font_size = "22pt"
legend.glyph_height = 35
legend.glyph_width = 35
legend.spacing = 14
legend.padding = 30
legend.background_fill_alpha = 0.85
legend.background_fill_color = "#ffffff"
legend.border_line_color = "#dddddd"
legend.border_line_width = 1
p.add_layout(legend)

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Swimmer Clinical Timeline")

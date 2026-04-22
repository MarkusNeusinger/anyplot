""" pyplots.ai
campbell-basic: Campbell Diagram
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 95/100 | Created: 2026-02-15
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import BoxAnnotation, ColumnDataSource, HoverTool, Label, Legend, LegendItem, Range1d, Span
from bokeh.plotting import figure


# Data
speeds = np.linspace(0, 6000, 100)

# Natural frequency modes (Hz) with pronounced rotordynamic behavior
mode_1_bending = 25 + 0.008 * speeds + 3.5 * np.sin(speeds / 2800 * np.pi)
mode_2_bending = 62 - 0.006 * speeds + 2.0 * np.sin(speeds / 2200 * np.pi)
mode_1_torsional = 85 + 0.005 * speeds
mode_axial = 110 - 0.004 * speeds + 2.5 * np.cos(speeds / 3200 * np.pi)
mode_3_bending = 130 + 0.010 * speeds - 4.0 * np.cos(speeds / 2600 * np.pi)

modes = {
    "1st Bending": mode_1_bending,
    "2nd Bending": mode_2_bending,
    "1st Torsional": mode_1_torsional,
    "Axial": mode_axial,
    "3rd Bending": mode_3_bending,
}

# Engine order lines: frequency = order * speed / 60
engine_orders = [1, 2, 3]
eo_frequencies = {order: order * speeds / 60 for order in engine_orders}

# Find critical speed intersections via sign-change interpolation
critical_speeds_rpm = []
critical_speeds_freq = []
critical_speed_labels = []
critical_in_operating = []

for order in engine_orders:
    eo_freq = eo_frequencies[order]
    for mode_name, mode_freq in modes.items():
        diff = eo_freq - mode_freq
        sign_changes = np.where(np.diff(np.sign(diff)))[0]
        for idx in sign_changes:
            denom = abs(diff[idx]) + abs(diff[idx + 1])
            if denom == 0:
                continue
            frac = abs(diff[idx]) / denom
            rpm_val = speeds[idx] + frac * (speeds[idx + 1] - speeds[idx])
            freq_val = mode_freq[idx] + frac * (mode_freq[idx + 1] - mode_freq[idx])
            if 100 < rpm_val < 5900 and 5 < freq_val < 195:
                critical_speeds_rpm.append(rpm_val)
                critical_speeds_freq.append(freq_val)
                critical_speed_labels.append(f"{order}x × {mode_name}")
                critical_in_operating.append(3000 <= rpm_val <= 5000)

# Compute y-range
all_freqs = np.concatenate(list(modes.values()))
y_max_data = max(np.max(all_freqs), max(critical_speeds_freq) if critical_speeds_freq else 0)
y_max = min(int(np.ceil(y_max_data / 10) * 10) + 15, 200)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="campbell-basic · bokeh · pyplots.ai",
    x_axis_label="Rotational Speed (RPM)",
    y_axis_label="Frequency (Hz)",
    x_range=Range1d(-100, 6300),
    y_range=Range1d(0, y_max),
)

# Operating range shading (3000–5000 RPM)
operating_zone = BoxAnnotation(
    left=3000,
    right=5000,
    fill_color="#306998",
    fill_alpha=0.06,
    line_color="#306998",
    line_alpha=0.3,
    line_dash="dotted",
    line_width=2,
)
p.add_layout(operating_zone)

# Operating range boundary lines for crisp delineation
for rpm_boundary in [3000, 5000]:
    boundary_line = Span(
        location=rpm_boundary,
        dimension="height",
        line_color="#306998",
        line_alpha=0.35,
        line_width=2,
        line_dash="dashed",
    )
    p.add_layout(boundary_line)

# Operating range label
op_label = Label(
    x=4000,
    y=y_max * 0.04,
    text="Operating Range (3000–5000 RPM)",
    text_font_size="18pt",
    text_color="#306998",
    text_alpha=0.8,
    text_align="center",
    text_font_style="bold italic",
)
p.add_layout(op_label)

# Danger zone highlighting around critical speeds within operating range
for rpm_val, freq_val, in_op in zip(critical_speeds_rpm, critical_speeds_freq, critical_in_operating, strict=True):
    if in_op:
        danger = BoxAnnotation(
            left=rpm_val - 120,
            right=rpm_val + 120,
            bottom=freq_val - 4,
            top=freq_val + 4,
            fill_color="#C44E52",
            fill_alpha=0.10,
            line_color="#C44E52",
            line_alpha=0.25,
            line_width=1,
        )
        p.add_layout(danger)

# Natural frequency mode colors — distinct, colorblind-safe palette
# Python Blue, amber, rose, violet, teal — all perceptually distinct
mode_colors = ["#306998", "#E8A838", "#C44E52", "#7A68A6", "#48A9A6"]

# Plot natural frequency curves
legend_items = []
for i, (mode_name, mode_freq) in enumerate(modes.items()):
    source = ColumnDataSource(data={"speed": speeds, "freq": mode_freq})
    line = p.line(x="speed", y="freq", source=source, line_width=4, line_color=mode_colors[i], line_alpha=0.9)
    legend_items.append(LegendItem(label=mode_name, renderers=[line]))

# Engine order lines (lighter, thinner to reduce visual clutter)
eo_color = "#666666"

for order in engine_orders:
    eo_freq = eo_frequencies[order]
    mask = eo_freq <= y_max
    clipped_speeds = speeds[mask]
    clipped_freq = eo_freq[mask]

    source = ColumnDataSource(data={"speed": clipped_speeds, "freq": clipped_freq})
    line = p.line(
        x="speed", y="freq", source=source, line_width=2, line_color=eo_color, line_dash=[12, 8], line_alpha=0.6
    )
    legend_items.append(LegendItem(label=f"{order}x EO", renderers=[line]))

# Engine order labels — positioned at right edge, offset to avoid crowding
for order in engine_orders:
    freq_at_max = order * 6000 / 60
    if freq_at_max > y_max - 5:
        label_rpm = (y_max - 12) * 60 / order
        label_freq = y_max - 10
    else:
        label_rpm = 5850
        label_freq = freq_at_max

    label = Label(
        x=label_rpm,
        y=label_freq,
        text=f" {order}x",
        text_font_size="20pt",
        text_color="#555555",
        text_font_style="bold",
        text_baseline="middle",
    )
    p.add_layout(label)

# Critical speed markers — dark orange, clearly distinct from crimson mode lines
if critical_speeds_rpm:
    crit_source = ColumnDataSource(
        data={
            "rpm": critical_speeds_rpm,
            "freq": critical_speeds_freq,
            "label": critical_speed_labels,
            "rpm_display": [f"{r:.0f}" for r in critical_speeds_rpm],
            "freq_display": [f"{f:.1f}" for f in critical_speeds_freq],
            "in_operating": ["YES — CAUTION" if op else "No" for op in critical_in_operating],
        }
    )
    crit_scatter = p.scatter(
        x="rpm",
        y="freq",
        source=crit_source,
        marker="diamond",
        size=28,
        fill_color="#E65100",
        line_color="#FFFFFF",
        line_width=2.5,
        fill_alpha=0.9,
    )
    legend_items.append(LegendItem(label="Critical Speed", renderers=[crit_scatter]))

    # HoverTool with enriched tooltips (Bokeh distinctive feature)
    hover = HoverTool(
        renderers=[crit_scatter],
        tooltips=[
            ("Intersection", "@label"),
            ("RPM", "@rpm_display"),
            ("Frequency", "@freq_display Hz"),
            ("In Operating Range?", "@in_operating"),
        ],
        mode="mouse",
    )
    p.add_tools(hover)

    # Annotate the most critical intersection in the operating range
    op_crits = [
        (r, f, lbl)
        for r, f, lbl, op in zip(
            critical_speeds_rpm, critical_speeds_freq, critical_speed_labels, critical_in_operating, strict=True
        )
        if op
    ]
    if op_crits:
        op_crits.sort(key=lambda x: x[1])
        worst_rpm, worst_freq, worst_label = op_crits[0]
        annotation = Label(
            x=worst_rpm + 280,
            y=worst_freq + 8,
            text=f"⚠ {worst_label} @ {worst_rpm:.0f} RPM",
            text_font_size="15pt",
            text_color="#E65100",
            text_font_style="bold",
            text_alpha=0.85,
        )
        p.add_layout(annotation)

# Legend — positioned top-left, compact to minimize data overlap
legend = Legend(
    items=legend_items,
    location="top_left",
    label_text_font_size="16pt",
    glyph_width=50,
    glyph_height=26,
    spacing=10,
    padding=16,
    background_fill_color="#FFFFFF",
    background_fill_alpha=0.88,
    border_line_color="#CCCCCC",
    border_line_alpha=0.25,
    border_line_width=1,
)
p.add_layout(legend)

# Title styling
p.title.text_font_size = "28pt"
p.title.align = "center"
p.title.text_color = "#222222"

# Axis styling
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.axis_label_text_color = "#333333"
p.yaxis.axis_label_text_color = "#333333"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"
p.xaxis.axis_line_color = "#BBBBBB"
p.yaxis.axis_line_color = "#BBBBBB"
p.xaxis.major_tick_line_color = "#BBBBBB"
p.yaxis.major_tick_line_color = "#BBBBBB"
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Grid styling (subtle, refined)
p.xgrid.grid_line_color = "#E0E0E0"
p.xgrid.grid_line_alpha = 0.4
p.ygrid.grid_line_color = "#E0E0E0"
p.ygrid.grid_line_alpha = 0.4

# Background and frame
p.background_fill_color = "#FAFAFA"
p.border_fill_color = "#FFFFFF"
p.outline_line_color = None

# Save
export_png(p, filename="plot.png")

output_file("plot.html")
save(p)

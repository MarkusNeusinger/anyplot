""" pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-05
"""

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Data - Simulated outbreak with two waves (propagated transmission pattern)
np.random.seed(42)
dates = pd.date_range("2024-01-15", periods=90, freq="D")

# Wave 1: peaks around day 20, Wave 2: peaks around day 55
days = np.arange(90)
wave1 = 35 * np.exp(-0.5 * ((days - 20) / 7) ** 2)
wave2 = 50 * np.exp(-0.5 * ((days - 55) / 9) ** 2)
baseline = 2 + 3 * np.random.rand(90)
total_signal = wave1 + wave2 + baseline

# Split into confirmed, probable, suspect cases
confirmed_frac = np.clip(0.6 + 0.15 * np.sin(days / 15), 0.45, 0.75)
probable_frac = np.clip(0.25 + 0.05 * np.cos(days / 10), 0.15, 0.35)
suspect_frac = 1.0 - confirmed_frac - probable_frac

confirmed = np.round(total_signal * confirmed_frac).astype(int)
probable = np.round(total_signal * probable_frac).astype(int)
suspect = np.round(total_signal * suspect_frac).astype(int)
daily_total = confirmed + probable + suspect

# Key intervention events with spaced-out dates to avoid label crowding
interventions = {
    10: "Cluster Identified",
    28: "Contact Tracing",
    42: "Quarantine Order",
    62: "Vaccination Drive",
    80: "Outbreak Contained",
}

# X-axis labels — intervention dates get marker + event name
date_labels = []
for i, d in enumerate(dates):
    fmt = d.strftime("%b %d")
    if i in interventions:
        date_labels.append(f"\u25bc {interventions[i]}")
    else:
        date_labels.append(fmt)

# Major labels: monthly anchors + intervention dates, filtered to avoid crowding
monthly_set = {0, 31, 59, 89}
intervention_set = set(interventions.keys())
major_indices = sorted(monthly_set | intervention_set)
# Remove monthly ticks within 5 days of an intervention label
filtered_indices = []
for idx in major_indices:
    if idx in intervention_set:
        filtered_indices.append(idx)
    elif all(abs(idx - iv) > 5 for iv in intervention_set):
        filtered_indices.append(idx)
major_labels = [date_labels[i] for i in filtered_indices]

# Build series with rich tooltip labels for interactive HTML
confirmed_series = []
probable_series = []
suspect_series = []
for i in range(90):
    day_str = dates[i].strftime("%b %d, %Y")
    total_day = int(daily_total[i])
    event = interventions.get(i)
    tip = f"{day_str} \u2014 {total_day} total cases"
    if event:
        tip = f"\u26a0 {event}\n{tip}"
    confirmed_series.append({"value": int(confirmed[i]), "label": tip})
    probable_series.append({"value": int(probable[i]), "label": tip})
    suspect_series.append({"value": int(suspect[i]), "label": tip})

# Style — publication-quality epidemiological palette
custom_style = Style(
    background="#FAFAF7",
    plot_background="#FAFAF7",
    foreground="#2D2D2D",
    foreground_strong="#1A1A1A",
    foreground_subtle="#D8D8D4",
    colors=("#1B5E8C", "#E8A838", "#8B4049"),
    title_font_size=58,
    label_font_size=26,
    major_label_font_size=28,
    legend_font_size=34,
    value_font_size=22,
    tooltip_font_size=26,
    stroke_width=1,
    opacity=0.92,
    opacity_hover=1.0,
    title_font_family="DejaVu Sans",
    label_font_family="DejaVu Sans",
    legend_font_family="DejaVu Sans",
    value_font_family="DejaVu Sans",
)

# Chart — clean stacked bar with polished layout
chart = pygal.StackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="Epidemic Curve (Respiratory Outbreak) \u00b7 histogram-epidemic \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Date of Symptom Onset",
    y_title="New Cases (Daily)",
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    legend_box_size=24,
    legend_at_bottom_columns=3,
    margin=50,
    margin_bottom=200,
    margin_right=80,
    spacing=2,
    rounded_bars=3,
    truncate_legend=-1,
    truncate_label=-1,
    x_label_rotation=45,
    show_minor_x_labels=False,
    print_values=False,
    range=(0, int(np.max(daily_total) * 1.1)),
    value_formatter=lambda x: f"{int(x):,}" if x else "",
)

chart.x_labels = date_labels
chart.x_labels_major = major_labels

# Add stacked epidemic series
chart.add("Confirmed", confirmed_series)
chart.add("Probable", probable_series)
chart.add("Suspect", suspect_series)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")

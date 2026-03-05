"""pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: pygal 3.1.0 | Python 3.14.3
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

# Key intervention events (day index -> label)
interventions = {10: "Cluster ID", 25: "Contact Tracing", 40: "Quarantine", 60: "Vaccination", 75: "Contained"}

# X-axis labels — annotate intervention dates with event name
date_labels = []
for i, d in enumerate(dates):
    fmt = d.strftime("%b %d")
    if i in interventions:
        date_labels.append(f"{fmt} [{interventions[i]}]")
    else:
        date_labels.append(fmt)

# Major labels: weekly ticks + all intervention dates
weekly_set = {i for i in range(90) if i % 7 == 0}
intervention_set = set(interventions.keys())
major_indices = sorted(weekly_set | intervention_set)
major_labels = [date_labels[i] for i in major_indices]

# Build series with intervention annotations as tooltip labels
confirmed_series = []
probable_series = []
suspect_series = []
for i in range(90):
    label = interventions.get(i)
    if label:
        confirmed_series.append({"value": int(confirmed[i]), "label": label})
        probable_series.append({"value": int(probable[i]), "label": label})
        suspect_series.append({"value": int(suspect[i]), "label": label})
    else:
        confirmed_series.append(int(confirmed[i]))
        probable_series.append(int(probable[i]))
        suspect_series.append(int(suspect[i]))

# Style — refined palette for epidemiological data
custom_style = Style(
    background="#FAFAF7",
    plot_background="#FAFAF7",
    foreground="#2D2D2D",
    foreground_strong="#1A1A1A",
    foreground_subtle="#D4D4D0",
    colors=("#1B5E8C", "#D4882C", "#B84747"),
    title_font_size=60,
    label_font_size=28,
    major_label_font_size=30,
    legend_font_size=36,
    value_font_size=24,
    tooltip_font_size=28,
    stroke_width=1,
    opacity=0.92,
    opacity_hover=1.0,
)

# Chart with x-guides to draw vertical lines at intervention dates
chart = pygal.StackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="Epidemic Curve (Respiratory Outbreak) · histogram-epidemic · pygal · pyplots.ai",
    x_title="Date of Symptom Onset",
    y_title="New Cases",
    show_y_guides=True,
    show_x_guides=True,
    legend_at_bottom=True,
    legend_box_size=28,
    margin=50,
    margin_bottom=160,
    spacing=2,
    truncate_legend=-1,
    truncate_label=-1,
    x_label_rotation=45,
    show_minor_x_labels=False,
    print_values=False,
)

chart.x_labels = date_labels
chart.x_labels_major = major_labels

# Add stacked epidemic series with annotated intervention events
chart.add("Confirmed", confirmed_series)
chart.add("Probable", probable_series)
chart.add("Suspect", suspect_series)

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")

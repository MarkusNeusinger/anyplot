""" anyplot.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: pygal 3.1.3 | Python 3.14.10
Quality: 81/100 | Updated: 2026-11-28
"""

import os

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome tokens (Imprint palette reference)
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
ONSET_DATE = "Date of Symptom Onset"  # role: onset_date
CASE_COUNT = "New Cases (Daily)"  # role: case_count
CASE_TYPE = "Case classification"  # role: case_type
EVENT_LABEL = "Intervention"  # role: events

# Data: replace this block with your own table, for example df = pd.read_csv("cases.csv")
# Simulated respiratory outbreak with two waves (propagated transmission); one row per day and case type.
# The intervention column names the event on its date and is empty elsewhere.
np.random.seed(42)
n_days = 90
dates = pd.date_range("2024-01-15", periods=n_days, freq="D")
days = np.arange(n_days)
wave1 = 35 * np.exp(-0.5 * ((days - 20) / 7) ** 2)
wave2 = 50 * np.exp(-0.5 * ((days - 55) / 9) ** 2)
total_signal = wave1 + wave2 + 2 + 3 * np.random.rand(n_days)

confirmed_frac = np.clip(0.6 + 0.15 * np.sin(days / 15), 0.45, 0.75)
probable_frac = np.clip(0.25 + 0.05 * np.cos(days / 10), 0.15, 0.35)
suspect_frac = 1.0 - confirmed_frac - probable_frac

events = {
    10: "Cluster Identified",
    28: "Contact Tracing",
    42: "Quarantine Order",
    62: "Vaccination Drive",
    80: "Outbreak Contained",
}
event_by_day = [events.get(i) for i in range(n_days)]

df = pd.DataFrame(
    {
        ONSET_DATE: np.repeat(dates, 3),
        CASE_TYPE: ["Confirmed", "Probable", "Suspect"] * n_days,
        CASE_COUNT: np.round(np.column_stack([total_signal * f for f in (confirmed_frac, probable_frac, suspect_frac)]))
        .astype(int)
        .ravel(),
        EVENT_LABEL: np.repeat(event_by_day, 3),
    }
)

# Plot
table = df.pivot_table(index=ONSET_DATE, columns=CASE_TYPE, values=CASE_COUNT, sort=False)
day_totals = table.sum(axis=1)
n_bins = len(table)
event_rows = df.drop_duplicates(ONSET_DATE).reset_index(drop=True)[EVENT_LABEL]
intervention_idx = [i for i, label in enumerate(event_rows) if isinstance(label, str)]

# X-axis labels: intervention dates get a triangle marker + event name
date_labels = [
    f"▼ {event_rows[i]}" if i in intervention_idx else d.strftime("%b %d") for i, d in enumerate(table.index)
]

# Major labels: first and last date plus interventions, without crowding an intervention
major_idx = sorted(
    set(intervention_idx) | {i for i in (0, n_bins - 1) if all(abs(i - iv) > 5 for iv in intervention_idx)}
)
major_labels = [date_labels[i] for i in major_idx]

# Series with rich tooltip dicts for the interactive HTML
series = {name: [] for name in table.columns}
for i, day in enumerate(table.index):
    tip = f"{day.strftime('%b %d, %Y')} — {int(day_totals.iloc[i])} total cases"
    if i in intervention_idx:
        tip = f"⚠ {event_rows[i]}\n{tip}"
    for name in table.columns:
        count = table[name].iloc[i]
        series[name].append({"value": None if pd.isna(count) else int(count), "label": tip})

# Title font size scaled for length (formula: round(66 * 67 / len(title)))
title = "Epidemic Curve (Respiratory Outbreak) · histogram-epidemic · python · pygal · anyplot.ai"
title_font_size = round(66 * 67 / len(title))  # prevents overflow at 3200 px

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    guide_stroke_color=INK_MUTED,
    major_guide_stroke_color=INK_MUTED,
    colors=IMPRINT_PALETTE,
    title_font_size=title_font_size,
    label_font_size=44,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    tooltip_font_size=36,
    stroke_width=2.5,
    opacity=0.92,
    opacity_hover=1.0,
)

chart = pygal.StackedBar(
    width=3200,
    height=1800,
    style=custom_style,
    title=title,
    x_title=ONSET_DATE,
    y_title=CASE_COUNT,
    show_y_guides=True,
    show_x_guides=True,
    legend_at_bottom=True,
    legend_box_size=28,
    legend_at_bottom_columns=3,
    margin=60,
    margin_bottom=180,
    margin_right=80,
    spacing=2,
    rounded_bars=3,
    truncate_legend=-1,
    truncate_label=-1,
    x_label_rotation=45,
    show_minor_x_labels=False,
    print_values=False,
    range=(0, int(day_totals.max() * 1.1)),
    value_formatter=lambda x: f"{int(x):,}" if x else "",
)

chart.x_labels = date_labels
chart.x_labels_major = major_labels

for name in table.columns:
    chart.add(str(name), series[name])

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())

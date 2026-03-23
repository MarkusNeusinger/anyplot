""" pyplots.ai
line-load-duration: Load Duration Curve for Energy Systems
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-15
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - synthetic annual hourly load profile for a mid-sized utility
np.random.seed(42)
hours = 8760
time = np.arange(hours)

# Realistic load profile with clear peak/intermediate/base separation
base_load = 400
daily_cycle = 200 * np.sin(2 * np.pi * (time % 24 - 6) / 24)
seasonal = 250 * np.cos(2 * np.pi * (time / 24 - 30) / 365)
weekday_boost = np.where((time // 24) % 7 < 5, 80, 0)
noise = np.random.normal(0, 50, hours)
load_mw = base_load + 350 + daily_cycle + seasonal + weekday_boost + noise
load_mw = np.clip(load_mw, 380, 1250)

# Sort descending to create load duration curve
load_sorted = np.sort(load_mw)[::-1]
hour_index = np.arange(hours)

# Define capacity tiers
base_capacity = 550
intermediate_capacity = 900
peak_capacity = 1100

# Determine region boundaries (where load crosses each tier)
peak_end = int(np.searchsorted(-load_sorted, -peak_capacity))
inter_end = int(np.searchsorted(-load_sorted, -base_capacity))

# Total energy consumption (area under curve)
total_energy_gwh = np.trapezoid(load_sorted) / 1000

# Downsample for performance (8760 points is a lot for Vega)
step = 10
idx = np.arange(0, hours, step)
idx = np.append(idx, hours - 1)
load_ds = load_sorted[idx]
hour_ds = idx.astype(float)

# Build three separate area datasets for colored fill regions
peak_df = pd.DataFrame({"hour": hour_ds[hour_ds <= peak_end], "load_mw": load_ds[: len(hour_ds[hour_ds <= peak_end])]})

inter_mask = (hour_ds >= peak_end) & (hour_ds <= inter_end)
inter_hours = np.concatenate([[peak_end], hour_ds[inter_mask]])
inter_load = np.concatenate([[np.interp(peak_end, hour_ds, load_ds)], load_ds[inter_mask]])
inter_df = pd.DataFrame({"hour": inter_hours, "load_mw": inter_load})

base_mask = hour_ds >= inter_end
base_hours = np.concatenate([[inter_end], hour_ds[base_mask]])
base_load_vals = np.concatenate([[np.interp(inter_end, hour_ds, load_ds)], load_ds[base_mask]])
base_df = pd.DataFrame({"hour": base_hours, "load_mw": base_load_vals})

# Full curve for line overlay
full_df = pd.DataFrame({"hour": hour_ds, "load_mw": load_ds})

# Peak area
peak_area = alt.Chart(peak_df).mark_area(opacity=0.55, color="#8e44ad").encode(x=alt.X("hour:Q"), y=alt.Y("load_mw:Q"))

# Intermediate area
inter_area = (
    alt.Chart(inter_df).mark_area(opacity=0.55, color="#f39c12").encode(x=alt.X("hour:Q"), y=alt.Y("load_mw:Q"))
)

# Base area
base_area = alt.Chart(base_df).mark_area(opacity=0.55, color="#306998").encode(x=alt.X("hour:Q"), y=alt.Y("load_mw:Q"))

# Nearest-point selection for interactive crosshair (Altair-distinctive)
nearest = alt.selection_point(nearest=True, on="pointerover", fields=["hour"], empty=False)

# Line overlay on top of the full curve
line = (
    alt.Chart(full_df)
    .mark_line(color="#1a1a2e", strokeWidth=2.5)
    .encode(
        x=alt.X("hour:Q", title="Hours of Year (ranked)", axis=alt.Axis(format=",d")),
        y=alt.Y("load_mw:Q", title="Power Demand (MW)", scale=alt.Scale(domain=[0, 1400])),
        tooltip=[
            alt.Tooltip("hour:Q", title="Hour Rank", format=",d"),
            alt.Tooltip("load_mw:Q", title="Load (MW)", format=",.0f"),
        ],
    )
)

# Crosshair point that snaps to nearest data point
crosshair_points = (
    alt.Chart(full_df)
    .mark_point(size=120, color="#1a1a2e", filled=True)
    .encode(x="hour:Q", y="load_mw:Q", opacity=alt.condition(nearest, alt.value(1), alt.value(0)))
    .add_params(nearest)
)

# Vertical rule at crosshair position
crosshair_rule = (
    alt.Chart(full_df)
    .mark_rule(color="#555555", strokeDash=[4, 4], strokeWidth=1)
    .encode(x="hour:Q", opacity=alt.condition(nearest, alt.value(0.6), alt.value(0)))
)

# Capacity tier dashed lines
tier_data = pd.DataFrame(
    {
        "label": ["Peak Capacity (1,100 MW)", "Intermediate Capacity (900 MW)", "Base Capacity (550 MW)"],
        "y_val": [peak_capacity, intermediate_capacity, base_capacity],
    }
)

tier_rules = (
    alt.Chart(tier_data)
    .mark_rule(strokeDash=[12, 6], strokeWidth=2, opacity=0.7)
    .encode(y="y_val:Q", color=alt.value("#2c3e50"))
)

tier_labels = (
    alt.Chart(tier_data)
    .mark_text(align="right", dx=-10, dy=-12, fontSize=18, fontWeight="bold", color="#2c3e50")
    .encode(x=alt.value(1580), y="y_val:Q", text="label:N")
)

# Region labels positioned within each area
region_labels_df = pd.DataFrame(
    {
        "hour": [peak_end / 2, (peak_end + inter_end) / 2, (inter_end + 8760) / 2],
        "load_mw": [1150, 750, 470],
        "label": ["Peak Load", "Intermediate Load", "Base Load"],
    }
)

region_labels = (
    alt.Chart(region_labels_df)
    .mark_text(fontSize=18, fontWeight="bold", fontStyle="italic", opacity=0.7)
    .encode(x="hour:Q", y="load_mw:Q", text="label:N", color=alt.value("#2c3e50"))
)

# Energy annotation
energy_df = pd.DataFrame(
    {"hour": [5500], "load_mw": [200], "text": [f"Total Energy: {total_energy_gwh:,.0f} GWh/year"]}
)

energy_label = (
    alt.Chart(energy_df)
    .mark_text(fontSize=18, fontWeight="bold", color="#2c3e50")
    .encode(x="hour:Q", y="load_mw:Q", text="text:N")
)

# Compose - static layers for PNG
chart = (
    alt.layer(peak_area, inter_area, base_area, line, tier_rules, tier_labels, region_labels, energy_label)
    .properties(width=1600, height=900, title=alt.Title("line-load-duration · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.15)
    .configure_view(strokeWidth=0)
)

# Save PNG (static)
chart.save("plot.png", scale_factor=3.0)

# Interactive HTML version with crosshair and zoom/pan
interactive_chart = (
    alt.layer(
        peak_area,
        inter_area,
        base_area,
        line,
        crosshair_points,
        crosshair_rule,
        tier_rules,
        tier_labels,
        region_labels,
        energy_label,
    )
    .properties(width=1600, height=900, title=alt.Title("line-load-duration · altair · pyplots.ai", fontSize=28))
    .configure_axis(labelFontSize=18, titleFontSize=22, gridOpacity=0.15)
    .configure_view(strokeWidth=0)
    .interactive()
)
interactive_chart.save("plot.html")

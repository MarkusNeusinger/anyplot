"""pyplots.ai
heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
Library: altair | Python 3.13
Quality: pending | Created: 2026-03-02
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - synthetic rainflow counting matrix for a steel component under variable-amplitude loading
np.random.seed(42)

n_amp_bins = 20
n_mean_bins = 20
amplitude_edges = np.linspace(25, 500, n_amp_bins + 1)
mean_edges = np.linspace(-200, 200, n_mean_bins + 1)
amplitude_centers = (amplitude_edges[:-1] + amplitude_edges[1:]) / 2
mean_centers = (mean_edges[:-1] + mean_edges[1:]) / 2

# Build count matrix: low amplitude cycles dominate, counts decay with amplitude
amp_grid, mean_grid = np.meshgrid(amplitude_centers, mean_centers, indexing="ij")

# Base distribution: exponential decay in amplitude, Gaussian in mean
base_counts = 5000 * np.exp(-amp_grid / 120) * np.exp(-0.5 * (mean_grid / 100) ** 2)

# Add secondary cluster at moderate amplitude / slight positive mean (e.g., dominant load cycle)
cluster = 800 * np.exp(-0.5 * ((amp_grid - 175) / 50) ** 2 - 0.5 * ((mean_grid - 50) / 40) ** 2)
raw_counts = base_counts + cluster

# Add noise and round to integers
raw_counts += np.random.exponential(scale=5, size=raw_counts.shape)
cycle_counts = np.round(raw_counts).astype(int)
cycle_counts = np.clip(cycle_counts, 0, None)

# Sparsify high-amplitude region (fewer cycles at high stress range)
mask = np.random.rand(*cycle_counts.shape) < 0.3
cycle_counts[(amp_grid > 350) & mask] = 0

# Convert to long-form DataFrame
rows = []
for i, amp in enumerate(amplitude_centers):
    for j, mean_val in enumerate(mean_centers):
        count = int(cycle_counts[i, j])
        if count > 0:
            rows.append(
                {
                    "Amplitude (MPa)": round(amp, 1),
                    "Mean Stress (MPa)": round(mean_val, 1),
                    "Cycle Count": count,
                    "Log Count": float(np.log10(max(count, 1))),
                }
            )

df = pd.DataFrame(rows)

# Plot - rainflow heatmap with sequential colormap, log-scaled
heatmap = (
    alt.Chart(df)
    .mark_rect(cornerRadius=1)
    .encode(
        x=alt.X(
            "Mean Stress (MPa):O",
            title="Mean Stress (MPa)",
            sort=sorted(df["Mean Stress (MPa)"].unique().tolist()),
            axis=alt.Axis(
                labelFontSize=14,
                titleFontSize=20,
                labelAngle=-45,
                labelPadding=6,
                titlePadding=12,
                values=sorted(df["Mean Stress (MPa)"].unique().tolist())[::2],
            ),
        ),
        y=alt.Y(
            "Amplitude (MPa):O",
            title="Stress Amplitude (MPa)",
            sort=sorted(df["Amplitude (MPa)"].unique().tolist(), reverse=True),
            axis=alt.Axis(
                labelFontSize=14,
                titleFontSize=20,
                labelPadding=6,
                titlePadding=12,
                values=sorted(df["Amplitude (MPa)"].unique().tolist())[::2],
            ),
        ),
        color=alt.Color(
            "Log Count:Q",
            scale=alt.Scale(scheme="inferno"),
            legend=alt.Legend(
                title="Cycle Count",
                titleFontSize=18,
                labelFontSize=14,
                gradientLength=400,
                gradientThickness=20,
                orient="right",
                titlePadding=8,
                offset=12,
                labelExpr="pow(10, datum.value) < 10 ? format(pow(10, datum.value), '.0f') : format(pow(10, datum.value), ',.0f')",
            ),
        ),
        tooltip=[
            alt.Tooltip("Amplitude (MPa):O", title="Amplitude"),
            alt.Tooltip("Mean Stress (MPa):O", title="Mean Stress"),
            alt.Tooltip("Cycle Count:Q", title="Cycles", format=","),
        ],
    )
)

# Style and layout
chart = (
    heatmap.properties(
        width=780,
        height=780,
        title=alt.Title(
            "heatmap-rainflow · altair · pyplots.ai",
            subtitle="Rainflow cycle counting matrix — variable-amplitude fatigue loading on steel component",
            fontSize=26,
            subtitleFontSize=16,
            subtitleColor="#666666",
            anchor="start",
            offset=16,
        ),
        padding={"left": 20, "right": 20, "top": 20, "bottom": 20},
    )
    .configure_view(strokeWidth=0, fill="#ffffff")
    .configure_axis(grid=False, domain=False, ticks=False)
)

# Save
chart.save("plot.png", scale_factor=3.6)
chart.save("plot.html")

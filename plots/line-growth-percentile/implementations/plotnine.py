"""pyplots.ai
line-growth-percentile: Pediatric Growth Chart with Percentile Curves
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-19
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_line,
    geom_point,
    geom_ribbon,
    geom_text,
    ggplot,
    labs,
    scale_alpha_manual,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - WHO-style weight-for-age reference for boys, 0-36 months
np.random.seed(42)

age_months = np.arange(0, 37, 1)

# Realistic weight-for-age percentile curves (kg) for boys 0-36 months
# Based on approximate WHO growth standards
median_weight = 3.3 + 0.7 * age_months - 0.008 * age_months**2 + 0.00005 * age_months**3
sd_weight = 0.4 + 0.02 * age_months

percentiles = {
    "P3": median_weight - 1.881 * sd_weight,
    "P10": median_weight - 1.282 * sd_weight,
    "P25": median_weight - 0.674 * sd_weight,
    "P50": median_weight,
    "P75": median_weight + 0.674 * sd_weight,
    "P90": median_weight + 1.282 * sd_weight,
    "P97": median_weight + 1.881 * sd_weight,
}

# Build reference dataframe in wide format
df_ref = pd.DataFrame({"age": age_months, **{k.lower(): v for k, v in percentiles.items()}})

# Long-format band data with fill and alpha mapped via aesthetics
band_specs = [
    ("P3–P10", "p3", "p10", "#1a4e7a", 0.35),
    ("P10–P25", "p10", "p25", "#3a7ebf", 0.30),
    ("P25–P75", "p25", "p75", "#7eb8e0", 0.25),
    ("P75–P90", "p75", "p90", "#3a7ebf", 0.30),
    ("P90–P97", "p90", "p97", "#1a4e7a", 0.35),
]

df_bands = pd.concat(
    [
        pd.DataFrame({"age": df_ref["age"], "ymin": df_ref[lo], "ymax": df_ref[hi], "band": label})
        for label, lo, hi, _, _ in band_specs
    ],
    ignore_index=True,
)
band_order = [s[0] for s in band_specs]
df_bands["band"] = pd.Categorical(df_bands["band"], categories=band_order, ordered=True)

band_fill_map = {s[0]: s[3] for s in band_specs}
band_alpha_map = {s[0]: s[4] for s in band_specs}

# Long-format line data with color mapped via aesthetic
line_specs = [
    ("P3", "p3", "#1a4e7a"),
    ("P10", "p10", "#2a6699"),
    ("P25", "p25", "#4a8ec2"),
    ("P50", "p50", "#0d3b66"),
    ("P75", "p75", "#4a8ec2"),
    ("P90", "p90", "#2a6699"),
    ("P97", "p97", "#1a4e7a"),
]

df_lines = pd.concat(
    [pd.DataFrame({"age": df_ref["age"], "weight": df_ref[col], "percentile": label}) for label, col, _ in line_specs],
    ignore_index=True,
)
pct_order = [s[0] for s in line_specs]
df_lines["percentile"] = pd.Categorical(df_lines["percentile"], categories=pct_order, ordered=True)

line_color_map = {s[0]: s[2] for s in line_specs}

# Individual patient data - a healthy boy tracking around the 60th-75th percentile
patient_ages = np.array([0, 1, 2, 4, 6, 9, 12, 15, 18, 24, 30, 36])
patient_weights = np.array([3.5, 4.6, 5.8, 7.2, 8.3, 9.5, 10.4, 11.2, 11.9, 13.1, 14.5, 15.6])
df_patient = pd.DataFrame({"age": patient_ages, "weight": patient_weights})

# Percentile labels at right margin (age=36)
df_labels = pd.DataFrame({"age": [36] * 7, "weight": [percentiles[p][-1] for p in pct_order], "label": pct_order})

# Separate median vs boundary lines for distinct sizing
df_median = df_lines[df_lines["percentile"] == "P50"]
df_boundary = df_lines[df_lines["percentile"] != "P50"]

# Plot using grammar of graphics: aesthetic mappings + scale_*_manual
plot = (
    ggplot()
    # Percentile bands via fill + alpha aesthetic mappings
    + geom_ribbon(df_bands, aes(x="age", ymin="ymin", ymax="ymax", fill="band", alpha="band"))
    + scale_fill_manual(values=band_fill_map)
    + scale_alpha_manual(values=band_alpha_map)
    # Boundary percentile lines via color aesthetic mapping
    + geom_line(df_boundary, aes(x="age", y="weight", color="percentile"), size=0.5, alpha=0.6)
    # Median line emphasized separately
    + geom_line(df_median, aes(x="age", y="weight"), color="#0d3b66", size=1.8)
    + scale_color_manual(values=line_color_map)
    # Percentile labels at right margin
    + geom_text(df_labels, aes(x="age", y="weight", label="label"), ha="left", size=11, color="#1a4e7a", nudge_x=0.5)
    # Patient trajectory
    + geom_line(df_patient, aes(x="age", y="weight"), color="#E63946", size=1.5)
    + geom_point(df_patient, aes(x="age", y="weight"), color="#E63946", fill="white", size=4, stroke=1.2)
    # Labels and scales
    + labs(x="Age (months)", y="Weight (kg)", title="line-growth-percentile · plotnine · pyplots.ai")
    + scale_x_continuous(breaks=range(0, 37, 3), limits=(0, 38))
    + scale_y_continuous(breaks=range(2, 20, 2))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(alpha=0.2, size=0.8),
        legend_position="none",
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)

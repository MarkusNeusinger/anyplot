""" pyplots.ai
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

percentile_3 = median_weight - 1.881 * sd_weight
percentile_10 = median_weight - 1.282 * sd_weight
percentile_25 = median_weight - 0.674 * sd_weight
percentile_50 = median_weight
percentile_75 = median_weight + 0.674 * sd_weight
percentile_90 = median_weight + 1.282 * sd_weight
percentile_97 = median_weight + 1.881 * sd_weight

# Build reference dataframe
df_ref = pd.DataFrame(
    {
        "age": age_months,
        "p3": percentile_3,
        "p10": percentile_10,
        "p25": percentile_25,
        "p50": percentile_50,
        "p75": percentile_75,
        "p90": percentile_90,
        "p97": percentile_97,
    }
)

# Individual patient data - a healthy boy tracking around the 60th-75th percentile
patient_ages = np.array([0, 1, 2, 4, 6, 9, 12, 15, 18, 24, 30, 36])
patient_weights = np.array([3.5, 4.6, 5.8, 7.2, 8.3, 9.5, 10.4, 11.2, 11.9, 13.1, 14.5, 15.6])

df_patient = pd.DataFrame({"age": patient_ages, "weight": patient_weights})

# Blue-toned palette for boys (darker at extremes, lighter near median)
band_colors = {
    "P3–P10": "#1a4e7a",
    "P10–P25": "#3a7ebf",
    "P25–P75": "#7eb8e0",
    "P75–P90": "#3a7ebf",
    "P90–P97": "#1a4e7a",
}

band_alphas = {"P3–P10": 0.35, "P10–P25": 0.30, "P25–P75": 0.25, "P75–P90": 0.30, "P90–P97": 0.35}

# Create ribbon data for percentile bands
bands = []
for label, ymin_col, ymax_col in [
    ("P3–P10", "p3", "p10"),
    ("P10–P25", "p10", "p25"),
    ("P25–P75", "p25", "p75"),
    ("P75–P90", "p75", "p90"),
    ("P90–P97", "p90", "p97"),
]:
    band_df = pd.DataFrame({"age": df_ref["age"], "ymin": df_ref[ymin_col], "ymax": df_ref[ymax_col], "band": label})
    bands.append(band_df)

df_bands = pd.concat(bands, ignore_index=True)
df_bands["band"] = pd.Categorical(
    df_bands["band"], categories=["P3–P10", "P10–P25", "P25–P75", "P75–P90", "P90–P97"], ordered=True
)

# Percentile label positions at age=36 (right margin)
label_age = 36
df_labels = pd.DataFrame(
    {
        "age": [label_age] * 7,
        "weight": [
            df_ref["p3"].iloc[-1],
            df_ref["p10"].iloc[-1],
            df_ref["p25"].iloc[-1],
            df_ref["p50"].iloc[-1],
            df_ref["p75"].iloc[-1],
            df_ref["p90"].iloc[-1],
            df_ref["p97"].iloc[-1],
        ],
        "label": ["P3", "P10", "P25", "P50", "P75", "P90", "P97"],
    }
)

# Plot
plot = (
    ggplot()
    # Percentile bands
    + geom_ribbon(
        df_bands[df_bands["band"] == "P3–P10"], aes(x="age", ymin="ymin", ymax="ymax"), fill="#1a4e7a", alpha=0.35
    )
    + geom_ribbon(
        df_bands[df_bands["band"] == "P10–P25"], aes(x="age", ymin="ymin", ymax="ymax"), fill="#3a7ebf", alpha=0.30
    )
    + geom_ribbon(
        df_bands[df_bands["band"] == "P25–P75"], aes(x="age", ymin="ymin", ymax="ymax"), fill="#7eb8e0", alpha=0.25
    )
    + geom_ribbon(
        df_bands[df_bands["band"] == "P75–P90"], aes(x="age", ymin="ymin", ymax="ymax"), fill="#3a7ebf", alpha=0.30
    )
    + geom_ribbon(
        df_bands[df_bands["band"] == "P90–P97"], aes(x="age", ymin="ymin", ymax="ymax"), fill="#1a4e7a", alpha=0.35
    )
    # Percentile boundary lines
    + geom_line(df_ref, aes(x="age", y="p3"), color="#1a4e7a", size=0.5, alpha=0.6)
    + geom_line(df_ref, aes(x="age", y="p10"), color="#2a6699", size=0.5, alpha=0.6)
    + geom_line(df_ref, aes(x="age", y="p25"), color="#4a8ec2", size=0.5, alpha=0.6)
    + geom_line(df_ref, aes(x="age", y="p50"), color="#0d3b66", size=1.8)
    + geom_line(df_ref, aes(x="age", y="p75"), color="#4a8ec2", size=0.5, alpha=0.6)
    + geom_line(df_ref, aes(x="age", y="p90"), color="#2a6699", size=0.5, alpha=0.6)
    + geom_line(df_ref, aes(x="age", y="p97"), color="#1a4e7a", size=0.5, alpha=0.6)
    # Percentile labels at right margin
    + geom_text(df_labels, aes(x="age", y="weight", label="label"), ha="left", size=11, color="#1a4e7a", nudge_x=0.5)
    # Patient data
    + geom_line(df_patient, aes(x="age", y="weight"), color="#E63946", size=1.5)
    + geom_point(df_patient, aes(x="age", y="weight"), color="#E63946", fill="white", size=4, stroke=1.2)
    # Labels
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

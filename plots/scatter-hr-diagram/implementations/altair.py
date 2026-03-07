""" pyplots.ai
scatter-hr-diagram: Hertzsprung-Russell Diagram
Library: altair 6.0.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-07
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)

# Main sequence stars (diagonal band from hot/bright to cool/dim)
n_main = 250
main_temp = 10 ** np.random.uniform(np.log10(2500), np.log10(35000), n_main)
main_log_lum = (np.log10(main_temp) - np.log10(5778)) * 5.5 + np.random.normal(0, 0.3, n_main)
main_lum = 10**main_log_lum

# Red giants (cool but bright)
n_giants = 50
giant_temp = 10 ** np.random.uniform(np.log10(3200), np.log10(5500), n_giants)
giant_lum = 10 ** np.random.uniform(1.2, 3.0, n_giants)

# Supergiants (very bright, various temps)
n_super = 20
super_temp = 10 ** np.random.uniform(np.log10(3500), np.log10(30000), n_super)
super_lum = 10 ** np.random.uniform(3.5, 5.5, n_super)

# White dwarfs (hot but dim)
n_wd = 40
wd_temp = 10 ** np.random.uniform(np.log10(5000), np.log10(30000), n_wd)
wd_lum = 10 ** np.random.uniform(-4, -1.5, n_wd)

temperatures = np.concatenate([main_temp, giant_temp, super_temp, wd_temp])
luminosities = np.concatenate([main_lum, giant_lum, super_lum, wd_lum])
regions = ["Main Sequence"] * n_main + ["Red Giants"] * n_giants + ["Supergiants"] * n_super + ["White Dwarfs"] * n_wd

# Assign spectral type by temperature using np.select
spectral_types = np.select(
    [
        temperatures >= 30000,
        temperatures >= 10000,
        temperatures >= 7500,
        temperatures >= 6000,
        temperatures >= 5200,
        temperatures >= 3700,
    ],
    ["O", "B", "A", "F", "G", "K"],
    default="M",
)

df = pd.DataFrame(
    {
        "Temperature (K)": temperatures,
        "Luminosity (Solar)": luminosities,
        "Region": regions,
        "Spectral Type": spectral_types,
    }
)

# Sun as a reference point
sun = pd.DataFrame({"Temperature (K)": [5778], "Luminosity (Solar)": [1.0], "label": ["Sun ☉"]})

# Region label positions (placed in clear areas away from dense data)
region_labels = pd.DataFrame(
    {
        "Temperature (K)": [8000, 3200, 9000, 25000],
        "Luminosity (Solar)": [0.015, 800, 200000, 0.0008],
        "text": ["Main Sequence", "Red Giants", "Supergiants", "White Dwarfs"],
    }
)

# Interactive selection: click legend to highlight spectral type
selection = alt.selection_point(fields=["Spectral Type"], bind="legend")

# Plot
stars = (
    alt.Chart(df)
    .mark_circle(strokeWidth=0)
    .encode(
        x=alt.X(
            "Temperature (K):Q",
            scale=alt.Scale(type="log", domain=[50000, 2000]),
            axis=alt.Axis(
                title="Surface Temperature (K)",
                titleFontSize=22,
                titleColor="#333333",
                labelFontSize=16,
                labelColor="#555555",
                values=[2000, 3000, 5000, 7000, 10000, 20000, 40000],
                format="~s",
                gridOpacity=0.12,
                gridColor="#cccccc",
                domainColor="#aaaaaa",
            ),
        ),
        y=alt.Y(
            "Luminosity (Solar):Q",
            scale=alt.Scale(type="log", domain=[0.00005, 2000000]),
            axis=alt.Axis(
                title="Luminosity (L/L☉)",
                titleFontSize=22,
                titleColor="#333333",
                labelFontSize=16,
                labelColor="#555555",
                gridOpacity=0.12,
                gridColor="#cccccc",
                domainColor="#aaaaaa",
                format=".0e",
            ),
        ),
        color=alt.Color(
            "Spectral Type:N",
            scale=alt.Scale(
                domain=["O", "B", "A", "F", "G", "K", "M"],
                range=["#2244aa", "#6699ee", "#b0c4de", "#c8a82a", "#f0e040", "#ee8822", "#cc4411"],
            ),
            sort=["O", "B", "A", "F", "G", "K", "M"],
            legend=alt.Legend(
                title="Spectral Type", titleFontSize=18, labelFontSize=15, symbolSize=200, orient="right"
            ),
        ),
        size=alt.value(40),
        opacity=alt.condition(selection, alt.value(0.5), alt.value(0.08)),
        tooltip=["Temperature (K):Q", "Luminosity (Solar):Q", "Spectral Type:N", "Region:N"],
    )
    .add_params(selection)
)

# Sun marker
sun_point = (
    alt.Chart(sun)
    .mark_point(shape="cross", size=500, color="#FFD700", strokeWidth=3, filled=True)
    .encode(x="Temperature (K):Q", y="Luminosity (Solar):Q", tooltip=alt.value("Sun (G2V, 5778 K, 1.0 L☉)"))
)

sun_label = (
    alt.Chart(sun)
    .mark_text(fontSize=16, fontWeight="bold", color="#DAA520", dx=30, dy=-18)
    .encode(x="Temperature (K):Q", y="Luminosity (Solar):Q", text="label:N")
)

# Region labels
labels = (
    alt.Chart(region_labels)
    .mark_text(fontSize=15, fontStyle="italic", color="#888888", fontWeight="bold")
    .encode(x="Temperature (K):Q", y="Luminosity (Solar):Q", text="text:N")
)

chart = (
    (stars + sun_point + sun_label + labels)
    .properties(
        width=1600, height=900, title=alt.Title("scatter-hr-diagram · altair · pyplots.ai", fontSize=28, anchor="start")
    )
    .configure_view(strokeWidth=0)
    .configure_axis(tickSize=0)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")

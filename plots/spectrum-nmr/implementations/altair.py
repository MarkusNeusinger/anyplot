""" pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: altair 6.0.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-09
"""

import altair as alt
import numpy as np
import pandas as pd


# Data - Synthetic 1H NMR spectrum of ethanol (CH3-CH2-OH)
np.random.seed(42)
chemical_shift = np.linspace(-0.5, 12.0, 6000)
w = 0.012  # default Lorentzian half-width

# Build intensity from Lorentzian peaks: A / (1 + ((x - c) / w)^2)
intensity = np.zeros_like(chemical_shift)

# TMS reference peak at 0 ppm (singlet)
intensity += 0.3 / (1 + ((chemical_shift - 0.0) / 0.015) ** 2)

# CH3 triplet near 1.18 ppm (3 peaks, 1:2:1 ratio, J ~ 0.07 ppm)
j_ch3 = 0.07
intensity += 0.50 / (1 + ((chemical_shift - (1.18 - j_ch3)) / w) ** 2)
intensity += 1.00 / (1 + ((chemical_shift - 1.18) / w) ** 2)
intensity += 0.50 / (1 + ((chemical_shift - (1.18 + j_ch3)) / w) ** 2)

# OH singlet near 2.61 ppm
intensity += 0.35 / (1 + ((chemical_shift - 2.61) / 0.02) ** 2)

# CH2 quartet near 3.69 ppm (4 peaks, 1:3:3:1 ratio, J ~ 0.07 ppm)
j_ch2 = 0.07
intensity += 0.25 / (1 + ((chemical_shift - (3.69 - 1.5 * j_ch2)) / w) ** 2)
intensity += 0.75 / (1 + ((chemical_shift - (3.69 - 0.5 * j_ch2)) / w) ** 2)
intensity += 0.75 / (1 + ((chemical_shift - (3.69 + 0.5 * j_ch2)) / w) ** 2)
intensity += 0.25 / (1 + ((chemical_shift - (3.69 + 1.5 * j_ch2)) / w) ** 2)

# Add minimal baseline noise
intensity += np.random.normal(0, 0.003, len(chemical_shift))
intensity = np.clip(intensity, 0, None)

df = pd.DataFrame({"Chemical Shift (ppm)": chemical_shift, "Intensity": intensity})

# Peak labels
labels_df = pd.DataFrame(
    {
        "Chemical Shift (ppm)": [0.0, 1.18, 2.61, 3.69],
        "Intensity": [0.33, 1.05, 0.39, 0.80],
        "label": ["TMS\n0.00", "CH\u2083 (triplet)\n1.18", "OH (singlet)\n2.61", "CH\u2082 (quartet)\n3.69"],
    }
)

# Reversed x-axis scale (NMR convention: high ppm on left)
x_scale = alt.Scale(domain=[12.0, -0.5])
y_scale = alt.Scale(domain=[0, 1.25])

# Spectrum line
spectrum = (
    alt.Chart(df)
    .mark_line(color="#306998", strokeWidth=1.8)
    .encode(
        x=alt.X("Chemical Shift (ppm):Q", scale=x_scale, title="Chemical Shift (ppm)"),
        y=alt.Y("Intensity:Q", title="Intensity (a.u.)", scale=y_scale),
        tooltip=[alt.Tooltip("Chemical Shift (ppm):Q", format=".2f"), alt.Tooltip("Intensity:Q", format=".3f")],
    )
)

# Peak annotation labels
peak_labels = (
    alt.Chart(labels_df)
    .mark_text(fontSize=16, fontWeight="bold", color="#306998", lineBreak="\n", align="center", dy=-18)
    .encode(x=alt.X("Chemical Shift (ppm):Q", scale=x_scale), y=alt.Y("Intensity:Q", scale=y_scale), text="label:N")
)

# Combine layers
chart = (
    alt.layer(spectrum, peak_labels)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "Ethanol \u00b9H NMR \u00b7 spectrum-nmr \u00b7 altair \u00b7 pyplots.ai", fontSize=28, anchor="middle"
        ),
    )
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        titleColor="#333333",
        labelColor="#555555",
        grid=False,
        domainColor="#aaaaaa",
        domainWidth=0.6,
        tickColor="#aaaaaa",
        tickSize=5,
        tickWidth=0.6,
    )
    .configure_title(font="Helvetica Neue, Arial, sans-serif", color="#222222")
    .configure_view(strokeWidth=0)
    .interactive()
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")

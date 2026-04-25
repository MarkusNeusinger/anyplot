"""anyplot.ai
area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
Library: altair 6.1.0 | Python 3.14.3
Quality: pending | Created: 2026-04-25
"""

import importlib
import os
import sys


# Drop script directory from sys.path so the `altair` package resolves, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")
np = importlib.import_module("numpy")
pd = importlib.import_module("pandas")


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Okabe-Ito position 1 — silhouette fill

# Data — Wallis (Valais, CH) panorama: 16 4000-m summits along a 180° sweep
peaks = pd.DataFrame(
    [
        ("Weisshorn", 4506, 9),
        ("Zinalrothorn", 4221, 20),
        ("Ober Gabelhorn", 4063, 30),
        ("Dent Blanche", 4358, 42),
        ("Matterhorn", 4478, 56),
        ("Breithorn", 4164, 73),
        ("Pollux", 4092, 81),
        ("Castor", 4223, 88),
        ("Liskamm", 4527, 97),
        ("Monte Rosa", 4634, 109),
        ("Strahlhorn", 4190, 122),
        ("Rimpfischhorn", 4199, 132),
        ("Allalinhorn", 4027, 140),
        ("Alphubel", 4206, 148),
        ("Täschhorn", 4491, 158),
        ("Dom", 4545, 168),
    ],
    columns=["name", "elevation_m", "angle_deg"],
)

# Skyline ridge — max of named-peak gaussians plus naturalistic minor ridge texture
np.random.seed(42)
angles = np.linspace(-2, 182, 1500)
ridge_elev = 2950 + 110 * np.sin(angles * 0.11) + 35 * np.sin(angles * 0.43 + 1.1)

# Minor sub-peaks for naturalistic ridge between named summits
for _ in range(55):
    pos = np.random.uniform(-2, 182)
    height = np.random.uniform(150, 480)
    width = np.random.uniform(1.4, 3.0)
    ridge_elev = np.maximum(ridge_elev, 2950 + height * np.exp(-((angles - pos) ** 2) / (2 * width**2)))

# Named-peak gaussians (sharper summits)
for _, row in peaks.iterrows():
    height = row["elevation_m"] - 2950
    width = 2.0 + (row["elevation_m"] - 4000) * 0.0007
    ridge_elev = np.maximum(ridge_elev, 2950 + height * np.exp(-((angles - row["angle_deg"]) ** 2) / (2 * width**2)))

ridge = pd.DataFrame({"angle_deg": angles, "elevation_m": ridge_elev})

# Stagger label heights so adjacent peaks don't collide
peaks = peaks.sort_values("angle_deg").reset_index(drop=True)
LABEL_HIGH = 5950
LABEL_LOW = 5550
peaks["label_y"] = [LABEL_HIGH if i % 2 == 0 else LABEL_LOW for i in range(len(peaks))]
# Push the Matterhorn label apart from its neighbours since it's the focal summit
peaks.loc[peaks["name"] == "Matterhorn", "label_y"] = LABEL_HIGH + 100
peaks["elev_label"] = peaks["elevation_m"].apply(lambda v: f"{v:.0f} m")

# Plot — silhouette area
silhouette = (
    alt.Chart(ridge)
    .mark_area(color=BRAND, line={"color": BRAND, "strokeWidth": 1.5}, opacity=1.0)
    .encode(
        x=alt.X("angle_deg:Q", scale=alt.Scale(domain=[0, 180]), axis=None),
        y=alt.Y(
            "elevation_m:Q",
            title="Elevation (m)",
            scale=alt.Scale(domain=[2900, 6300]),
            axis=alt.Axis(values=[3000, 3500, 4000, 4500, 5000]),
        ),
    )
)

# Leader lines from summit up to the label position
leaders = (
    alt.Chart(peaks)
    .mark_rule(strokeWidth=1.0, opacity=0.55, color=INK_SOFT)
    .encode(x="angle_deg:Q", y="elevation_m:Q", y2="label_y:Q")
)

# Two-line labels: name on top, elevation below — both positioned above label_y
name_labels = (
    alt.Chart(peaks)
    .mark_text(align="center", baseline="bottom", fontSize=15, fontWeight="bold", color=INK, dy=-22)
    .encode(x="angle_deg:Q", y="label_y:Q", text="name:N")
)
elev_labels = (
    alt.Chart(peaks)
    .mark_text(align="center", baseline="bottom", fontSize=13, color=INK_SOFT, dy=-6)
    .encode(x="angle_deg:Q", y="label_y:Q", text="elev_label:N")
)

chart = (
    (silhouette + leaders + name_labels + elev_labels)
    .properties(
        width=1600,
        height=900,
        title=alt.Title(
            "Wallis Panorama · area-mountain-panorama · altair · anyplot.ai",
            subtitle="Sixteen 4000-m summits along a 180° horizontal sweep, Valais Alps",
            subtitleColor=INK_SOFT,
            subtitleFontSize=18,
            fontSize=28,
            anchor="start",
            offset=18,
            color=INK,
        ),
        background=PAGE_BG,
    )
    .configure_view(fill=PAGE_BG, stroke=None)
    .configure_axis(
        domainColor=INK_SOFT,
        tickColor=INK_SOFT,
        gridColor=INK,
        gridOpacity=0.0,
        labelColor=INK_SOFT,
        titleColor=INK,
        labelFontSize=18,
        titleFontSize=22,
        tickSize=8,
    )
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")

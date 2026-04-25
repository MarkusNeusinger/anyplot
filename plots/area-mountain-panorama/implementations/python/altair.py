""" anyplot.ai
area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
Library: altair 6.1.0 | Python 3.14.4
Quality: 93/100 | Created: 2026-04-25
"""

import importlib
import os
import sys


# Drop script directory from sys.path so the `altair` package resolves, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")
np = importlib.import_module("numpy")
pd = importlib.import_module("pandas")


# Theme tokens (chrome flips with theme; data colors stay constant)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
BRAND = "#009E73"  # Okabe-Ito position 1 — silhouette fill (single data series)

# Theme-adaptive dusk sky gradient (chrome layer above the ridgeline; spec-authorized)
SKY_HORIZON = "#FFC58A" if THEME == "light" else "#5A3422"  # warm dusk glow at ridgeline
SKY_MID = "#D89AA8" if THEME == "light" else "#2E1F35"  # twilight rose / deep plum
SKY_ZENITH = "#5C5078" if THEME == "light" else "#0C0E1A"  # evening blue / night sky

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

# Skyline ridge — gaussians around named peaks plus naturalistic minor ridge texture
np.random.seed(42)
angles = np.linspace(-2, 182, 1500)
ridge_elev = 2950 + 110 * np.sin(angles * 0.11) + 35 * np.sin(angles * 0.43 + 1.1)

for _ in range(55):
    pos = np.random.uniform(-2, 182)
    height = np.random.uniform(150, 480)
    width = np.random.uniform(1.4, 3.0)
    ridge_elev = np.maximum(ridge_elev, 2950 + height * np.exp(-((angles - pos) ** 2) / (2 * width**2)))

for _, row in peaks.iterrows():
    height = row["elevation_m"] - 2950
    width = 2.0 + (row["elevation_m"] - 4000) * 0.0007
    ridge_elev = np.maximum(ridge_elev, 2950 + height * np.exp(-((angles - row["angle_deg"]) ** 2) / (2 * width**2)))

ridge = pd.DataFrame({"angle_deg": angles, "elevation_m": ridge_elev})

# Stagger label heights so adjacent peaks don't collide; Matterhorn lifted as focal summit
peaks = peaks.sort_values("angle_deg").reset_index(drop=True)
LABEL_HIGH = 5800
LABEL_LOW = 5400
peaks["label_y"] = [LABEL_HIGH if i % 2 == 0 else LABEL_LOW for i in range(len(peaks))]
peaks.loc[peaks["name"] == "Matterhorn", "label_y"] = 6000
peaks["elev_label"] = peaks["elevation_m"].apply(lambda v: f"{v:.0f} m")

matterhorn = peaks[peaks["name"] == "Matterhorn"]
others = peaks[peaks["name"] != "Matterhorn"]

# Shared scales / axis so all layers register on the same coordinate system
X_SCALE = alt.Scale(domain=[0, 180])
Y_SCALE = alt.Scale(domain=[2900, 6300])
Y_AXIS = alt.Axis(values=[3000, 3500, 4000, 4500, 5000])

# Sky — dusk vertical gradient covering the full plot area; silhouette will mask the lower half
sky_df = pd.DataFrame({"x_min": [0], "x_max": [180], "y_min": [2900], "y_max": [6300]})
sky = (
    alt.Chart(sky_df)
    .mark_rect(
        color={
            "x1": 0,
            "y1": 0,
            "x2": 0,
            "y2": 1,
            "gradient": "linear",
            "stops": [
                {"offset": 0.0, "color": SKY_ZENITH},
                {"offset": 0.55, "color": SKY_MID},
                {"offset": 1.0, "color": SKY_HORIZON},
            ],
        }
    )
    .encode(
        x=alt.X("x_min:Q", scale=X_SCALE, axis=None),
        x2="x_max:Q",
        y=alt.Y("y_min:Q", scale=Y_SCALE, title="Elevation (m)", axis=Y_AXIS),
        y2="y_max:Q",
    )
)

# Silhouette — brand-green photo-like fill; ridge stroke gives the snow-edge alpenglow line
silhouette = (
    alt.Chart(ridge)
    .mark_area(color=BRAND, line={"color": BRAND, "strokeWidth": 2.5}, opacity=1.0)
    .encode(x="angle_deg:Q", y="elevation_m:Q")
)

# Leader lines from summit up to label position (with tooltip for HTML hover)
leaders = (
    alt.Chart(others)
    .mark_rule(strokeWidth=1.0, opacity=0.55, color=INK_SOFT)
    .encode(
        x="angle_deg:Q",
        y="elevation_m:Q",
        y2="label_y:Q",
        tooltip=[alt.Tooltip("name:N", title="Peak"), alt.Tooltip("elevation_m:Q", title="Elevation (m)", format=",d")],
    )
)
matterhorn_leader = (
    alt.Chart(matterhorn)
    .mark_rule(strokeWidth=2.0, opacity=0.9, color=INK)
    .encode(
        x="angle_deg:Q",
        y="elevation_m:Q",
        y2="label_y:Q",
        tooltip=[alt.Tooltip("name:N", title="Peak"), alt.Tooltip("elevation_m:Q", title="Elevation (m)", format=",d")],
    )
)

# Two-line peak labels at recommended sizes (name 18, elevation 15 — meets tick-floor)
name_labels = (
    alt.Chart(others)
    .mark_text(align="center", baseline="bottom", fontSize=18, fontWeight="bold", color=INK, dy=-26)
    .encode(
        x="angle_deg:Q",
        y="label_y:Q",
        text="name:N",
        tooltip=[alt.Tooltip("name:N", title="Peak"), alt.Tooltip("elevation_m:Q", title="Elevation (m)", format=",d")],
    )
)
elev_labels = (
    alt.Chart(others)
    .mark_text(align="center", baseline="bottom", fontSize=15, color=INK_SOFT, dy=-8)
    .encode(
        x="angle_deg:Q",
        y="label_y:Q",
        text="elev_label:N",
        tooltip=[alt.Tooltip("name:N", title="Peak"), alt.Tooltip("elevation_m:Q", title="Elevation (m)", format=",d")],
    )
)

# Matterhorn focal accent: notably larger label so the anchor summit reads as the composition's focus
matterhorn_name = (
    alt.Chart(matterhorn)
    .mark_text(align="center", baseline="bottom", fontSize=26, fontWeight="bold", color=INK, dy=-30)
    .encode(
        x="angle_deg:Q",
        y="label_y:Q",
        text="name:N",
        tooltip=[alt.Tooltip("name:N", title="Peak"), alt.Tooltip("elevation_m:Q", title="Elevation (m)", format=",d")],
    )
)
matterhorn_elev = (
    alt.Chart(matterhorn)
    .mark_text(align="center", baseline="bottom", fontSize=18, fontWeight="bold", color=INK_SOFT, dy=-8)
    .encode(
        x="angle_deg:Q",
        y="label_y:Q",
        text="elev_label:N",
        tooltip=[alt.Tooltip("name:N", title="Peak"), alt.Tooltip("elevation_m:Q", title="Elevation (m)", format=",d")],
    )
)

chart = (
    (sky + silhouette + leaders + matterhorn_leader + name_labels + elev_labels + matterhorn_name + matterhorn_elev)
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

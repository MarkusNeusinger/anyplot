"""anyplot.ai
area-mountain-panorama: Mountain Panorama Profile with Labeled Peaks
Library: altair 6.1.0 | Python 3.14.4
Quality: pending | Created: 2026-06-30
"""

import importlib
import os
import sys


# Drop script directory from sys.path so `altair` resolves the package, not this file
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
alt = importlib.import_module("altair")
np = importlib.import_module("numpy")
pd = importlib.import_module("pandas")
from PIL import Image


# Theme tokens — chrome flips with theme; Imprint palette data colors stay constant
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — silhouette fill (single data series)

# Theme-adaptive dusk sky gradient (spec-authorized chrome above the ridgeline)
SKY_HORIZON = "#FFC58A" if THEME == "light" else "#5A3422"
SKY_MID = "#D89AA8" if THEME == "light" else "#2E1F35"
SKY_ZENITH = "#5C5078" if THEME == "light" else "#0C0E1A"
# Alpenglow rim — warm gold / rose-copper at the sky-to-silhouette boundary
ALPENGLOW = "#FFBA6A" if THEME == "light" else "#C88060"

# Data — 6 major Wallis (Valais, CH) summits across a 180° horizontal sweep.
# Ober Gabelhorn (30°) and Liskamm (97°) omitted: their 12° gaps to adjacent
# peaks (Dent Blanche 42°, Monte Rosa 109°) prevent clean two-tier label stagger.
peaks = pd.DataFrame(
    [
        ("Weisshorn", 4506, 9),
        ("Dent Blanche", 4358, 42),
        ("Matterhorn", 4478, 56),
        ("Monte Rosa", 4634, 109),
        ("Alphubel", 4206, 148),
        ("Dom", 4545, 168),
    ],
    columns=["name", "elevation_m", "angle_deg"],
)

# Ridgeline — gaussian superposition: named summits + naturalistic minor relief
np.random.seed(42)
angles = np.linspace(-2, 182, 1500)
ridge_elev = 2950 + 110 * np.sin(angles * 0.11) + 35 * np.sin(angles * 0.43 + 1.1)

for _ in range(55):
    pos = np.random.uniform(-2, 182)
    height = np.random.uniform(150, 480)
    width = np.random.uniform(1.4, 3.0)
    ridge_elev = np.maximum(ridge_elev, 2950 + height * np.exp(-((angles - pos) ** 2) / (2 * width**2)))

for _, row in peaks.iterrows():
    h = row["elevation_m"] - 2950
    w = 2.0 + (row["elevation_m"] - 4000) * 0.0007
    ridge_elev = np.maximum(ridge_elev, 2950 + h * np.exp(-((angles - row["angle_deg"]) ** 2) / (2 * w**2)))

ridge = pd.DataFrame({"angle_deg": angles, "elevation_m": ridge_elev})

# Two-tier label stagger + Matterhorn focal accent.
# HIGH tier: Weisshorn/Monte Rosa/Dom — well-separated (≥59°).
# LOW tier: Dent Blanche/Alphubel — well-separated (106°).
# Dent Blanche uses right-align to avoid horizontal overlap with Matterhorn's
# center-aligned SPECIAL label (14° / 48px gap between their anchor points).
label_y_map = {
    "Weisshorn": 4950,  # HIGH
    "Dent Blanche": 4700,  # LOW  — right-aligned in text layers
    "Matterhorn": 5050,  # SPECIAL focal
    "Monte Rosa": 4950,  # HIGH
    "Alphubel": 4700,  # LOW
    "Dom": 4950,  # HIGH
}
peaks["label_y"] = peaks["name"].map(label_y_map)
peaks["elev_label"] = peaks["elevation_m"].apply(lambda v: f"{v} m")

matterhorn = peaks[peaks["name"] == "Matterhorn"]
dent_blanche = peaks[peaks["name"] == "Dent Blanche"]
others_center = peaks[(peaks["name"] != "Matterhorn") & (peaks["name"] != "Dent Blanche")]

# Coordinate system — only the sky layer carries the explicit scale + axis;
# other layers share it implicitly via Vega-Lite layer scale resolution.
# Adding alt.Scale to any secondary layer causes vl-convert to produce ~2× chart
# height overhead (confirmed via systematic debug tests), making the output exceed
# the 1800-source-px target even at height=190. Sky alone is the "anchor" layer.
X_SCALE = alt.Scale(domain=[0, 180])
Y_SCALE = alt.Scale(domain=[2900, 5800])
Y_AXIS = alt.Axis(values=[3000, 3500, 4000, 4500, 5000])

# Layer 1: dusk sky gradient (vertical linear, zenith → ridge horizon)
sky_df = pd.DataFrame({"x_min": [0], "x_max": [180], "y_min": [2900], "y_max": [5800]})
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

# Layer 2: mountain silhouette — brand-green filled area below the ridgeline
silhouette = alt.Chart(ridge).mark_area(color=BRAND, opacity=1.0).encode(x="angle_deg:Q", y="elevation_m:Q")

# Layer 3: alpenglow rim — warm glowing stroke at the sky-to-silhouette boundary
alpenglow = (
    alt.Chart(ridge)
    .mark_line(color=ALPENGLOW, strokeWidth=3.5, opacity=0.88)
    .encode(x="angle_deg:Q", y="elevation_m:Q")
)

_tooltip_others = [
    alt.Tooltip("name:N", title="Peak"),
    alt.Tooltip("elevation_m:Q", title="Elevation (m)", format=",d"),
]
_tooltip_mat = [alt.Tooltip("name:N", title="Peak"), alt.Tooltip("elevation_m:Q", title="Elevation (m)", format=",d")]

# Layers 4–5: leader lines from summit apex to label anchor
leaders = (
    alt.Chart(pd.concat([others_center, dent_blanche]))
    .mark_rule(strokeWidth=1.0, opacity=0.55, color=INK_SOFT)
    .encode(x="angle_deg:Q", y="elevation_m:Q", y2="label_y:Q", tooltip=_tooltip_others)
)
matterhorn_leader = (
    alt.Chart(matterhorn)
    .mark_rule(strokeWidth=2.5, opacity=0.9, color=INK)
    .encode(x="angle_deg:Q", y="elevation_m:Q", y2="label_y:Q", tooltip=_tooltip_mat)
)

# Layers 6–7: center-aligned name/elev labels for non-Matterhorn, non-Dent-Blanche peaks
name_labels = (
    alt.Chart(others_center)
    .mark_text(align="center", baseline="bottom", fontSize=12, fontWeight="bold", color=INK, dy=-28)
    .encode(x="angle_deg:Q", y="label_y:Q", text="name:N", tooltip=_tooltip_others)
)
elev_labels = (
    alt.Chart(others_center)
    .mark_text(align="center", baseline="bottom", fontSize=12, color=INK_SOFT, dy=-8)
    .encode(x="angle_deg:Q", y="label_y:Q", text="elev_label:N", tooltip=_tooltip_others)
)

# Layers 8–9: right-aligned name/elev labels for Dent Blanche.
# Right-align causes text to extend LEFT of x=42°, giving a 28px horizontal gap
# to Matterhorn's center-aligned labels at x=56° and avoiding visual collision.
db_name = (
    alt.Chart(dent_blanche)
    .mark_text(align="right", baseline="bottom", fontSize=12, fontWeight="bold", color=INK, dy=-28)
    .encode(x="angle_deg:Q", y="label_y:Q", text="name:N", tooltip=_tooltip_others)
)
db_elev = (
    alt.Chart(dent_blanche)
    .mark_text(align="right", baseline="bottom", fontSize=12, color=INK_SOFT, dy=-8)
    .encode(x="angle_deg:Q", y="label_y:Q", text="elev_label:N", tooltip=_tooltip_others)
)

# Layers 10–11: Matterhorn focal accent — larger font, heavier weight, composition anchor
matterhorn_name = (
    alt.Chart(matterhorn)
    .mark_text(align="center", baseline="bottom", fontSize=16, fontWeight="bold", color=INK, dy=-32)
    .encode(x="angle_deg:Q", y="label_y:Q", text="name:N", tooltip=_tooltip_mat)
)
matterhorn_elev = (
    alt.Chart(matterhorn)
    .mark_text(align="center", baseline="bottom", fontSize=12, fontWeight="bold", color=INK_SOFT, dy=-8)
    .encode(x="angle_deg:Q", y="label_y:Q", text="elev_label:N", tooltip=_tooltip_mat)
)

title_str = "Wallis Panorama · area-mountain-panorama · python · altair · anyplot.ai"
n = len(title_str)
ratio = 67 / n if n > 67 else 1.0
title_fs = max(11, round(16 * ratio))

# height=190: vl-convert with explicit Y_SCALE on the sky anchor layer adds ~47 CSS px
# of Y overhead per 190 CSS px (source height ≈ 1500px pre-pad, ≤1800px with title).
# DO NOT increase to ≥210 — overhead scales with height and tips over 1800 source px.
chart = (
    (
        sky
        + silhouette
        + alpenglow
        + leaders
        + matterhorn_leader
        + name_labels
        + elev_labels
        + db_name
        + db_elev
        + matterhorn_name
        + matterhorn_elev
    )
    .properties(
        width=620,
        height=190,
        title=alt.Title(
            title_str,
            subtitle="Six 4000-m summits along a 180° horizontal sweep, Valais Alps",
            subtitleColor=INK_SOFT,
            subtitleFontSize=13,
            fontSize=title_fs,
            anchor="start",
            offset=12,
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
        labelFontSize=10,
        titleFontSize=12,
        tickSize=5,
    )
)

chart.save(f"plot-{THEME}.png", scale_factor=4.0)
chart.save(f"plot-{THEME}.html")

# Pad-only to exact 3200×1800 target — altair.md Canvas rule (never crop)
TW, TH = 3200, 1800
_img = Image.open(f"plot-{THEME}.png").convert("RGB")
_w, _h = _img.size
if _w > TW or _h > TH:
    raise SystemExit(
        f"altair vl-convert produced {_w}×{_h}, exceeds target {TW}×{TH}. "
        f"Shrink chart .properties(width=, height=) values and re-render."
    )
if _w < TW or _h < TH:
    _canvas = Image.new("RGB", (TW, TH), PAGE_BG)
    _canvas.paste(_img, ((TW - _w) // 2, (TH - _h) // 2))
    _canvas.save(f"plot-{THEME}.png")

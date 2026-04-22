""" pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: altair 6.0.0 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-11
"""

import altair as alt
import numpy as np
import pandas as pd


np.random.seed(42)

# Material family data with realistic property ranges
families = {
    "Metals": {
        "density": (2700, 8900),
        "modulus": (45, 400),
        "materials": [
            "Aluminum",
            "Steel",
            "Titanium",
            "Copper",
            "Nickel",
            "Zinc",
            "Magnesium",
            "Brass",
            "Bronze",
            "Tungsten",
            "Cast Iron",
            "Stainless Steel",
            "Inconel",
            "Tin",
        ],
    },
    "Polymers": {
        "density": (900, 1500),
        "modulus": (0.2, 4.0),
        "materials": [
            "Polyethylene",
            "Polypropylene",
            "PVC",
            "Nylon",
            "Polycarbonate",
            "ABS",
            "PMMA",
            "PET",
            "Polystyrene",
            "PTFE",
            "Epoxy",
            "Polyurethane",
        ],
    },
    "Ceramics": {
        "density": (2200, 4500),
        "modulus": (200, 450),
        "materials": [
            "Alumina",
            "Silicon Carbide",
            "Zirconia",
            "Silicon Nitride",
            "Glass",
            "Porcelain",
            "Boron Carbide",
            "Tungsten Carbide",
            "Silica",
            "Magnesia",
        ],
    },
    "Composites": {
        "density": (1400, 2200),
        "modulus": (15, 200),
        "materials": [
            "CFRP",
            "GFRP",
            "Kevlar Composite",
            "Boron-Epoxy",
            "Wood-Polymer",
            "Metal Matrix",
            "Ceramic Matrix",
            "Carbon-Carbon",
            "Basalt Fiber",
        ],
    },
    "Elastomers": {
        "density": (900, 1300),
        "modulus": (0.001, 0.1),
        "materials": [
            "Natural Rubber",
            "Silicone",
            "Neoprene",
            "Butyl Rubber",
            "EPDM",
            "Nitrile Rubber",
            "Polyisoprene",
            "SBR",
        ],
    },
    "Foams": {
        "density": (20, 500),
        "modulus": (0.001, 1.0),
        "materials": [
            "Polyurethane Foam",
            "Polystyrene Foam",
            "PVC Foam",
            "Metal Foam",
            "Cork",
            "Ceramic Foam",
            "Phenolic Foam",
            "Melamine Foam",
        ],
    },
}

# Generate data points
rows = []
for family, props in families.items():
    d_lo, d_hi = props["density"]
    m_lo, m_hi = props["modulus"]
    for mat in props["materials"]:
        density = 10 ** np.random.uniform(np.log10(d_lo), np.log10(d_hi))
        modulus = 10 ** np.random.uniform(np.log10(m_lo), np.log10(m_hi))
        rows.append({"material": mat, "family": family, "density": round(density, 1), "modulus": round(modulus, 4)})

df = pd.DataFrame(rows)


def convex_hull(points):
    """Monotone chain convex hull algorithm."""
    sp = sorted(map(tuple, points))
    if len(sp) < 3:
        return list(sp)
    lo, up = [], []
    for p in sp:
        while len(lo) >= 2 and _cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(sp):
        while len(up) >= 2 and _cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


# Compute padded convex hull envelopes per family (in log space)
family_order = ["Metals", "Polymers", "Ceramics", "Composites", "Elastomers", "Foams"]
family_sizes = {f: len(families[f]["materials"]) for f in family_order}
max_size = max(family_sizes.values())

envelope_rows = []
for family, group in df.groupby("family"):
    log_x = np.log10(group["density"].values)
    log_y = np.log10(group["modulus"].values)
    cx, cy = log_x.mean(), log_y.mean()
    pts = np.column_stack([log_x, log_y])

    hull_pts = convex_hull(pts) if len(pts) >= 3 else list(map(tuple, pts))

    # Pad outward from centroid
    pad = 0.22
    padded = []
    for hx, hy in hull_pts:
        dx, dy = hx - cx, hy - cy
        dist = np.hypot(dx, dy) or 1e-6
        padded.append((hx + pad * dx / dist, hy + pad * dy / dist))

    # Sort by angle for proper polygon ordering, close the polygon
    angles = [np.arctan2(hy - cy, hx - cx) for hx, hy in padded]
    padded = [p for _, p in sorted(zip(angles, padded, strict=True))]
    padded.append(padded[0])

    # Scale opacity by family size for visual hierarchy
    fill_alpha = 0.10 + 0.10 * (family_sizes[family] / max_size)
    for i, (xi, yi) in enumerate(padded):
        envelope_rows.append(
            {"family": family, "density": 10**xi, "modulus": 10**yi, "pt_order": i, "fill_alpha": round(fill_alpha, 3)}
        )

df_envelope = pd.DataFrame(envelope_rows)

# Family label positions (geometric center in log space with nudge offsets)
label_nudge = {
    "Metals": (0.35, -0.3),
    "Polymers": (-0.15, 0.35),
    "Ceramics": (-0.35, 0.45),
    "Composites": (-0.3, -0.35),
    "Elastomers": (0.25, 0.3),
    "Foams": (-0.25, -0.2),
}
family_centers = []
for family, group in df.groupby("family"):
    log_cx = np.mean(np.log10(group["density"].values))
    log_cy = np.mean(np.log10(group["modulus"].values))
    dx, dy = label_nudge.get(family, (0, 0))
    family_centers.append(
        {"family": family, "density_center": 10 ** (log_cx + dx), "modulus_center": 10 ** (log_cy + dy)}
    )
df_labels = pd.DataFrame(family_centers)

# Color palette and scales
palette = ["#306998", "#E8833A", "#2A9D8F", "#E76F51", "#7B68AE", "#8AB17D"]
font_family = "Helvetica Neue, Helvetica, Arial, sans-serif"

x_scale = alt.Scale(type="log", domain=[10, 20000])
y_scale = alt.Scale(type="log", domain=[0.0005, 1000])
color_scale = alt.Scale(domain=family_order, range=palette)

# Interactive highlight selection
highlight = alt.selection_point(fields=["family"], on="pointerover", empty=False)

# Envelope regions with per-family opacity for visual depth
envelopes = (
    alt.Chart(df_envelope)
    .mark_line(filled=True, strokeWidth=1.5, interpolate="basis-closed")
    .encode(
        x=alt.X("density:Q", scale=x_scale),
        y=alt.Y("modulus:Q", scale=y_scale),
        color=alt.Color("family:N", scale=color_scale, legend=None),
        fill=alt.Fill("family:N", scale=color_scale, legend=None),
        fillOpacity="fill_alpha:Q",
        strokeOpacity=alt.value(0.45),
        order="pt_order:O",
        detail="family:N",
    )
)

# Scatter points with interactive highlight
points = (
    alt.Chart(df)
    .mark_circle(stroke="white", strokeWidth=0.8)
    .encode(
        x=alt.X("density:Q", scale=x_scale, title="Density (kg/m\u00b3)"),
        y=alt.Y("modulus:Q", scale=y_scale, title="Young\u2019s Modulus (GPa)"),
        color=alt.Color(
            "family:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Material Family",
                titleFontSize=18,
                titleFont=font_family,
                labelFontSize=16,
                labelFont=font_family,
                symbolSize=300,
                orient="right",
                symbolOpacity=0.85,
                titleColor="#333333",
                labelColor="#444444",
            ),
        ),
        size=alt.condition(highlight, alt.value(220), alt.value(150)),
        opacity=alt.condition(highlight, alt.value(0.95), alt.value(0.75)),
        tooltip=[
            alt.Tooltip("material:N", title="Material"),
            alt.Tooltip("family:N", title="Family"),
            alt.Tooltip("density:Q", title="Density (kg/m\u00b3)", format=",.0f"),
            alt.Tooltip("modulus:Q", title="Modulus (GPa)", format=".3f"),
        ],
    )
    .add_params(highlight)
)

# Family labels with white halo for readability
label_bg = (
    alt.Chart(df_labels)
    .mark_text(fontSize=16, fontWeight="bold", font=font_family, opacity=0.9)
    .encode(
        x=alt.X("density_center:Q", scale=x_scale),
        y=alt.Y("modulus_center:Q", scale=y_scale),
        text="family:N",
        color=alt.value("white"),
    )
)

labels = (
    alt.Chart(df_labels)
    .mark_text(fontSize=16, fontWeight="bold", font=font_family, opacity=0.9)
    .encode(
        x=alt.X("density_center:Q", scale=x_scale),
        y=alt.Y("modulus_center:Q", scale=y_scale),
        text="family:N",
        color=alt.Color("family:N", scale=color_scale, legend=None),
    )
)

# Performance index guide lines: E/rho = constant
guide_densities = np.logspace(np.log10(10), np.log10(20000), 50)
guide_lines_rows = []
for ratio, label in [(0.01, "E/\u03c1 = 0.01"), (0.1, "E/\u03c1 = 0.1")]:
    for d in guide_densities:
        m = ratio * d / 1000
        if 0.0005 <= m <= 1000:
            guide_lines_rows.append({"density": d, "modulus": m, "guide": label})
df_guides = pd.DataFrame(guide_lines_rows)

guides = (
    alt.Chart(df_guides)
    .mark_line(strokeDash=[6, 4], strokeWidth=1.3, opacity=0.35)
    .encode(
        x=alt.X("density:Q", scale=x_scale),
        y=alt.Y("modulus:Q", scale=y_scale),
        detail="guide:N",
        color=alt.value("#666666"),
    )
)

guide_label_data = []
for ratio, label in [(0.01, "E/\u03c1 = 0.01"), (0.1, "E/\u03c1 = 0.1")]:
    d_pos = 15000
    m_pos = ratio * d_pos / 1000
    if 0.0005 <= m_pos <= 1000:
        guide_label_data.append({"density": d_pos, "modulus": m_pos, "guide": label})
df_guide_labels = pd.DataFrame(guide_label_data)

guide_labels = (
    alt.Chart(df_guide_labels)
    .mark_text(fontSize=13, fontStyle="italic", font=font_family, opacity=0.5, angle=328, dy=-14)
    .encode(
        x=alt.X("density:Q", scale=x_scale),
        y=alt.Y("modulus:Q", scale=y_scale),
        text="guide:N",
        color=alt.value("#777777"),
    )
)

# Compose layered chart
chart = (
    alt.layer(envelopes, guides, guide_labels, points, label_bg, labels)
    .properties(
        width=1400,
        height=900,
        title=alt.Title(
            "scatter-ashby-material \u00b7 altair \u00b7 pyplots.ai",
            fontSize=28,
            fontWeight=500,
            font=font_family,
            color="#222222",
            subtitle="Young\u2019s Modulus vs Density across material families",
            subtitleFontSize=16,
            subtitleColor="#888888",
            subtitleFont=font_family,
        ),
        padding={"left": 80, "right": 200, "top": 50, "bottom": 60},
        background="#FAFBFC",
    )
    .resolve_scale(color="shared", fill="independent")
    .configure_axis(
        labelFontSize=18,
        titleFontSize=22,
        labelFont=font_family,
        titleFont=font_family,
        gridOpacity=0.12,
        grid=True,
        gridColor="#DDDDDD",
        domainColor="#BBBBBB",
        tickColor="#BBBBBB",
        labelColor="#555555",
        titleColor="#333333",
    )
    .configure_view(strokeWidth=0)
    .configure_legend(
        titleFontSize=18,
        labelFontSize=16,
        symbolSize=250,
        padding=15,
        offset=10,
        cornerRadius=4,
        fillColor="#FAFBFC",
        strokeColor="#EEEEEE",
    )
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")

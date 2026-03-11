"""pyplots.ai
scatter-ashby-material: Ashby Material Selection Chart
Library: altair 6.0.0 | Python 3.14.3
Quality: 76/100 | Created: 2026-03-11
"""

import altair as alt
import numpy as np
import pandas as pd


# Data
np.random.seed(42)

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
        "density": (2200, 6000),
        "modulus": (70, 450),
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

rows = []
for family, props in families.items():
    d_lo, d_hi = props["density"]
    m_lo, m_hi = props["modulus"]
    for mat in props["materials"]:
        log_d = np.random.uniform(np.log10(d_lo), np.log10(d_hi))
        log_m = np.random.uniform(np.log10(m_lo), np.log10(m_hi))
        density = 10**log_d
        modulus = 10**log_m
        rows.append({"material": mat, "family": family, "density": round(density, 1), "modulus": round(modulus, 4)})

df = pd.DataFrame(rows)

# Compute padded convex hull envelopes for each family (in log space)
envelope_rows = []
for family, group in df.groupby("family"):
    log_x = np.log10(group["density"].values)
    log_y = np.log10(group["modulus"].values)
    cx, cy = np.mean(log_x), np.mean(log_y)
    pts = np.column_stack([log_x, log_y])

    # Simple convex hull (Graham scan)
    def _cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    sorted_pts = sorted(map(tuple, pts))
    if len(sorted_pts) >= 3:
        lower = []
        for p in sorted_pts:
            while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)
        upper = []
        for p in reversed(sorted_pts):
            while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)
        hull = lower[:-1] + upper[:-1]
    else:
        hull = sorted_pts

    # Pad the hull outward from centroid
    pad = 0.25
    hull_padded = []
    for hx, hy in hull:
        dx, dy = hx - cx, hy - cy
        dist = np.sqrt(dx**2 + dy**2) or 1e-6
        hull_padded.append((hx + pad * dx / dist, hy + pad * dy / dist))

    # Smooth the hull by interpolating more points along the boundary
    hull_padded.append(hull_padded[0])  # close the polygon
    smooth_pts = []
    for j in range(len(hull_padded) - 1):
        x0, y0 = hull_padded[j]
        x1, y1 = hull_padded[j + 1]
        for t in np.linspace(0, 1, 8, endpoint=False):
            smooth_pts.append((x0 + t * (x1 - x0), y0 + t * (y1 - y0)))

    for i, (xi, yi) in enumerate(smooth_pts):
        envelope_rows.append({"family": family, "density": 10**xi, "modulus": 10**yi, "pt_order": i})

df_envelope = pd.DataFrame(envelope_rows)

# Family label positions (geometric center in log space, nudged to avoid overlap)
label_nudge = {
    "Metals": (0.2, -0.2),
    "Polymers": (-0.1, 0.3),
    "Ceramics": (-0.2, 0.3),
    "Composites": (-0.15, -0.35),
    "Elastomers": (0.15, 0.25),
    "Foams": (-0.2, -0.15),
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

# Colors
palette = ["#306998", "#E8833A", "#2A9D8F", "#E76F51", "#7B68AE", "#8AB17D"]
family_order = ["Metals", "Polymers", "Ceramics", "Composites", "Elastomers", "Foams"]

x_scale = alt.Scale(type="log", domain=[10, 20000])
y_scale = alt.Scale(type="log", domain=[0.0005, 1000])
color_scale = alt.Scale(domain=family_order, range=palette)

# Envelope regions (filled ellipses)
envelopes = (
    alt.Chart(df_envelope)
    .mark_line(filled=True, strokeWidth=1.5, interpolate="basis-closed")
    .encode(
        x=alt.X("density:Q", scale=x_scale),
        y=alt.Y("modulus:Q", scale=y_scale),
        color=alt.Color("family:N", scale=color_scale, legend=None),
        fill=alt.Fill("family:N", scale=color_scale, legend=None),
        fillOpacity=alt.value(0.15),
        strokeOpacity=alt.value(0.45),
        order="pt_order:O",
        detail="family:N",
    )
)

# Scatter points
points = (
    alt.Chart(df)
    .mark_circle(opacity=0.8, stroke="white", strokeWidth=0.8)
    .encode(
        x=alt.X("density:Q", scale=x_scale, title="Density (kg/m³)"),
        y=alt.Y("modulus:Q", scale=y_scale, title="Young's Modulus (GPa)"),
        color=alt.Color(
            "family:N",
            scale=color_scale,
            legend=alt.Legend(
                title="Material Family",
                titleFontSize=18,
                labelFontSize=16,
                symbolSize=300,
                orient="right",
                symbolOpacity=0.8,
            ),
        ),
        size=alt.value(160),
        tooltip=["material:N", "family:N", "density:Q", "modulus:Q"],
    )
)

# Family labels with halo effect for readability
label_bg = (
    alt.Chart(df_labels)
    .mark_text(fontSize=15, fontWeight="bold", opacity=0.9)
    .encode(
        x=alt.X("density_center:Q", scale=x_scale),
        y=alt.Y("modulus_center:Q", scale=y_scale),
        text="family:N",
        color=alt.value("white"),
    )
)

labels = (
    alt.Chart(df_labels)
    .mark_text(fontSize=15, fontWeight="bold", opacity=0.9)
    .encode(
        x=alt.X("density_center:Q", scale=x_scale),
        y=alt.Y("modulus_center:Q", scale=y_scale),
        text="family:N",
        color=alt.Color("family:N", scale=color_scale, legend=None),
    )
)

# Performance index guide line: E/ρ = constant (lightweight stiffness)
guide_densities = np.logspace(np.log10(10), np.log10(20000), 50)
guide_lines_rows = []
for ratio, label in [(0.01, "E/ρ = 0.01"), (0.1, "E/ρ = 0.1")]:
    for d in guide_densities:
        m = ratio * d / 1000  # convert to GPa (density in kg/m³, modulus in GPa)
        if 0.0005 <= m <= 1000:
            guide_lines_rows.append({"density": d, "modulus": m, "guide": label})
df_guides = pd.DataFrame(guide_lines_rows)

guides = (
    alt.Chart(df_guides)
    .mark_line(strokeDash=[6, 4], strokeWidth=1.2, opacity=0.35)
    .encode(
        x=alt.X("density:Q", scale=x_scale),
        y=alt.Y("modulus:Q", scale=y_scale),
        detail="guide:N",
        color=alt.value("#555555"),
    )
)

guide_label_data = []
for ratio, label in [(0.01, "E/ρ = 0.01"), (0.1, "E/ρ = 0.1")]:
    d_pos = 15000
    m_pos = ratio * d_pos / 1000
    if 0.0005 <= m_pos <= 1000:
        guide_label_data.append({"density": d_pos, "modulus": m_pos, "guide": label})
df_guide_labels = pd.DataFrame(guide_label_data)

guide_labels = (
    alt.Chart(df_guide_labels)
    .mark_text(fontSize=11, fontStyle="italic", opacity=0.45, angle=328, dy=-12)
    .encode(
        x=alt.X("density:Q", scale=x_scale),
        y=alt.Y("modulus:Q", scale=y_scale),
        text="guide:N",
        color=alt.value("#666666"),
    )
)

# Compose chart: points first to ensure legend renders
base = alt.layer(envelopes, guides, guide_labels, points, label_bg, labels)

chart = (
    base.properties(
        width=1400,
        height=900,
        title=alt.Title("scatter-ashby-material · altair · pyplots.ai", fontSize=28, fontWeight=500),
        padding={"left": 80, "right": 200, "top": 50, "bottom": 60},
    )
    .resolve_scale(color="shared", fill="independent")
    .configure_axis(
        labelFontSize=18, titleFontSize=22, gridOpacity=0.15, grid=True, domainColor="#cccccc", tickColor="#cccccc"
    )
    .configure_view(strokeWidth=0)
    .configure_legend(titleFontSize=18, labelFontSize=16, symbolSize=250, padding=15, offset=10)
)

# Save
chart.save("plot.png", scale_factor=3.0)
chart.save("plot.html")

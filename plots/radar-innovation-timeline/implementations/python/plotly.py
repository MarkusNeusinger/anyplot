""" pyplots.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: plotly 6.5.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-02-18
"""

import numpy as np
import plotly.graph_objects as go


np.random.seed(42)

# Data - Technology innovation items across sectors and time horizons
sectors = ["AI & ML", "Cloud & Infra", "Sustainability", "Biotech"]
rings = ["Adopt", "Trial", "Assess", "Hold"]
ring_radii = {"Adopt": 1.3, "Trial": 2.3, "Assess": 3.3, "Hold": 4.3}
ring_marker_sizes = {"Adopt": 22, "Trial": 17, "Assess": 14, "Hold": 11}
ring_boundaries = [1.8, 2.8, 3.8, 4.8]

innovations = [
    # AI & ML sector
    {"name": "LLM Agents", "sector": "AI & ML", "ring": "Adopt", "textpos": "top center"},
    {"name": "RAG Pipelines", "sector": "AI & ML", "ring": "Adopt", "textpos": "bottom left"},
    {"name": "Multimodal Models", "sector": "AI & ML", "ring": "Trial", "textpos": "top left"},
    {"name": "AI Code Review", "sector": "AI & ML", "ring": "Trial", "textpos": "bottom right"},
    {"name": "Neuromorphic Chips", "sector": "AI & ML", "ring": "Assess", "textpos": "top center"},
    {"name": "Autonomous Research", "sector": "AI & ML", "ring": "Hold", "textpos": "bottom center"},
    {"name": "Quantum ML", "sector": "AI & ML", "ring": "Hold", "textpos": "top center"},
    # Cloud & Infra sector
    {"name": "Platform Engineering", "sector": "Cloud & Infra", "ring": "Adopt", "textpos": "bottom right"},
    {"name": "FinOps", "sector": "Cloud & Infra", "ring": "Adopt", "textpos": "top right"},
    {"name": "WebAssembly", "sector": "Cloud & Infra", "ring": "Trial", "textpos": "top center"},
    {"name": "Edge Computing", "sector": "Cloud & Infra", "ring": "Trial", "textpos": "bottom center"},
    {"name": "Confidential Computing", "sector": "Cloud & Infra", "ring": "Assess", "textpos": "top right"},
    {"name": "Serverless GPUs", "sector": "Cloud & Infra", "ring": "Assess", "textpos": "bottom right"},
    {"name": "Decentralized Cloud", "sector": "Cloud & Infra", "ring": "Hold", "textpos": "top center"},
    # Sustainability sector
    {"name": "Carbon Tracking APIs", "sector": "Sustainability", "ring": "Adopt", "textpos": "top left"},
    {"name": "Green Software", "sector": "Sustainability", "ring": "Trial", "textpos": "bottom right"},
    {"name": "Digital Product Passports", "sector": "Sustainability", "ring": "Trial", "textpos": "top left"},
    {"name": "Circular Economy Platforms", "sector": "Sustainability", "ring": "Assess", "textpos": "bottom right"},
    {"name": "Fusion Energy Tech", "sector": "Sustainability", "ring": "Hold", "textpos": "top center"},
    {"name": "Climate AI", "sector": "Sustainability", "ring": "Assess", "textpos": "top left"},
    # Biotech sector
    {"name": "mRNA Therapeutics", "sector": "Biotech", "ring": "Adopt", "textpos": "top center"},
    {"name": "CRISPR Diagnostics", "sector": "Biotech", "ring": "Trial", "textpos": "bottom left"},
    {"name": "Digital Twins (Health)", "sector": "Biotech", "ring": "Assess", "textpos": "bottom left"},
    {"name": "Synthetic Biology", "sector": "Biotech", "ring": "Assess", "textpos": "top left"},
    {"name": "Brain-Computer Interfaces", "sector": "Biotech", "ring": "Hold", "textpos": "bottom center"},
    {"name": "Longevity Engineering", "sector": "Biotech", "ring": "Hold", "textpos": "top left"},
]

# Sector angular ranges (270-degree layout, starting top, going clockwise)
sector_span = 270 / len(sectors)
sector_starts = {s: i * sector_span for i, s in enumerate(sectors)}

# Color palette (Python Blue first, colorblind-safe)
sector_colors = {"AI & ML": "#306998", "Cloud & Infra": "#E0872B", "Sustainability": "#2A9D8F", "Biotech": "#8E4585"}

# Distinct marker shapes per sector for visual grouping
sector_symbols = {"AI & ML": "circle", "Cloud & Infra": "diamond", "Sustainability": "square", "Biotech": "triangle-up"}

# Compute positions for all items grouped by sector
items_by_sector: dict[str, list[dict]] = {s: [] for s in sectors}

for sector in sectors:
    start_angle = sector_starts[sector]
    sector_items = [inn for inn in innovations if inn["sector"] == sector]

    for ring in rings:
        ring_items = [it for it in sector_items if it["ring"] == ring]
        if not ring_items:
            continue
        n = len(ring_items)
        padding = sector_span * 0.18
        usable_span = sector_span - 2 * padding
        for idx, item in enumerate(ring_items):
            angle = start_angle + sector_span / 2 if n == 1 else start_angle + padding + usable_span * idx / (n - 1)
            base_r = ring_radii[ring]
            jitter = np.random.uniform(-0.18, 0.18)
            items_by_sector[sector].append(
                {"name": item["name"], "ring": ring, "angle": angle, "r": base_r + jitter, "textpos": item["textpos"]}
            )

# Create figure
fig = go.Figure()

# Ring background fills — stronger for Adopt to create visual focal point
ring_fills = [
    (0, ring_boundaries[0], "rgba(48, 105, 152, 0.08)"),
    (ring_boundaries[0], ring_boundaries[1], "rgba(48, 105, 152, 0.05)"),
    (ring_boundaries[1], ring_boundaries[2], "rgba(48, 105, 152, 0.03)"),
    (ring_boundaries[2], ring_boundaries[3], "rgba(48, 105, 152, 0.015)"),
]
theta_fill = np.linspace(0, 270, 200).tolist()
for r_inner, r_outer, fill_color in ring_fills:
    fig.add_trace(
        go.Scatterpolar(
            r=[r_outer] * len(theta_fill) + [r_inner] * len(theta_fill),
            theta=theta_fill + theta_fill[::-1],
            fill="toself",
            fillcolor=fill_color,
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Ring boundary lines
for radius in ring_boundaries:
    theta_circle = np.linspace(0, 270, 200)
    fig.add_trace(
        go.Scatterpolar(
            r=np.full_like(theta_circle, radius).tolist(),
            theta=theta_circle.tolist(),
            mode="lines",
            line={"color": "rgba(0, 0, 0, 0.10)", "width": 1.2},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Sector divider lines (including closing line at 270°)
for angle in [sector_starts[s] for s in sectors] + [270]:
    fig.add_trace(
        go.Scatterpolar(
            r=[0, 5.2],
            theta=[angle, angle],
            mode="lines",
            line={"color": "rgba(0, 0, 0, 0.18)", "width": 1, "dash": "dot"},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Innovation items per sector with marker size varying by ring for visual hierarchy
for sector in sectors:
    items = items_by_sector[sector]
    color = sector_colors[sector]
    fig.add_trace(
        go.Scatterpolar(
            r=[it["r"] for it in items],
            theta=[it["angle"] for it in items],
            mode="markers+text",
            marker={
                "size": [ring_marker_sizes[it["ring"]] for it in items],
                "color": color,
                "symbol": sector_symbols[sector],
                "line": {"color": "white", "width": 2},
                "opacity": [1.0 if it["ring"] == "Adopt" else 0.82 for it in items],
            },
            text=[f"<b>{it['name']}</b>" if it["ring"] == "Adopt" else it["name"] for it in items],
            textposition=[it["textpos"] for it in items],
            textfont={"size": 16, "color": color},
            name=sector,
            legendgroup=sector,
            hovertemplate="%{text}<br>Ring: %{customdata}<extra>" + sector + "</extra>",
            customdata=[it["ring"] for it in items],
        )
    )

# Ring labels — staggered along the right edge past the 270° boundary
ring_label_data = [
    ("Adopt (Now)", ring_radii["Adopt"], 280),
    ("Trial (0-1 yr)", ring_radii["Trial"], 283),
    ("Assess (1-3 yr)", ring_radii["Assess"], 286),
    ("Hold (3+ yr)", ring_radii["Hold"], 289),
]
for label, radius, angle in ring_label_data:
    fig.add_trace(
        go.Scatterpolar(
            r=[radius],
            theta=[angle],
            mode="text",
            text=[f"<b>{label}</b>"],
            textfont={"size": 15, "color": "rgba(60, 60, 60, 0.85)"},
            textposition="middle right",
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Sector header labels along outer edge
for sector in sectors:
    mid_angle = sector_starts[sector] + sector_span / 2
    fig.add_trace(
        go.Scatterpolar(
            r=[5.6],
            theta=[mid_angle],
            mode="text",
            text=[f"<b>{sector}</b>"],
            textfont={"size": 22, "color": sector_colors[sector]},
            textposition="top center",
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Layout with subtitle
fig.update_layout(
    title={
        "text": (
            "radar-innovation-timeline · plotly · pyplots.ai"
            "<br><sup style='color:#666; font-weight:normal'>"
            "Technology adoption radar — inner rings = near-term, outer = longer horizon"
            "</sup>"
        ),
        "font": {"size": 30},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.97,
    },
    polar={
        "radialaxis": {"visible": False, "range": [0, 6.2]},
        "angularaxis": {"visible": False, "direction": "clockwise", "rotation": 90},
        "bgcolor": "rgba(250, 250, 250, 0.3)",
        "domain": {"x": [0.0, 0.82], "y": [0.03, 0.92]},
    },
    legend={
        "font": {"size": 15},
        "x": 0.84,
        "y": 0.55,
        "xanchor": "left",
        "yanchor": "middle",
        "bgcolor": "rgba(255, 255, 255, 0.95)",
        "bordercolor": "rgba(0, 0, 0, 0.15)",
        "borderwidth": 1,
        "title": {"text": "<b>Sectors</b>", "font": {"size": 17}},
    },
    template="plotly_white",
    margin={"l": 30, "r": 50, "t": 90, "b": 30},
    paper_bgcolor="white",
    width=1200,
    height=1200,
    annotations=[
        {
            "text": (
                "<b>Time Horizons</b><br>"
                "● <b>Adopt</b> — ready now<br>"
                "● <b>Trial</b> — evaluating 0-1 yr<br>"
                "● <b>Assess</b> — exploring 1-3 yr<br>"
                "● <b>Hold</b> — future watch 3+ yr"
            ),
            "x": 0.84,
            "y": 0.32,
            "xref": "paper",
            "yref": "paper",
            "xanchor": "left",
            "yanchor": "top",
            "showarrow": False,
            "font": {"size": 15, "color": "#555"},
            "bgcolor": "rgba(255,255,255,0.95)",
            "bordercolor": "rgba(0,0,0,0.12)",
            "borderwidth": 1,
            "borderpad": 8,
        }
    ],
)

# Save
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")

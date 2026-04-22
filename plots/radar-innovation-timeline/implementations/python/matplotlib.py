""" pyplots.ai
radar-innovation-timeline: Innovation Radar with Time-Horizon Rings
Library: matplotlib 3.10.8 | Python 3.14.3
Quality: 88/100 | Created: 2026-02-18
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Technology innovations mapped to time horizons and categories
np.random.seed(42)

rings = ["Adopt", "Trial", "Assess", "Hold"]
sectors = ["AI & ML", "Cloud & Infra", "Data Engineering", "Security"]
n_sectors = len(sectors)

innovations = [
    # AI & ML
    ("LLM Agents", "Adopt", "AI & ML"),
    ("RAG Pipelines", "Trial", "AI & ML"),
    ("Vision Transformers", "Trial", "AI & ML"),
    ("Federated Learning", "Assess", "AI & ML"),
    ("Neuromorphic Chips", "Hold", "AI & ML"),
    ("AI Code Assistants", "Adopt", "AI & ML"),
    # Cloud & Infra
    ("Kubernetes", "Adopt", "Cloud & Infra"),
    ("FinOps Tooling", "Trial", "Cloud & Infra"),
    ("Edge Computing", "Assess", "Cloud & Infra"),
    ("Serverless Containers", "Assess", "Cloud & Infra"),
    ("Quantum Cloud APIs", "Hold", "Cloud & Infra"),
    ("Platform Engineering", "Trial", "Cloud & Infra"),
    # Data Engineering
    ("Apache Iceberg", "Adopt", "Data Engineering"),
    ("Real-time Lakehouse", "Trial", "Data Engineering"),
    ("Data Contracts", "Trial", "Data Engineering"),
    ("Streaming SQL", "Assess", "Data Engineering"),
    ("Data Mesh", "Hold", "Data Engineering"),
    # Security
    ("Zero Trust Arch", "Adopt", "Security"),
    ("SBOM Tooling", "Trial", "Security"),
    ("AI Threat Detection", "Assess", "Security"),
    ("Post-Quantum Crypto", "Assess", "Security"),
    ("Confidential Computing", "Hold", "Security"),
    ("Homomorphic Encryption", "Hold", "Security"),
]

# Indices and mappings
ring_index = {name: i for i, name in enumerate(rings)}
sector_index = {name: i for i, name in enumerate(sectors)}

# Sector colors (colorblind-safe Okabe-Ito family)
sector_colors = {"AI & ML": "#306998", "Cloud & Infra": "#E69F00", "Data Engineering": "#009E73", "Security": "#CC79A7"}
sector_markers = {"AI & ML": "o", "Cloud & Infra": "s", "Data Engineering": "D", "Security": "^"}

# Marker sizes by ring — visual hierarchy: near-term prominent, far-future subtle
ring_marker_sizes = {"Adopt": 280, "Trial": 220, "Assess": 170, "Hold": 130}

# Layout: 270 degrees arc, gap at upper-right for ring labels
arc_span = 3 / 4 * 2 * np.pi
arc_start = np.deg2rad(115)  # Rotated slightly to keep all sector labels on-canvas
sector_width = arc_span / n_sectors

# Ring band boundaries (wide bands to prevent cross-ring label overlap)
ring_boundaries = [0.5, 2.8, 5.1, 7.4, 9.7]

# Count items per ring-sector
sector_ring_counts = {}
for _, ring_name, sector_name in innovations:
    key = (ring_name, sector_name)
    sector_ring_counts[key] = sector_ring_counts.get(key, 0) + 1

# Compute positions
positions = []
sector_ring_placed = {}
for name, ring_name, sector_name in innovations:
    r_idx = ring_index[ring_name]
    s_idx = sector_index[sector_name]
    key = (ring_name, sector_name)

    placed = sector_ring_placed.get(key, 0)
    total = sector_ring_counts[key]
    sector_ring_placed[key] = placed + 1

    # Place markers in the center portion of the ring band (avoid edges)
    band_width = ring_boundaries[r_idx + 1] - ring_boundaries[r_idx]
    r_lo = ring_boundaries[r_idx] + band_width * 0.30
    r_hi = ring_boundaries[r_idx] + band_width * 0.70
    if total == 1:
        r = (r_lo + r_hi) / 2
    elif total == 2:
        r = r_lo + (r_hi - r_lo) * (0.30 + 0.40 * placed)
    else:
        r = r_lo + (r_hi - r_lo) * (placed + 0.5) / total

    # Spread angularly within sector with wider margins
    sector_start = arc_start + s_idx * sector_width
    margin = sector_width * 0.10
    a_lo = sector_start + margin
    a_hi = sector_start + sector_width - margin
    if total == 1:
        theta = (a_lo + a_hi) / 2
    elif total == 2:
        # Wide spread: items at 25% and 75% of angular range
        frac = 0.25 + 0.50 * placed
        # Reverse in odd rings to break radial alignment with adjacent rings
        if r_idx % 2 == 1:
            frac = 1.0 - frac
        theta = a_lo + (a_hi - a_lo) * frac
    else:
        frac = placed / (total - 1)
        if r_idx % 2 == 1:
            frac = 1.0 - frac
        theta = a_lo + (a_hi - a_lo) * frac

    # Small jitter
    theta += np.random.uniform(-0.01, 0.01)
    r += np.random.uniform(-0.02, 0.02)

    positions.append((name, theta, r, sector_name, ring_name, placed, total))

# --- Plot ---
fig = plt.figure(figsize=(12, 12))
ax = fig.add_subplot(111, polar=True)

# Ring fills with pastel coloring
ring_fill_colors = ["#D0E4F5", "#D4EDDA", "#FFF3CD", "#F5C6CB"]
for i in range(len(rings)):
    theta_fill = np.linspace(arc_start, arc_start + arc_span, 300)
    ax.fill_between(
        theta_fill,
        np.full(300, ring_boundaries[i]),
        np.full(300, ring_boundaries[i + 1]),
        color=ring_fill_colors[i],
        alpha=0.40,
    )

# Ring boundary arcs
for boundary in ring_boundaries:
    theta_arc = np.linspace(arc_start, arc_start + arc_span, 300)
    ax.plot(theta_arc, np.full(300, boundary), color="#888888", linewidth=1.0, alpha=0.65)

# Sector divider lines
for i in range(n_sectors + 1):
    angle = arc_start + i * sector_width
    ax.plot([angle, angle], [ring_boundaries[0], ring_boundaries[-1]], color="#888888", linewidth=1.0, alpha=0.65)

# Ring labels in the arc gap (pushed further into gap to avoid item overlaps)
label_angle = arc_start + arc_span + 0.15
for i, ring_name in enumerate(rings):
    r_mid = (ring_boundaries[i] + ring_boundaries[i + 1]) / 2
    ax.text(
        label_angle,
        r_mid,
        ring_name,
        ha="left",
        va="center",
        fontsize=18,
        fontweight="bold",
        color="#444444",
        fontstyle="italic",
    )

# Sector labels along outer edge (closer to ring to avoid figure clipping)
for i, sector_name in enumerate(sectors):
    angle = arc_start + (i + 0.5) * sector_width
    ax.text(
        angle,
        ring_boundaries[-1] + 0.65,
        sector_name,
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        color="#222222",
    )

# Label background for readability
label_bbox = {"boxstyle": "round,pad=0.12", "facecolor": "white", "alpha": 0.85, "edgecolor": "none"}

# Plot markers and labels
for name, theta, r, sector_name, ring_name, placed, total in positions:
    color = sector_colors[sector_name]
    marker = sector_markers[sector_name]
    msize = ring_marker_sizes[ring_name]

    ax.scatter(theta, r, s=msize, color=color, marker=marker, edgecolors="white", linewidth=1.0, zorder=5, alpha=0.95)

    # Labels: alternate direction for multi-item cells; single items always outward
    if total >= 2 and placed % 2 == 1:
        label_offset = -0.55
        va = "top"
    else:
        label_offset = 0.55
        va = "bottom"

    ax.text(
        theta,
        r + label_offset,
        name,
        fontsize=15,
        ha="center",
        va=va,
        color="#222222",
        fontweight="medium",
        bbox=label_bbox,
        zorder=6,
    )

# Styling
ax.set_ylim(0, ring_boundaries[-1] + 1.8)
ax.set_yticklabels([])
ax.set_xticklabels([])
ax.set_xticks([])
ax.set_yticks([])
ax.grid(False)
ax.spines["polar"].set_visible(False)

# Title
ax.set_title("radar-innovation-timeline · matplotlib · pyplots.ai", fontsize=24, fontweight="medium", pad=30)

# Legend in lower-right corner
legend_handles = [
    plt.scatter(
        [], [], s=150, color=sector_colors[s], marker=sector_markers[s], edgecolors="white", linewidth=1.0, label=s
    )
    for s in sectors
]
fig.legend(
    handles=legend_handles,
    loc="lower right",
    fontsize=16,
    framealpha=0.92,
    edgecolor="#CCCCCC",
    title="Sectors",
    title_fontsize=18,
    handletextpad=0.8,
    borderpad=1.0,
    bbox_to_anchor=(0.95, 0.03),
)

fig.subplots_adjust(left=0.05, right=0.95, top=0.93, bottom=0.02)
plt.savefig("plot.png", dpi=300, bbox_inches="tight")

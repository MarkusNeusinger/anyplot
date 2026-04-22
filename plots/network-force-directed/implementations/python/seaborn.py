""" pyplots.ai
network-force-directed: Force-Directed Graph
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


# Set seaborn style
sns.set_theme(style="white")

np.random.seed(42)

# Create sample social network data - organization with 3 departments
num_nodes = 37
community_sizes = [15, 12, 10]
community_names = ["Engineering", "Marketing", "Sales"]
communities = []

# Assign nodes to communities
for comm_idx, size in enumerate(community_sizes):
    communities.extend([comm_idx] * size)

# Generate edges with community structure
edges = []
for i in range(num_nodes):
    for j in range(i + 1, num_nodes):
        if communities[i] == communities[j]:
            # Higher connection probability within community
            if np.random.random() < 0.35:
                weight = np.random.uniform(0.5, 1.0)
                edges.append((i, j, weight))
        else:
            # Lower connection probability between communities
            if np.random.random() < 0.05:
                weight = np.random.uniform(0.3, 0.7)
                edges.append((i, j, weight))

# Calculate node degrees
degrees = [0] * num_nodes
for src, tgt, _ in edges:
    degrees[src] += 1
    degrees[tgt] += 1

# Force-directed layout (Fruchterman-Reingold algorithm inline)
n = num_nodes
k = 0.5
iterations = 150

# Initialize random positions
pos = np.random.rand(n, 2) * 2 - 1

# Temperature for simulated annealing
t = 1.0
dt = t / (iterations + 1)

for _ in range(iterations):
    # Calculate repulsive forces between all pairs
    disp = np.zeros((n, 2))

    for i in range(n):
        for j in range(i + 1, n):
            delta = pos[i] - pos[j]
            dist = max(np.linalg.norm(delta), 0.01)
            force = (k * k) / dist
            force_vec = (delta / dist) * force
            disp[i] += force_vec
            disp[j] -= force_vec

    # Calculate attractive forces along edges
    for src, tgt, _ in edges:
        delta = pos[src] - pos[tgt]
        dist = max(np.linalg.norm(delta), 0.01)
        force = (dist * dist) / k
        force_vec = (delta / dist) * force
        disp[src] -= force_vec
        disp[tgt] += force_vec

    # Apply displacements with temperature limiting
    for i in range(n):
        disp_norm = max(np.linalg.norm(disp[i]), 0.01)
        pos[i] += (disp[i] / disp_norm) * min(disp_norm, t)

    # Cool down
    t -= dt

# Normalize positions to [-1, 1]
pos -= pos.mean(axis=0)
max_coord = np.abs(pos).max()
if max_coord > 0:
    pos /= max_coord

positions = pos

# Extract positions
x_coords = positions[:, 0]
y_coords = positions[:, 1]

# Node sizes based on degree (hub nodes are larger)
node_sizes = [150 + degree * 60 for degree in degrees]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Define community colors using colorblind-safe palette
community_colors = ["#306998", "#FFD43B", "#E74C3C"]  # Python Blue, Yellow, Red

# Draw edges
for src, tgt, weight in edges:
    x0, y0 = positions[src]
    x1, y1 = positions[tgt]
    ax.plot([x0, x1], [y0, y1], color="#CCCCCC", linewidth=1 + weight * 2, alpha=0.5, zorder=1)

# Draw nodes using seaborn scatterplot
sns.scatterplot(
    x=x_coords,
    y=y_coords,
    hue=communities,
    palette=community_colors,
    size=node_sizes,
    sizes=(150, 800),
    alpha=0.85,
    edgecolor="white",
    linewidth=2,
    ax=ax,
    legend=False,
    zorder=2,
)

# Add labels for high-degree nodes (hubs)
degree_threshold = np.percentile(degrees, 75)
for node in range(num_nodes):
    if degrees[node] >= degree_threshold:
        ax.annotate(
            f"Node {node}",
            (positions[node, 0], positions[node, 1]),
            fontsize=12,
            ha="center",
            va="bottom",
            xytext=(0, 10),
            textcoords="offset points",
            fontweight="bold",
            color="#333333",
        )

# Create custom legend for communities
legend_elements = []
for idx, name in enumerate(community_names):
    count = community_sizes[idx]
    legend_elements.append(
        plt.scatter([], [], c=community_colors[idx], s=300, label=f"{name} ({count})", edgecolor="white", linewidth=2)
    )

ax.legend(
    handles=legend_elements,
    loc="upper left",
    fontsize=16,
    title="Department",
    title_fontsize=18,
    frameon=True,
    fancybox=True,
    shadow=True,
)

# Styling
ax.set_title("network-force-directed · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.set_xlabel("Force-Directed X Position", fontsize=20)
ax.set_ylabel("Force-Directed Y Position", fontsize=20)
ax.tick_params(axis="both", labelsize=16)

# Remove axis ticks for cleaner network visualization
ax.set_xticks([])
ax.set_yticks([])

# Add subtle border
for spine in ax.spines.values():
    spine.set_color("#CCCCCC")
    spine.set_linewidth(2)

# Add network statistics annotation
total_edges = len(edges)
avg_degree = sum(degrees) / num_nodes
stats_text = f"Nodes: {num_nodes} | Edges: {total_edges} | Avg Degree: {avg_degree:.1f}"
ax.text(0.5, -0.08, stats_text, transform=ax.transAxes, fontsize=14, ha="center", va="top", color="#666666")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")

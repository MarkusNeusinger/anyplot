""" pyplots.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-31
"""

import matplotlib.pyplot as plt


# Primate phylogenetic tree - pre-computed coordinates
# Each leaf: (name, y_position, x_end) where x_end is total distance from root
# Species ordered by evolutionary grouping (top to bottom)
species = [
    ("Galago", 0, 0.24),
    ("Tarsier", 1, 0.24),
    ("Lemur", 2, 0.18),
    ("Spider Monkey", 3, 0.20),
    ("Capuchin", 4, 0.19),
    ("Baboon", 5, 0.18),
    ("Rhesus Macaque", 6, 0.18),
    ("Gibbon", 7, 0.16),
    ("Orangutan", 8, 0.15),
    ("Gorilla", 9, 0.14),
    ("Chimpanzee", 10, 0.13),
    ("Human", 11, 0.13),
]

# Branch structure: each branch is (x1, y1, x2, y2, color)
# Horizontal branches (to tips)
branch_color = "#306998"
yellow = "#FFD43B"
green = "#5A9C5A"

# Pre-computed branch segments for the phylogenetic tree
# Format: (x_start, y_start, x_end, y_end, color)
branches = [
    # Root split (Prosimians vs Simians)
    (0, 5.5, 0.05, 5.5, branch_color),  # Root to split
    (0.05, 1, 0.05, 5.5, branch_color),  # Vertical at root
    (0.05, 1, 0.05, 10, branch_color),  # Vertical to Simians
    # Prosimians clade
    (0.05, 1, 0.08, 1, green),  # To Prosimians node
    (0.08, 0.5, 0.08, 2, green),  # Prosimians vertical
    (0.08, 0.5, 0.10, 0.5, green),  # To Lorisoids
    (0.10, 0, 0.10, 1, green),  # Lorisoids vertical
    (0.10, 0, 0.24, 0, green),  # To Galago
    (0.10, 1, 0.24, 1, green),  # To Tarsier
    (0.08, 2, 0.18, 2, green),  # To Lemur
    # Simians main branch
    (0.05, 10, 0.08, 10, branch_color),  # To Simians node
    (0.08, 5.5, 0.08, 10, branch_color),  # Simians vertical
    # Apes clade
    (0.08, 10, 0.10, 10, branch_color),  # To Apes
    (0.10, 8.5, 0.10, 10, branch_color),  # Apes vertical
    # African Apes
    (0.10, 10, 0.11, 10, branch_color),  # To African Apes
    (0.11, 9.5, 0.11, 11, branch_color),  # African Apes vertical
    (0.11, 9, 0.14, 9, branch_color),  # To Gorilla
    (0.11, 10.5, 0.12, 10.5, branch_color),  # To Hominini
    (0.12, 10, 0.12, 11, branch_color),  # Hominini vertical
    (0.12, 10, 0.13, 10, branch_color),  # To Chimpanzee
    (0.12, 11, 0.13, 11, branch_color),  # To Human
    # Asian Apes
    (0.10, 8.5, 0.13, 8.5, branch_color),  # To Asian Apes
    (0.13, 7, 0.13, 8, branch_color),  # Asian Apes vertical
    (0.13, 7, 0.16, 7, branch_color),  # To Gibbon
    (0.13, 8, 0.15, 8, branch_color),  # To Orangutan
    # Monkeys clade
    (0.08, 5.5, 0.12, 5.5, yellow),  # To Monkeys
    (0.12, 3.5, 0.12, 5.5, yellow),  # Monkeys vertical
    # Old World Monkeys
    (0.12, 5.5, 0.14, 5.5, yellow),  # To Old World
    (0.14, 5, 0.14, 6, yellow),  # OW vertical
    (0.14, 5, 0.18, 5, yellow),  # To Baboon
    (0.14, 6, 0.18, 6, yellow),  # To Rhesus
    # New World Monkeys
    (0.12, 3.5, 0.15, 3.5, yellow),  # To New World
    (0.15, 3, 0.15, 4, yellow),  # NW vertical
    (0.15, 3, 0.20, 3, yellow),  # To Spider Monkey
    (0.15, 4, 0.19, 4, yellow),  # To Capuchin
]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Draw all branches
for x1, y1, x2, y2, color in branches:
    ax.plot([x1, x2], [y1, y2], color=color, linewidth=2.5, solid_capstyle="round")

# Draw species labels
for name, y, x in species:
    ax.plot(x, y, "o", color=branch_color, markersize=8)
    ax.text(x + 0.008, y, name, va="center", ha="left", fontsize=16, fontweight="medium")

# Style the plot
ax.set_xlabel("Evolutionary Distance (substitutions per site)", fontsize=20)
ax.set_title("Primate Evolution · tree-phylogenetic · matplotlib · pyplots.ai", fontsize=24)

# Set axis limits
ax.set_xlim(-0.02, 0.38)
ax.set_ylim(-1, 12.5)

# Style ticks
ax.tick_params(axis="x", labelsize=16)
ax.tick_params(axis="y", left=False, labelleft=False)

# Add subtle grid on x-axis only
ax.grid(True, axis="x", alpha=0.3, linestyle="--")

# Remove spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)

# Add scale bar
ax.plot([0, 0.05], [-0.5, -0.5], color="#333333", linewidth=3, solid_capstyle="butt")
ax.text(0.025, -0.8, "0.05", ha="center", va="top", fontsize=14, color="#333333")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")

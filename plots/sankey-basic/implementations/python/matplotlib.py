""" pyplots.ai
sankey-basic: Basic Sankey Diagram
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-23
"""

import matplotlib.pyplot as plt
from matplotlib.sankey import Sankey


# Data - Energy flow example (in TWh - Terawatt-hours)
# This shows how energy from primary sources flows through generation
# to end-use sectors, demonstrating the typical Sankey flow pattern

# Primary energy sources (inputs)
coal = 120
natural_gas = 90
nuclear = 60
renewables = 30
total_primary = coal + natural_gas + nuclear + renewables  # 300 TWh

# Energy lost in generation/transmission
losses = 100

# Net energy delivered to sectors
residential = 55
commercial = 45
industrial = 80
transportation = 20
net_delivered = residential + commercial + industrial + transportation  # 200 TWh

# Verify balance: inputs = outputs + losses
assert total_primary == net_delivered + losses, "Energy balance must be maintained"

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Create Sankey diagram with improved settings
sankey = Sankey(
    ax=ax, scale=0.0025, offset=0.25, head_angle=120, format="", unit="", gap=0.5, radius=0.15, shoulder=0.04
)

# Add primary sources to generation hub (first diagram)
# Positive flows = inputs (from sources)
# Negative flows = outputs (to next stage or losses)
sankey.add(
    flows=[coal, natural_gas, nuclear, renewables, -losses, -net_delivered],
    labels=["Coal\n120 TWh", "Natural Gas\n90 TWh", "Nuclear\n60 TWh", "Renewables\n30 TWh", "Losses\n100 TWh", ""],
    orientations=[-1, 0, 1, 1, -1, 0],
    pathlengths=[0.6, 0.3, 0.6, 0.8, 0.5, 0.5],
    facecolor="#306998",
    edgecolor="#1a3a52",
    alpha=0.75,
    linewidth=2,
)

# Add distribution to end-use sectors (second diagram connected to first)
sankey.add(
    flows=[net_delivered, -residential, -commercial, -industrial, -transportation],
    labels=["", "Residential\n55 TWh", "Commercial\n45 TWh", "Industrial\n80 TWh", "Transport\n20 TWh"],
    orientations=[0, -1, 0, 1, 1],
    pathlengths=[0.3, 0.6, 0.3, 0.6, 0.8],
    prior=0,
    connect=(5, 0),
    facecolor="#FFD43B",
    edgecolor="#b8960f",
    alpha=0.75,
    linewidth=2,
)

# Finish and get diagram objects
diagrams = sankey.finish()

# Style all labels with larger fonts for visibility
for diagram in diagrams:
    for text in diagram.texts:
        text.set_fontsize(18)
        text.set_fontweight("bold")

# Set title
ax.set_title("National Energy Flow · sankey-basic · matplotlib · pyplots.ai", fontsize=26, fontweight="bold", pad=30)

# Remove axes for cleaner look
ax.axis("off")

# Add a subtle annotation explaining the diagram
ax.text(
    0.5,
    -0.08,
    "Energy sources → Generation & Losses → End-use sectors (300 TWh total primary energy)",
    transform=ax.transAxes,
    fontsize=16,
    ha="center",
    color="#555555",
    style="italic",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")

""" pyplots.ai
box-horizontal: Horizontal Box Plot
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 94/100 | Created: 2025-12-30
"""

import matplotlib.pyplot as plt
import numpy as np


# Data - Response times (ms) by service type
np.random.seed(42)

# Different services with varying response time distributions
services = [
    "Authentication Service",
    "Database Query",
    "File Upload",
    "Payment Processing",
    "Email Notification",
    "Image Processing",
]

# Generate data with different distributions to show variety
data = [
    np.random.normal(150, 30, 80),  # Auth - tight distribution
    np.concatenate([np.random.normal(200, 40, 70), [450, 480, 520]]),  # DB - with outliers
    np.random.normal(500, 100, 90),  # File upload - wider spread
    np.random.exponential(180, 85) + 100,  # Payment - skewed right
    np.random.normal(80, 15, 75),  # Email - fast and tight
    np.random.uniform(300, 800, 60),  # Image - wide uniform spread
]

# Create figure
fig, ax = plt.subplots(figsize=(16, 9))

# Create horizontal box plot
bp = ax.boxplot(
    data,
    vert=False,
    tick_labels=services,
    patch_artist=True,
    widths=0.6,
    flierprops={"marker": "o", "markersize": 8, "markerfacecolor": "#FFD43B", "markeredgecolor": "#306998"},
    medianprops={"color": "#FFD43B", "linewidth": 2.5},
    whiskerprops={"color": "#306998", "linewidth": 2},
    capprops={"color": "#306998", "linewidth": 2},
    boxprops={"facecolor": "#306998", "edgecolor": "#306998", "linewidth": 2, "alpha": 0.7},
)

# Labels and styling
ax.set_xlabel("Response Time (ms)", fontsize=20)
ax.set_ylabel("Service Type", fontsize=20)
ax.set_title("box-horizontal · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--", axis="x")

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")

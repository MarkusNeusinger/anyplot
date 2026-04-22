""" pyplots.ai
venn-basic: Venn Diagram
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-29
"""

import matplotlib.pyplot as plt
from matplotlib_venn import venn3


# Data: Developer survey - programming language proficiency
# venn3 expects exclusive counts for each region:
# venn3 expects: (Abc, aBc, ABc, abC, AbC, aBC, ABC)
# Where uppercase = in set, lowercase = not in set
only_a = 40  # Only Python
only_b = 25  # Only JavaScript
a_and_b = 20  # Python + JavaScript (not SQL)
only_c = 15  # Only SQL
a_and_c = 10  # Python + SQL (not JavaScript)
b_and_c = 15  # JavaScript + SQL (not Python)
a_and_b_and_c = 10  # All three

# Plot
fig, ax = plt.subplots(figsize=(12, 12))

# Create Venn diagram with subset sizes
venn = venn3(
    subsets=(only_a, only_b, a_and_b, only_c, a_and_c, b_and_c, a_and_b_and_c),
    set_labels=("Python", "JavaScript", "SQL"),
    ax=ax,
    alpha=0.6,
    set_colors=("#306998", "#FFD43B", "#4ECDC4"),
)

# Style circle labels (set names)
for text in venn.set_labels:
    if text:
        text.set_fontsize(24)
        text.set_fontweight("bold")

# Style subset labels (numbers in regions)
for text in venn.subset_labels:
    if text:
        text.set_fontsize(20)
        text.set_fontweight("bold")

ax.set_title("venn-basic · matplotlib · pyplots.ai", fontsize=28, fontweight="bold", pad=20)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="white")

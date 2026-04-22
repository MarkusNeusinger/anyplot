""" pyplots.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: plotnine 0.15.2 | Python 3.13.11
Quality: 90/100 | Created: 2025-12-31
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_color_manual,
    theme,
    theme_void,
)


# Phylogenetic tree data for primate evolution (mitochondrial DNA based)
# Tree structure with branch lengths (simplified representation)
# Format: parent -> child with branch length representing evolutionary distance

np.random.seed(42)

# Define tree structure manually for primate phylogeny
# Coordinates computed from tree topology with branch lengths
# Y positions for leaf nodes (species)
species = ["Human", "Chimpanzee", "Gorilla", "Orangutan", "Gibbon", "Macaque", "Baboon", "Lemur"]
n_species = len(species)

# Evolutionary distances (substitutions per site, scaled for visualization)
# Branch lengths represent molecular clock estimates

# Build tree layout coordinates
# Using rectangular/cladogram layout with proportional branch lengths

# Y coordinates for leaves (evenly spaced)
leaf_y = {species[i]: i for i in range(n_species)}

# Define internal nodes and their x positions (evolutionary time)
# Root is at x=0, tips at varying x based on total branch length

# Tree topology for primates:
# Root -> (Strepsirrhini: Lemur) + (Haplorrhini: rest)
# Haplorrhini -> (Catarrhini: Old World) + (Hylobatidae: Gibbon)
# Catarrhini -> (Cercopithecidae: Macaque, Baboon) + (Hominoidea: great apes)
# Hominoidea -> (Ponginae: Orangutan) + (Homininae: African apes)
# Homininae -> (Gorillini: Gorilla) + (Hominini: Human, Chimp)

# X positions (cumulative branch lengths from root)
branch_data = {
    # Internal nodes x positions
    "root": 0.0,
    "haplorrhini": 0.15,
    "strepsirrhini": 0.15,
    "catarrhini": 0.25,
    "hylobatidae": 0.25,
    "hominoidea": 0.35,
    "cercopithecidae": 0.35,
    "homininae": 0.45,
    "ponginae": 0.45,
    "hominini": 0.55,
    "gorillini": 0.55,
}

# Leaf x positions (tips)
leaf_x = {
    "Human": 0.65,
    "Chimpanzee": 0.65,
    "Gorilla": 0.60,
    "Orangutan": 0.55,
    "Gibbon": 0.50,
    "Macaque": 0.55,
    "Baboon": 0.55,
    "Lemur": 0.45,
}

# Calculate internal node y positions (average of children)
internal_y = {
    "hominini": (leaf_y["Human"] + leaf_y["Chimpanzee"]) / 2,
    "gorillini": leaf_y["Gorilla"],
    "homininae": (leaf_y["Human"] + leaf_y["Chimpanzee"] + leaf_y["Gorilla"]) / 3,
    "ponginae": leaf_y["Orangutan"],
    "hominoidea": (leaf_y["Human"] + leaf_y["Chimpanzee"] + leaf_y["Gorilla"] + leaf_y["Orangutan"]) / 4,
    "hylobatidae": leaf_y["Gibbon"],
    "catarrhini": (leaf_y["Human"] + leaf_y["Chimpanzee"] + leaf_y["Gorilla"] + leaf_y["Orangutan"] + leaf_y["Gibbon"])
    / 5,
    "cercopithecidae": (leaf_y["Macaque"] + leaf_y["Baboon"]) / 2,
    "haplorrhini": (
        leaf_y["Human"]
        + leaf_y["Chimpanzee"]
        + leaf_y["Gorilla"]
        + leaf_y["Orangutan"]
        + leaf_y["Gibbon"]
        + leaf_y["Macaque"]
        + leaf_y["Baboon"]
    )
    / 7,
    "strepsirrhini": leaf_y["Lemur"],
    "root": sum(leaf_y.values()) / len(leaf_y),
}

# Build segments for the tree (horizontal and vertical lines)
segments = []

# Horizontal branches (from parent to child x position)
# Vertical connectors (at parent x position, connecting children)

# Root to main clades
segments.append(
    {
        "x": branch_data["root"],
        "xend": branch_data["haplorrhini"],
        "y": internal_y["haplorrhini"],
        "yend": internal_y["haplorrhini"],
        "clade": "Haplorrhini",
    }
)
segments.append(
    {
        "x": branch_data["root"],
        "xend": branch_data["strepsirrhini"],
        "y": internal_y["strepsirrhini"],
        "yend": internal_y["strepsirrhini"],
        "clade": "Strepsirrhini",
    }
)

# Vertical connector at root
segments.append(
    {
        "x": branch_data["root"],
        "xend": branch_data["root"],
        "y": internal_y["haplorrhini"],
        "yend": internal_y["strepsirrhini"],
        "clade": "Root",
    }
)

# Strepsirrhini to Lemur
segments.append(
    {
        "x": branch_data["strepsirrhini"],
        "xend": leaf_x["Lemur"],
        "y": leaf_y["Lemur"],
        "yend": leaf_y["Lemur"],
        "clade": "Strepsirrhini",
    }
)

# Haplorrhini to Catarrhini and Hylobatidae
segments.append(
    {
        "x": branch_data["haplorrhini"],
        "xend": branch_data["catarrhini"],
        "y": internal_y["catarrhini"],
        "yend": internal_y["catarrhini"],
        "clade": "Haplorrhini",
    }
)
segments.append(
    {
        "x": branch_data["haplorrhini"],
        "xend": branch_data["catarrhini"],
        "y": internal_y["cercopithecidae"],
        "yend": internal_y["cercopithecidae"],
        "clade": "Haplorrhini",
    }
)

# Vertical at haplorrhini
segments.append(
    {
        "x": branch_data["haplorrhini"],
        "xend": branch_data["haplorrhini"],
        "y": internal_y["catarrhini"],
        "yend": internal_y["cercopithecidae"],
        "clade": "Haplorrhini",
    }
)

# Catarrhini splits
# To Hominoidea
segments.append(
    {
        "x": branch_data["catarrhini"],
        "xend": branch_data["hominoidea"],
        "y": internal_y["hominoidea"],
        "yend": internal_y["hominoidea"],
        "clade": "Hominoidea",
    }
)
# To Gibbon
segments.append(
    {
        "x": branch_data["catarrhini"],
        "xend": leaf_x["Gibbon"],
        "y": leaf_y["Gibbon"],
        "yend": leaf_y["Gibbon"],
        "clade": "Hylobatidae",
    }
)

# Vertical at catarrhini
segments.append(
    {
        "x": branch_data["catarrhini"],
        "xend": branch_data["catarrhini"],
        "y": internal_y["hominoidea"],
        "yend": leaf_y["Gibbon"],
        "clade": "Catarrhini",
    }
)

# Cercopithecidae to Macaque and Baboon
segments.append(
    {
        "x": branch_data["catarrhini"],
        "xend": leaf_x["Macaque"],
        "y": leaf_y["Macaque"],
        "yend": leaf_y["Macaque"],
        "clade": "Cercopithecidae",
    }
)
segments.append(
    {
        "x": branch_data["catarrhini"],
        "xend": leaf_x["Baboon"],
        "y": leaf_y["Baboon"],
        "yend": leaf_y["Baboon"],
        "clade": "Cercopithecidae",
    }
)

# Vertical at cercopithecidae split
segments.append(
    {
        "x": branch_data["catarrhini"],
        "xend": branch_data["catarrhini"],
        "y": leaf_y["Macaque"],
        "yend": leaf_y["Baboon"],
        "clade": "Cercopithecidae",
    }
)

# Hominoidea to Homininae and Orangutan
segments.append(
    {
        "x": branch_data["hominoidea"],
        "xend": branch_data["homininae"],
        "y": internal_y["homininae"],
        "yend": internal_y["homininae"],
        "clade": "Homininae",
    }
)
segments.append(
    {
        "x": branch_data["hominoidea"],
        "xend": leaf_x["Orangutan"],
        "y": leaf_y["Orangutan"],
        "yend": leaf_y["Orangutan"],
        "clade": "Ponginae",
    }
)

# Vertical at hominoidea
segments.append(
    {
        "x": branch_data["hominoidea"],
        "xend": branch_data["hominoidea"],
        "y": internal_y["homininae"],
        "yend": leaf_y["Orangutan"],
        "clade": "Hominoidea",
    }
)

# Homininae to Hominini and Gorilla
segments.append(
    {
        "x": branch_data["homininae"],
        "xend": branch_data["hominini"],
        "y": internal_y["hominini"],
        "yend": internal_y["hominini"],
        "clade": "Hominini",
    }
)
segments.append(
    {
        "x": branch_data["homininae"],
        "xend": leaf_x["Gorilla"],
        "y": leaf_y["Gorilla"],
        "yend": leaf_y["Gorilla"],
        "clade": "Gorillini",
    }
)

# Vertical at homininae
segments.append(
    {
        "x": branch_data["homininae"],
        "xend": branch_data["homininae"],
        "y": internal_y["hominini"],
        "yend": leaf_y["Gorilla"],
        "clade": "Homininae",
    }
)

# Hominini to Human and Chimpanzee
segments.append(
    {
        "x": branch_data["hominini"],
        "xend": leaf_x["Human"],
        "y": leaf_y["Human"],
        "yend": leaf_y["Human"],
        "clade": "Hominini",
    }
)
segments.append(
    {
        "x": branch_data["hominini"],
        "xend": leaf_x["Chimpanzee"],
        "y": leaf_y["Chimpanzee"],
        "yend": leaf_y["Chimpanzee"],
        "clade": "Hominini",
    }
)

# Vertical at hominini
segments.append(
    {
        "x": branch_data["hominini"],
        "xend": branch_data["hominini"],
        "y": leaf_y["Human"],
        "yend": leaf_y["Chimpanzee"],
        "clade": "Hominini",
    }
)

# Create DataFrames
df_segments = pd.DataFrame(segments)

# Leaf nodes for labels
df_leaves = pd.DataFrame({"x": [leaf_x[s] for s in species], "y": [leaf_y[s] for s in species], "species": species})

# Define clade colors
clade_colors = {
    "Root": "#555555",
    "Strepsirrhini": "#8B4513",  # Brown for lemurs
    "Haplorrhini": "#306998",  # Python blue
    "Catarrhini": "#306998",
    "Hylobatidae": "#228B22",  # Green for gibbons
    "Hominoidea": "#306998",
    "Cercopithecidae": "#DC143C",  # Crimson for Old World monkeys
    "Homininae": "#FFD43B",  # Python yellow
    "Ponginae": "#FF8C00",  # Orange for orangutans
    "Gorillini": "#FFD43B",
    "Hominini": "#FFD43B",
}

# Map colors to segments
df_segments["color"] = df_segments["clade"].map(clade_colors)

# Create the plot
plot = (
    ggplot()
    + geom_segment(df_segments, aes(x="x", xend="xend", y="y", yend="yend", color="clade"), size=2.5)
    + geom_point(df_leaves, aes(x="x", y="y"), size=5, color="#306998")
    + geom_text(df_leaves, aes(x="x", y="y", label="species"), ha="left", nudge_x=0.02, size=14, color="#222222")
    + scale_color_manual(values=clade_colors)
    # Scale bar annotation
    + annotate("segment", x=0.0, xend=0.1, y=-0.8, yend=-0.8, size=2.5, color="#333333")
    + annotate("text", x=0.05, y=-1.3, label="0.1 substitutions/site", size=16, color="#333333")
    + labs(
        title="Primate Phylogeny · tree-phylogenetic · plotnine · pyplots.ai",
        x="Evolutionary Distance (substitutions per site)",
    )
    + coord_cartesian(xlim=(-0.05, 0.85), ylim=(-1.5, 7.5))
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, ha="center", weight="bold"),
        legend_position=(0.88, 0.75),
        legend_title=element_text(size=14, weight="bold"),
        legend_text=element_text(size=12),
        legend_background=element_rect(fill="white", alpha=0.8),
        legend_key=element_blank(),
        plot_margin=0.05,
    )
    + labs(color="Clade")
)

# Save the plot
plot.save("plot.png", dpi=300, verbose=False)

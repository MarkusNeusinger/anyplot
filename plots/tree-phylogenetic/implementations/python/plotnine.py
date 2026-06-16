""" anyplot.ai
tree-phylogenetic: Phylogenetic Tree Diagram
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-15
"""

import os

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


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477"]

np.random.seed(42)

# Phylogenetic tree data for primate evolution (mitochondrial DNA based)
species = ["Human", "Chimpanzee", "Gorilla", "Orangutan", "Gibbon", "Macaque", "Baboon", "Lemur"]
n_species = len(species)

leaf_y = {species[i]: i for i in range(n_species)}

branch_data = {
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

segments = [
    {
        "x": branch_data["root"],
        "xend": branch_data["haplorrhini"],
        "y": internal_y["haplorrhini"],
        "yend": internal_y["haplorrhini"],
        "clade": "Haplorrhini",
    },
    {
        "x": branch_data["root"],
        "xend": branch_data["strepsirrhini"],
        "y": internal_y["strepsirrhini"],
        "yend": internal_y["strepsirrhini"],
        "clade": "Strepsirrhini",
    },
    {
        "x": branch_data["root"],
        "xend": branch_data["root"],
        "y": internal_y["haplorrhini"],
        "yend": internal_y["strepsirrhini"],
        "clade": "Root",
    },
    {
        "x": branch_data["strepsirrhini"],
        "xend": leaf_x["Lemur"],
        "y": leaf_y["Lemur"],
        "yend": leaf_y["Lemur"],
        "clade": "Strepsirrhini",
    },
    {
        "x": branch_data["haplorrhini"],
        "xend": branch_data["catarrhini"],
        "y": internal_y["catarrhini"],
        "yend": internal_y["catarrhini"],
        "clade": "Haplorrhini",
    },
    {
        "x": branch_data["haplorrhini"],
        "xend": branch_data["catarrhini"],
        "y": internal_y["cercopithecidae"],
        "yend": internal_y["cercopithecidae"],
        "clade": "Haplorrhini",
    },
    {
        "x": branch_data["haplorrhini"],
        "xend": branch_data["haplorrhini"],
        "y": internal_y["catarrhini"],
        "yend": internal_y["cercopithecidae"],
        "clade": "Haplorrhini",
    },
    {
        "x": branch_data["catarrhini"],
        "xend": branch_data["hominoidea"],
        "y": internal_y["hominoidea"],
        "yend": internal_y["hominoidea"],
        "clade": "Hominoidea",
    },
    {
        "x": branch_data["catarrhini"],
        "xend": leaf_x["Gibbon"],
        "y": leaf_y["Gibbon"],
        "yend": leaf_y["Gibbon"],
        "clade": "Hylobatidae",
    },
    {
        "x": branch_data["catarrhini"],
        "xend": branch_data["catarrhini"],
        "y": internal_y["hominoidea"],
        "yend": leaf_y["Gibbon"],
        "clade": "Catarrhini",
    },
    {
        "x": branch_data["catarrhini"],
        "xend": leaf_x["Macaque"],
        "y": leaf_y["Macaque"],
        "yend": leaf_y["Macaque"],
        "clade": "Cercopithecidae",
    },
    {
        "x": branch_data["catarrhini"],
        "xend": leaf_x["Baboon"],
        "y": leaf_y["Baboon"],
        "yend": leaf_y["Baboon"],
        "clade": "Cercopithecidae",
    },
    {
        "x": branch_data["catarrhini"],
        "xend": branch_data["catarrhini"],
        "y": leaf_y["Macaque"],
        "yend": leaf_y["Baboon"],
        "clade": "Cercopithecidae",
    },
    {
        "x": branch_data["hominoidea"],
        "xend": branch_data["homininae"],
        "y": internal_y["homininae"],
        "yend": internal_y["homininae"],
        "clade": "Homininae",
    },
    {
        "x": branch_data["hominoidea"],
        "xend": leaf_x["Orangutan"],
        "y": leaf_y["Orangutan"],
        "yend": leaf_y["Orangutan"],
        "clade": "Ponginae",
    },
    {
        "x": branch_data["hominoidea"],
        "xend": branch_data["hominoidea"],
        "y": internal_y["homininae"],
        "yend": leaf_y["Orangutan"],
        "clade": "Hominoidea",
    },
    {
        "x": branch_data["homininae"],
        "xend": branch_data["hominini"],
        "y": internal_y["hominini"],
        "yend": internal_y["hominini"],
        "clade": "Hominini",
    },
    {
        "x": branch_data["homininae"],
        "xend": leaf_x["Gorilla"],
        "y": leaf_y["Gorilla"],
        "yend": leaf_y["Gorilla"],
        "clade": "Gorillini",
    },
    {
        "x": branch_data["homininae"],
        "xend": branch_data["homininae"],
        "y": internal_y["hominini"],
        "yend": leaf_y["Gorilla"],
        "clade": "Homininae",
    },
    {
        "x": branch_data["hominini"],
        "xend": leaf_x["Human"],
        "y": leaf_y["Human"],
        "yend": leaf_y["Human"],
        "clade": "Hominini",
    },
    {
        "x": branch_data["hominini"],
        "xend": leaf_x["Chimpanzee"],
        "y": leaf_y["Chimpanzee"],
        "yend": leaf_y["Chimpanzee"],
        "clade": "Hominini",
    },
    {
        "x": branch_data["hominini"],
        "xend": branch_data["hominini"],
        "y": leaf_y["Human"],
        "yend": leaf_y["Chimpanzee"],
        "clade": "Hominini",
    },
]

df_segments = pd.DataFrame(segments)
df_leaves = pd.DataFrame({"x": [leaf_x[s] for s in species], "y": [leaf_y[s] for s in species], "species": species})

clade_colors = {
    "Root": "#999999",
    "Strepsirrhini": IMPRINT[0],
    "Haplorrhini": IMPRINT[1],
    "Catarrhini": IMPRINT[2],
    "Hylobatidae": IMPRINT[3],
    "Hominoidea": IMPRINT[4],
    "Cercopithecidae": IMPRINT[5],
    "Homininae": IMPRINT[6],
    "Ponginae": IMPRINT[0],
    "Gorillini": IMPRINT[1],
    "Hominini": IMPRINT[2],
}

df_segments["color"] = df_segments["clade"].map(clade_colors)

plot = (
    ggplot()
    + geom_segment(df_segments, aes(x="x", xend="xend", y="y", yend="yend", color="clade"), size=2.5)
    + geom_point(df_leaves, aes(x="x", y="y"), size=5, color=IMPRINT[0])
    + geom_text(df_leaves, aes(x="x", y="y", label="species"), ha="left", nudge_x=0.02, size=14, color=INK)
    + scale_color_manual(values=clade_colors)
    + annotate("segment", x=0.0, xend=0.1, y=-0.8, yend=-0.8, size=2.5, color=INK_SOFT)
    + annotate("text", x=0.05, y=-1.3, label="0.1 substitutions/site", size=16, color=INK_SOFT)
    + labs(title="tree-phylogenetic · plotnine · anyplot.ai", x="Evolutionary Distance (substitutions per site)")
    + coord_cartesian(xlim=(-0.05, 0.85), ylim=(-1.5, 7.5))
    + theme_void()
    + theme(
        figure_size=(16, 9),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        plot_title=element_text(size=24, ha="center", color=INK),
        legend_position=(0.88, 0.75),
        legend_background=element_rect(fill=PAGE_BG, alpha=0.95),
        legend_title=element_text(size=14, color=INK),
        legend_text=element_text(size=12, color=INK_SOFT),
        legend_key=element_blank(),
        plot_margin=0.05,
    )
    + labs(color="Clade")
)

plot.save(f"plot-{THEME}.png", dpi=300, verbose=False)

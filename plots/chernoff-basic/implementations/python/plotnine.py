"""anyplot.ai
chernoff-basic: Chernoff Faces for Multivariate Data
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-11-21
"""

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    coord_fixed,
    element_rect,
    element_text,
    facet_wrap,
    geom_path,
    geom_point,
    geom_polygon,
    ggplot,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
OBSERVATION = "Car"  # role: observation_id
GROUP = "Category"  # role: extra
VARIABLES = ["Engine power (HP)", "Fuel efficiency (MPG)", "Safety rating", "Comfort score"]  # role: variable_

# Data: replace this block with your own table, for example df = pd.read_csv("cars.csv")
df = pd.DataFrame(
    {
        OBSERVATION: ["Compact A", "Compact B", "Sedan A", "Sedan B", "SUV A", "SUV B"],
        GROUP: ["Compact", "Compact", "Sedan", "Sedan", "SUV", "SUV"],
        VARIABLES[0]: [100, 150, 180, 220, 280, 320],
        VARIABLES[1]: [38, 30, 26, 22, 18, 15],
        VARIABLES[2]: [3.9, 4.5, 4.8, 4.2, 4.6, 4.9],
        VARIABLES[3]: [3.0, 3.6, 4.5, 4.1, 4.0, 4.4],
    }
)

# Plot: reads only df and the constants above
# Normalize every variable to 0-1 before mapping it to a facial feature
values = df[VARIABLES].astype(float)
span = (values.max() - values.min()).replace(0, 1)
normalized = ((values - values.min()) / span).fillna(0.5)

face_widths = 0.6 + normalized[VARIABLES[0]] * 0.4
face_heights = 0.8 + normalized[VARIABLES[1]] * 0.4
eye_sizes = 0.08 + normalized[VARIABLES[2]] * 0.1
mouth_curvatures = -0.3 + normalized[VARIABLES[3]] * 0.6

parts = []


def add(obs, group, part, x, y):
    parts.append(pd.DataFrame({"obs": obs, "group": group, "part": part, "x": x, "y": y}))


for idx in range(len(df)):
    obs = str(df[OBSERVATION].iloc[idx])
    group = str(df[GROUP].iloc[idx])
    fw, fh = face_widths.iloc[idx], face_heights.iloc[idx]
    es, mc = eye_sizes.iloc[idx], mouth_curvatures.iloc[idx]

    theta = np.linspace(0, 2 * np.pi, 50)
    add(obs, group, "face", fw * np.cos(theta), fh * np.sin(theta))

    theta = np.linspace(0, 2 * np.pi, 20)
    for side, name in ((-1, "left"), (1, "right")):
        cx, cy = side * fw * 0.35, fh * 0.25
        add(obs, group, f"{name}_eye", cx + es * np.cos(theta), cy + es * np.sin(theta))
        add(obs, group, f"{name}_pupil", [cx], [cy])
        x_brow = np.linspace(cx - es, cx + es, 10)
        add(obs, group, f"{name}_eyebrow", x_brow, fh * 0.45 - side * 0.05 * (x_brow - cx) / es)

    x_mouth = np.linspace(-fw * 0.25, fw * 0.25, 20)
    add(obs, group, "mouth", x_mouth, -fh * 0.35 + mc * ((x_mouth / (fw * 0.25)) ** 2 - 1))
    add(obs, group, "nose", [0, 0], [fh * 0.1, -fh * 0.1])

plot_df = pd.concat(parts, ignore_index=True)
plot_df["obs"] = pd.Categorical(plot_df["obs"], categories=pd.unique(plot_df["obs"].dropna()))


def layer(name):
    return plot_df[plot_df["part"] == name]


anyplot_theme = theme(
    figure_size=(8, 4.5),
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    plot_title=element_text(size=12, weight="bold", color=INK, ha="center"),
    plot_subtitle=element_text(size=8, color=INK_SOFT, ha="center"),
    plot_caption=element_text(size=8, color=INK_SOFT, ha="center"),
    legend_position="bottom",
    legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_title=element_text(size=9, color=INK),
    legend_text=element_text(size=8, color=INK_SOFT),
    strip_text=element_text(size=9, color=INK, weight="bold"),
)

key = f"Face width = {VARIABLES[0]}  ·  Face height = {VARIABLES[1]}  ·  Eye size = {VARIABLES[2]}  ·  Mouth curve (smile) = {VARIABLES[3]}"

plot = (
    ggplot()
    + geom_polygon(data=layer("face"), mapping=aes(x="x", y="y", group="obs", fill="group"), color=INK_SOFT, size=0.8)
    + geom_polygon(
        data=layer("left_eye"), mapping=aes(x="x", y="y", group="obs"), fill=ELEVATED_BG, color=INK_SOFT, size=0.4
    )
    + geom_polygon(
        data=layer("right_eye"), mapping=aes(x="x", y="y", group="obs"), fill=ELEVATED_BG, color=INK_SOFT, size=0.4
    )
    + geom_point(data=layer("left_pupil"), mapping=aes(x="x", y="y"), color=INK_SOFT, size=2.5)
    + geom_point(data=layer("right_pupil"), mapping=aes(x="x", y="y"), color=INK_SOFT, size=2.5)
    + geom_path(data=layer("mouth"), mapping=aes(x="x", y="y", group="obs"), color=INK_SOFT, size=0.7)
    + geom_path(data=layer("nose"), mapping=aes(x="x", y="y", group="obs"), color=INK_SOFT, size=0.6)
    + geom_path(data=layer("left_eyebrow"), mapping=aes(x="x", y="y", group="obs"), color=INK_SOFT, size=0.7)
    + geom_path(data=layer("right_eyebrow"), mapping=aes(x="x", y="y", group="obs"), color=INK_SOFT, size=0.7)
    + facet_wrap("obs", ncol=3)
    + scale_fill_manual(values=IMPRINT_PALETTE, limits=pd.unique(df[GROUP].astype(str)).tolist())
    + labs(
        fill=GROUP,
        title="chernoff-basic · python · plotnine · anyplot.ai",
        subtitle="Car performance profiles",
        caption=key,
    )
    + theme_void()
    + anyplot_theme
    + coord_fixed(ratio=1)
)

plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")

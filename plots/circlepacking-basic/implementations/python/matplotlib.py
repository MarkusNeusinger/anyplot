"""anyplot.ai
circlepacking-basic: Circle Packing Chart
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-11
"""

import os

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (positions 1-8)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Column constants
ID = "id"  # role: id
PARENT = "parent"  # role: parent
VALUE = "value"  # role: value
LABEL = "label"  # role: label

# Data
df = pd.DataFrame(
    [
        ("Company", None, np.nan),
        ("Engineering", "Company", np.nan),
        ("Product", "Company", np.nan),
        ("Operations", "Company", np.nan),
        ("Sales", "Company", np.nan),
        ("Frontend", "Engineering", 25),
        ("Backend", "Engineering", 35),
        ("DevOps", "Engineering", 15),
        ("QA", "Engineering", 20),
        ("Design", "Product", 18),
        ("Research", "Product", 12),
        ("PM", "Product", 8),
        ("HR", "Operations", 10),
        ("Finance", "Operations", 12),
        ("Legal", "Operations", 6),
        ("Admin", "Operations", 8),
        ("North", "Sales", 22),
        ("South", "Sales", 18),
        ("Intl", "Sales", 28),
    ],
    columns=[ID, PARENT, VALUE],
)
df[LABEL] = df[ID]

# Plot
# Hierarchy: children per node, depth per node
children = {node: list(rows[ID]) for node, rows in df.groupby(PARENT, sort=False)}
root = df.loc[df[PARENT].isna(), ID].iloc[0]
# Rows whose parent has no row of its own hang off the root
for parent in [p for p in children if p not in set(df[ID])]:
    children.setdefault(root, []).extend(children.pop(parent))
leaf_value = df.set_index(ID)[VALUE]
labels = df.set_index(ID)[LABEL]
gap = 0.12 * np.sqrt(leaf_value.dropna()).median()


def enclosing(centers, radii):
    """Approximate smallest circle around circles (Badoiu-Clarkson iteration)."""
    c = (centers * radii[:, None] ** 2).sum(axis=0) / (radii**2).sum()
    for step in range(1, 400):
        far = np.argmax(np.hypot(*(centers - c).T) + radii)
        c = c + (centers[far] - c) / (step + 1)
    return c, (np.hypot(*(centers - c).T) + radii).max()


def pack(radii):
    """Greedy tangent packing; returns centers relative to the enclosing center and its radius."""
    order = np.argsort(-radii)
    placed = []
    for k in order:
        r = radii[k]
        if not placed:
            placed.append((k, np.zeros(2)))
            continue
        cands = []
        if len(placed) == 1:
            k0, p0 = placed[0]
            cands.append(p0 + np.array([radii[k0] + r, 0.0]))
        for a in range(len(placed)):
            for b in range(a + 1, len(placed)):
                (ka, pa), (kb, pb) = placed[a], placed[b]
                ra, rb = radii[ka] + r, radii[kb] + r
                d = np.hypot(*(pb - pa))
                if d > ra + rb or d < abs(ra - rb) or d == 0:
                    continue
                x = (ra**2 - rb**2 + d**2) / (2 * d)
                h = np.sqrt(max(ra**2 - x**2, 0.0))
                u = (pb - pa) / d
                mid = pa + u * x
                for sign in (1, -1):
                    cands.append(mid + sign * h * np.array([-u[1], u[0]]))
        centroid = np.mean([p for _, p in placed], axis=0)
        best, best_score = None, np.inf
        for p in cands:
            if all(np.hypot(*(p - q)) >= radii[kq] + r - 1e-9 for kq, q in placed):
                score = np.hypot(*(p - centroid)) + r
                if score < best_score:
                    best, best_score = p, score
        placed.append((k, best))
    centers = np.zeros((len(radii), 2))
    for k, p in placed:
        centers[k] = p
    c, big = enclosing(centers, radii)
    return centers - c, big


# Layout: leaf radius = sqrt(value) so area is proportional to value; parents wrap their packed children
radius = {leaf: np.sqrt(v) for leaf, v in leaf_value.dropna().items()}
offset = {}  # position relative to the parent's center


def layout(node):
    kids = children.get(node)
    if not kids:
        return
    for kid in kids:
        layout(kid)
    kids = [kid for kid in kids if kid in radius]
    if not kids:
        return
    children[node] = kids
    padded = np.array([radius[kid] + gap / 2 for kid in kids])
    centers, big = pack(padded)
    radius[node] = big + gap / 2
    for kid, c in zip(kids, centers, strict=True):
        offset[kid] = c


layout(root)
center = {root: np.zeros(2)}
depth = {root: 0}
queue = [root]
for node in queue:
    for kid in children.get(node, []) if node in radius else []:
        if kid in offset:
            center[kid] = center[node] + offset[kid]
            depth[kid] = depth[node] + 1
            queue.append(kid)

fig, ax = plt.subplots(figsize=(6, 6), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)
level_colors = {d: IMPRINT_PALETTE[d % len(IMPRINT_PALETTE)] for d in set(depth.values())}
fill_alpha = {0: 0.30, 1: 0.45}

for node in queue:
    d = depth[node]
    is_leaf = node not in children
    ax.add_patch(
        patches.Circle(
            center[node],
            radius[node],
            facecolor=level_colors[d],
            edgecolor=INK_SOFT if not is_leaf else PAGE_BG,
            linewidth=0.8,
            alpha=0.9 if is_leaf else fill_alpha.get(d, 0.5),
        )
    )

label_size = 0.9 * 72 * 6 * 0.9 / (2 * radius[root] * 1.1)  # points per data unit
for node in queue:
    x, y = center[node]
    r = radius[node]
    if node not in children:
        text = str(labels[node])
        if r * label_size * 2 >= len(text) * 3.2:
            ax.text(x, y, text, ha="center", va="center", fontsize=min(9, r * label_size * 0.9), color=INK_SOFT)
            ax.texts[-1].set_color("#FAF8F1" if THEME == "light" else INK)
    else:
        # Parent labels sit on the top edge of their circle, clear of the nested circles
        ax.text(
            x,
            y + r,
            str(labels[node]),
            ha="center",
            va="center",
            fontsize=10 if depth[node] == 0 else 8.5,
            fontweight="bold",
            color=INK,
            bbox={"facecolor": ELEVATED_BG, "edgecolor": INK_SOFT, "linewidth": 0.6, "boxstyle": "round,pad=0.25"},
            zorder=5,
        )

lim = radius[root] * 1.12
ax.set_xlim(-lim, lim)
ax.set_ylim(-lim, lim)
ax.set_aspect("equal")
ax.axis("off")

title = "circlepacking-basic · python · matplotlib · anyplot.ai"
ax.set_title(title, fontsize=12, fontweight="medium", color=INK, pad=6)

level_names = {0: str(labels[root]), 1: "Departments", 2: "Teams (area = headcount)"}
level_alpha = {0: 0.6, 1: 0.7}
legend_elements = [
    patches.Patch(
        facecolor=level_colors[d],
        edgecolor=INK_SOFT,
        alpha=level_alpha.get(d, 0.9),
        label=level_names.get(d, f"Level {d}"),
    )
    for d in sorted(level_colors)
]
leg = ax.legend(handles=legend_elements, loc="lower right", fontsize=8, framealpha=0.95)
leg.get_frame().set_facecolor(ELEVATED_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)

fig.subplots_adjust(left=0.02, right=0.98, top=0.94, bottom=0.02)
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)

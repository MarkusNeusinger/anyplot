# anyplot.ai
# network-hierarchical: Hierarchical Network Graph with Tree Layout
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 84/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Statistics

# --- Theme tokens ------------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint palette — one hue per organizational level (level 0 = root)
const IMPRINT_PALETTE = [
    colorant"#009E73",  # level 0 — CEO (brand green)
    colorant"#C475FD",  # level 1 — VPs (lavender)
    colorant"#4467A3",  # level 2 — Directors (blue)
    colorant"#BD8233",  # level 3 — Managers / ICs (ochre)
]

# --- Data: a 4-level organizational chart, 24 employees ----------------------
nodes = [
    (id = "ceo", label = "CEO", level = 0, parent = ""),
    (id = "vp_eng", label = "VP Engineering", level = 1, parent = "ceo"),
    (id = "vp_sales", label = "VP Sales", level = 1, parent = "ceo"),
    (id = "vp_ops", label = "VP Operations", level = 1, parent = "ceo"),
    (id = "dir_fe", label = "Dir. Frontend", level = 2, parent = "vp_eng"),
    (id = "dir_be", label = "Dir. Backend", level = 2, parent = "vp_eng"),
    (id = "dir_qa", label = "Dir. QA", level = 2, parent = "vp_eng"),
    (id = "dir_ent", label = "Dir. Enterprise", level = 2, parent = "vp_sales"),
    (id = "dir_smb", label = "Dir. SMB", level = 2, parent = "vp_sales"),
    (id = "dir_hr", label = "Dir. HR", level = 2, parent = "vp_ops"),
    (id = "dir_fin", label = "Dir. Finance", level = 2, parent = "vp_ops"),
    (id = "dir_log", label = "Dir. Logistics", level = 2, parent = "vp_ops"),
    (id = "mgr_fe_a", label = "Eng Mgr A", level = 3, parent = "dir_fe"),
    (id = "mgr_fe_b", label = "Eng Mgr B", level = 3, parent = "dir_fe"),
    (id = "mgr_be_a", label = "Eng Mgr C", level = 3, parent = "dir_be"),
    (id = "mgr_be_b", label = "Eng Mgr D", level = 3, parent = "dir_be"),
    (id = "lead_qa", label = "QA Lead", level = 3, parent = "dir_qa"),
    (id = "mgr_sales_a", label = "Sales Mgr A", level = 3, parent = "dir_ent"),
    (id = "mgr_sales_b", label = "Sales Mgr B", level = 3, parent = "dir_ent"),
    (id = "mgr_sales_c", label = "Sales Mgr C", level = 3, parent = "dir_smb"),
    (id = "mgr_hr", label = "HR Manager", level = 3, parent = "dir_hr"),
    (id = "mgr_fin", label = "Finance Mgr", level = 3, parent = "dir_fin"),
    (id = "analyst_fin", label = "Finance Analyst", level = 3, parent = "dir_fin"),
    (id = "mgr_log", label = "Logistics Mgr", level = 3, parent = "dir_log"),
]

children = Dict(n.id => String[] for n in nodes)
for n in nodes
    n.parent != "" && push!(children[n.parent], n.id)
end

# --- Tree layout: leaves get sequential x, parents average their children ----
const LEAF_SPACING  = 1.0
const LEVEL_SPACING = 1.6

x_pos = Dict{String,Float64}()
leaf_nodes = [n for n in nodes if n.level == 3]
for (i, n) in enumerate(leaf_nodes)
    x_pos[n.id] = i * LEAF_SPACING
end
for lvl in (2, 1, 0)
    for n in nodes
        n.level == lvl && (x_pos[n.id] = mean(x_pos[k] for k in children[n.id]))
    end
end
y_pos = Dict(n.id => -n.level * LEVEL_SPACING for n in nodes)

const BOX_W = 0.87 * LEAF_SPACING
const BOX_H = 0.42 * LEVEL_SPACING

# Level-coded emphasis: thicker borders at senior levels reinforce the
# hierarchy beyond color alone (CEO thickest, Manager/IC thinnest)
const STROKE_WIDTHS = [3.2, 2.8, 2.4, 2.0]

# --- Figure --------------------------------------------------------------
title_str = "network-hierarchical · julia · makie · anyplot.ai"

fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title           = title_str,
    titlesize       = 20,
    titlecolor      = INK,
    backgroundcolor = PAGE_BG,
)
hidedecorations!(ax)
hidespines!(ax)

# Edges — straight lines from parent box bottom to child box top, drawn first.
# Thinner + more transparent where a parent has many children, so dense
# fan-outs (e.g. a VP with 3 directors) read less cluttered than single-child
# edges.
for n in nodes
    n.parent == "" && continue
    px, py = x_pos[n.parent], y_pos[n.parent]
    cx, cy = x_pos[n.id], y_pos[n.id]
    nsiblings  = length(children[n.parent])
    edge_alpha = clamp(0.6 - 0.04 * (nsiblings - 1), 0.35, 0.6)
    edge_width = clamp(1.8 - 0.15 * (nsiblings - 1), 1.1, 1.8)
    lines!(
        ax, [px, cx], [py - BOX_H / 2, cy + BOX_H / 2];
        color = (INK_SOFT, edge_alpha), linewidth = edge_width,
    )
end

# Nodes — box per employee, border colored by organizational level, with
# stroke width tapering from CEO (thickest) to Manager/IC (thinnest)
for n in nodes
    x, y = x_pos[n.id], y_pos[n.id]
    poly!(
        ax, Rect2f(x - BOX_W / 2, y - BOX_H / 2, BOX_W, BOX_H);
        color       = ELEVATED_BG,
        strokecolor = IMPRINT_PALETTE[n.level + 1],
        strokewidth = STROKE_WIDTHS[n.level + 1],
    )
    text!(
        ax, x, y; text = n.label,
        color = INK, fontsize = 12,
        align = (:center, :center),
    )
end

xs, ys = collect(values(x_pos)), collect(values(y_pos))
xlims!(ax, minimum(xs) - BOX_W / 2 - 0.6, maximum(xs) + BOX_W / 2 + 0.6)
ylims!(ax, minimum(ys) - BOX_H / 2 - 0.2, maximum(ys) + BOX_H / 2 + 0.35)

# Legend — organizational level key
level_labels = ["CEO", "VP", "Director", "Manager / IC"]
legend_elems = [
    PolyElement(color = ELEVATED_BG, strokecolor = IMPRINT_PALETTE[i], strokewidth = STROKE_WIDTHS[i])
    for i in 1:4
]
Legend(
    fig[1, 2], legend_elems, level_labels, "Level";
    framevisible = false,
    labelcolor   = INK,
    titlecolor   = INK,
    labelsize    = 13,
    titlesize    = 14,
    patchsize    = (18, 18),
)
colsize!(fig.layout, 1, Relative(0.87))

# --- Save ------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

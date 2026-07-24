# anyplot.ai
# network-basic: Basic Network Graph
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-07-24

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint categorical palette (first 4 positions — module layers)
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — Core
    colorant"#C475FD",  # 2 — Data
    colorant"#4467A3",  # 3 — API
    colorant"#BD8233",  # 4 — UI
]
const LAYER_NAMES = ["Core", "Data", "API", "UI"]

# --- Data: software module dependency graph ---------------------------------
module_names = [
    "Auth", "Config", "Logger", "Cache", "EventBus",
    "UserRepo", "OrderRepo", "PaymentRepo", "Schema", "Migrations",
    "UserAPI", "OrderAPI", "PaymentAPI", "SearchAPI", "NotifyAPI", "Gateway",
    "Dashboard", "Checkout", "Profile", "Admin", "Reports", "MobileApp",
]
layer = [
    1, 1, 1, 1, 1,
    2, 2, 2, 2, 2,
    3, 3, 3, 3, 3, 3,
    4, 4, 4, 4, 4, 4,
]
n = length(module_names)

edges = [
    # Core internals
    (1, 2), (1, 3), (2, 4), (1, 5),
    # Data depends on Core
    (6, 1), (6, 4), (7, 1), (8, 1), (9, 4), (10, 9),
    # API depends on Data + Core
    (11, 6), (11, 1), (12, 7), (13, 8), (14, 6), (14, 7), (15, 5),
    (16, 11), (16, 12), (16, 13),
    # UI depends on API
    (17, 16), (17, 11), (18, 12), (18, 13), (19, 11),
    (20, 16), (21, 14), (21, 12), (22, 16),
]

degrees = zeros(Int, n)
for (a, b) in edges
    degrees[a] += 1
    degrees[b] += 1
end

# --- Force-directed layout (Fruchterman-Reingold, hand-rolled — no
#     NetworkLayout.jl, which is not installed in the CI runtime) -----------
angles = range(0, 2π; length = n + 1)[1:n] .+ randn(n) .* 0.15
radius = 0.4
positions = hcat(0.5 .+ radius .* cos.(angles), 0.5 .+ radius .* sin.(angles))

k = sqrt(1.0 / n)
iterations = 200
for iter in 1:iterations
    disp = zeros(n, 2)
    for i in 1:n, j in 1:n
        i == j && continue
        dx, dy = positions[i, 1] - positions[j, 1], positions[i, 2] - positions[j, 2]
        dist = max(hypot(dx, dy), 0.01)
        force = k^2 / dist
        disp[i, 1] += (dx / dist) * force
        disp[i, 2] += (dy / dist) * force
    end
    for (a, b) in edges
        dx, dy = positions[a, 1] - positions[b, 1], positions[a, 2] - positions[b, 2]
        dist = max(hypot(dx, dy), 0.01)
        force = dist^2 / k
        disp[a, 1] -= (dx / dist) * force
        disp[a, 2] -= (dy / dist) * force
        disp[b, 1] += (dx / dist) * force
        disp[b, 2] += (dy / dist) * force
    end
    temperature = 0.1 * (1 - iter / iterations)
    for i in 1:n
        dn = hypot(disp[i, 1], disp[i, 2])
        if dn > 0
            step = min(dn, temperature) / dn
            positions[i, 1] += disp[i, 1] * step
            positions[i, 2] += disp[i, 2] * step
        end
    end
end

pos_min = vec(minimum(positions; dims = 1))
pos_max = vec(maximum(positions; dims = 1))
positions = (positions .- pos_min') ./ (pos_max' .- pos_min') .* 0.86 .+ 0.07

# --- Plot ---------------------------------------------------------------
title_text = "Software Module Dependencies · network-basic · julia · makie · anyplot.ai"

fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title            = title_text,
    titlesize        = 18,
    titlecolor       = INK,
    backgroundcolor  = PAGE_BG,
)
hidedecorations!(ax)
hidespines!(ax)
xlims!(ax, -0.05, 1.05)
ylims!(ax, -0.05, 1.05)

edge_points = Vector{Point2f}(undef, 2 * length(edges))
for (idx, (a, b)) in enumerate(edges)
    edge_points[2idx - 1] = Point2f(positions[a, 1], positions[a, 2])
    edge_points[2idx]     = Point2f(positions[b, 1], positions[b, 2])
end
linesegments!(
    ax, edge_points;
    color     = RGBAf(INK_SOFT.r, INK_SOFT.g, INK_SOFT.b, 0.45),
    linewidth = 1.8,
)

node_colors = [IMPRINT_PALETTE[layer[i]] for i in 1:n]
node_sizes = [26.0 + degrees[i] * 5.0 for i in 1:n]
scatter!(
    ax, positions[:, 1], positions[:, 2];
    color       = node_colors,
    markersize  = node_sizes,
    strokecolor = PAGE_BG,
    strokewidth = 2.5,
)
label_offsets = [(0.0f0, -(node_sizes[i] / 2 + 9)) for i in 1:n]
text!(
    ax, positions[:, 1], positions[:, 2];
    text      = module_names,
    align     = (:center, :top),
    fontsize  = 11,
    color     = INK,
    offset    = label_offsets,
)

for (i, name) in enumerate(LAYER_NAMES)
    scatter!(ax, [NaN], [NaN]; color = IMPRINT_PALETTE[i], markersize = 20, label = name)
end
axislegend(ax, "Layer"; position = :lt, backgroundcolor = ELEVATED_BG, labelcolor = INK_SOFT, titlecolor = INK)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

# anyplot.ai
# upset-basic: UpSet Plot for Multi-Set Intersection Analysis
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-09-09

using CairoMakie
using Colors
using ColorSchemes
using Random

Random.seed!(42)

# --- Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome") ---
const THEME      = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG    = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK        = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT   = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED  = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"
const GRID_RGBA  = RGBAf(INK.r, INK.g, INK.b, 0.15)

# Imprint palette (see prompts/default-style-guide.md "Categorical Palette")
const BRAND      = colorant"#009E73"  # position 1 — ALWAYS first series
const IMPRINT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])  # sequential — degree encoding

# --- Data: differential-expression gene sets across sequencing experiments ---
set_names = ["RNA-seq", "ChIP-seq", "ATAC-seq", "Proteomics", "Methylation"]
n_sets = length(set_names)
n_genes = 3000
membership_probs = [0.34, 0.27, 0.21, 0.16, 0.11]

membership = falses(n_genes, n_sets)
for j in 1:n_sets, i in 1:n_genes
    membership[i, j] = rand() < membership_probs[j]
end
keep = [any(view(membership, i, :)) for i in 1:n_genes]
membership = membership[keep, :]
n_elements = size(membership, 1)

# Sort sets by total size (largest drawn at the top of the matrix)
set_sizes = vec(sum(membership, dims = 1))
set_order = sortperm(set_sizes, rev = true)
set_names_sorted = set_names[set_order]
set_sizes_sorted = set_sizes[set_order]
membership = membership[:, set_order]
set_y = [n_sets - k + 1 for k in 1:n_sets]  # top row = largest set

# Count occurrences of each membership pattern, keep the top 15 by size
combo_counts = Dict{Vector{Bool}, Int}()
for i in 1:n_elements
    key = membership[i, :]
    combo_counts[key] = get(combo_counts, key, 0) + 1
end
combos = collect(keys(combo_counts))
counts = [combo_counts[c] for c in combos]
combo_order = sortperm(counts, rev = true)
n_show = min(15, length(combos))
top_combos = combos[combo_order[1:n_show]]
top_counts = counts[combo_order[1:n_show]]
degrees = [sum(c) for c in top_combos]
deg_min, deg_max = extrema(degrees)
deg_span = max(deg_max - deg_min, 1)
bar_colors = [get(IMPRINT_SEQ, (d - deg_min) / deg_span) for d in degrees]

# --- Figure ---------------------------------------------------------------
fig = Figure(
    resolution = (1600, 900),
    fontsize = 14,
    backgroundcolor = PAGE_BG,
)

Label(
    fig[0, 1:3],
    "upset-basic · julia · makie · anyplot.ai",
    fontsize = 22,
    font = :bold,
    color = INK,
)

ax_bars = Axis(
    fig[1, 2];
    ylabel = "Intersection size",
    ylabelcolor = INK,
    yticklabelcolor = INK_SOFT,
    xticksvisible = false,
    xticklabelsvisible = false,
    backgroundcolor = PAGE_BG,
    topspinevisible = false,
    rightspinevisible = false,
    bottomspinevisible = false,
    leftspinecolor = INK_SOFT,
    ygridcolor = GRID_RGBA,
    ygridvisible = true,
    xgridvisible = false,
)

ax_setbars = Axis(
    fig[2, 1];
    xlabel = "Set size",
    xlabelcolor = INK,
    xticklabelcolor = INK_SOFT,
    yticksvisible = false,
    yticklabelsvisible = false,
    xreversed = true,
    backgroundcolor = PAGE_BG,
    topspinevisible = false,
    rightspinevisible = false,
    leftspinevisible = false,
    bottomspinecolor = INK_SOFT,
    xgridcolor = GRID_RGBA,
    xgridvisible = true,
    ygridvisible = false,
)

ax_matrix = Axis(
    fig[2, 2];
    yticks = (1:n_sets, reverse(set_names_sorted)),
    yticklabelcolor = INK_SOFT,
    xticksvisible = false,
    xticklabelsvisible = false,
    backgroundcolor = PAGE_BG,
    topspinevisible = false,
    rightspinevisible = false,
    leftspinevisible = false,
    bottomspinevisible = false,
    ygridvisible = false,
    xgridvisible = false,
)

linkxaxes!(ax_bars, ax_matrix)
linkyaxes!(ax_setbars, ax_matrix)
xlims!(ax_matrix, 0.3, n_show + 0.7)
ylims!(ax_matrix, 0.3, n_sets + 0.7)

# Intersection size bars — colored by degree (how many sets overlap)
barplot!(ax_bars, 1:n_show, top_counts; color = bar_colors, width = 0.65)

# Set size bars — single series, brand color
barplot!(ax_setbars, set_y, set_sizes_sorted; direction = :x, color = BRAND, width = 0.65)

# Alternating row bands for readability
for k in 1:n_sets
    if isodd(k)
        hspan!(ax_matrix, set_y[k] - 0.5, set_y[k] + 0.5; color = (INK, 0.04))
    end
end

# Dot matrix — connecting lines first, then non-member and member dots
for j in 1:n_show
    combo = top_combos[j]
    member_rows = [set_y[k] for k in 1:n_sets if combo[k]]
    if length(member_rows) >= 2
        lines!(ax_matrix, fill(j, 2), [minimum(member_rows), maximum(member_rows)];
               color = INK_SOFT, linewidth = 3)
    end
end

member_x = Float64[]; member_yv = Float64[]
absent_x = Float64[]; absent_yv = Float64[]
for j in 1:n_show, k in 1:n_sets
    combo = top_combos[j]
    if combo[k]
        push!(member_x, j); push!(member_yv, set_y[k])
    else
        push!(absent_x, j); push!(absent_yv, set_y[k])
    end
end

scatter!(ax_matrix, absent_x, absent_yv; color = (INK_MUTED, 0.3), markersize = 16)
scatter!(ax_matrix, member_x, member_yv; color = INK, markersize = 24)

Colorbar(
    fig[1, 3];
    limits = (deg_min, deg_max),
    colormap = IMPRINT_SEQ,
    label = "Sets in intersection",
    labelcolor = INK,
    ticklabelcolor = INK_SOFT,
    ticks = deg_min:deg_max,
    width = 18,
)

colsize!(fig.layout, 1, Relative(0.14))
colsize!(fig.layout, 2, Relative(0.80))
colsize!(fig.layout, 3, Relative(0.06))
rowsize!(fig.layout, 1, Relative(0.32))
rowsize!(fig.layout, 2, Relative(0.68))

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

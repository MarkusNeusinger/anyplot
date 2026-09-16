# anyplot.ai
# waffle-basic: Basic Waffle Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 85/100 | Created: 2026-09-09

using CairoMakie
using Colors

# --- Theme tokens ------------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green, ALWAYS first series
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red
]

# --- Data: household budget allocation, 100 squares = 100% -------------------
categories = ["Housing", "Food", "Transportation", "Savings", "Entertainment"]
percentages = [32, 22, 18, 16, 12]
focal_idx = argmax(percentages)

grid_size = 10
cell_categories = Vector{Int}(undef, grid_size^2)
cursor = 1
for (cat_idx, count) in enumerate(percentages)
    cell_categories[cursor:(cursor + count - 1)] .= cat_idx
    global cursor += count
end

square_gap = 0.12
square_side = 1.0 - square_gap
squares = Vector{Rect2{Float64}}(undef, grid_size^2)
cell_colors = Vector{eltype(IMPRINT_PALETTE)}(undef, grid_size^2)
for i in 1:(grid_size^2)
    row = (i - 1) ÷ grid_size          # 0 = top row
    col = (i - 1) % grid_size
    x = col + square_gap / 2
    y = (grid_size - 1 - row) + square_gap / 2
    squares[i] = Rect2(Float64(x), Float64(y), square_side, square_side)
    cell_colors[i] = IMPRINT_PALETTE[cell_categories[i]]
end

focal_mask    = cell_categories .== focal_idx
squares_rest  = squares[.!focal_mask]
colors_rest   = cell_colors[.!focal_mask]
squares_focal = squares[focal_mask]
colors_focal  = cell_colors[focal_mask]

# --- Plot ----------------------------------------------------------------
title_text    = "waffle-basic · julia · makie · anyplot.ai"
subtitle_text = "$(categories[focal_idx]) leads the budget at $(percentages[focal_idx])%"

canvas_side     = 1200
title_height    = 92
subtitle_height = 40
legend_height   = 70
row_gap         = 16
square_side_px  = canvas_side - title_height - subtitle_height - legend_height - 3 * row_gap

fig = Figure(
    size            = (canvas_side, canvas_side),
    fontsize        = 16,
    backgroundcolor = PAGE_BG,
)

Label(
    fig[1, 1], title_text;
    fontsize = 38, color = INK, font = :bold, halign = :center,
)

Label(
    fig[2, 1], subtitle_text;
    fontsize = 18, color = INK_SOFT, halign = :center,
)

ax = Axis(
    fig[3, 1];
    aspect          = DataAspect(),
    backgroundcolor = PAGE_BG,
)
hidespines!(ax)
hidedecorations!(ax)

# Focal category (largest share) gets an ink-colored outline to anchor the
# eye and reinforce the storytelling callout above; every other square keeps
# the neutral background-colored gap stroke.
poly!(ax, squares_rest; color = colors_rest, strokewidth = 3, strokecolor = PAGE_BG)
poly!(ax, squares_focal; color = colors_focal, strokewidth = 5, strokecolor = INK)
xlims!(ax, 0, grid_size)
ylims!(ax, 0, grid_size)

legend_labels = ["$(categories[i]) ($(percentages[i])%)" for i in eachindex(categories)]
legend_elements = [PolyElement(color = IMPRINT_PALETTE[i], strokewidth = 0) for i in eachindex(categories)]
Legend(
    fig[4, 1], legend_elements, legend_labels;
    orientation     = :horizontal,
    framevisible    = false,
    backgroundcolor = :transparent,
    labelcolor      = INK,
    labelsize       = 18,
    patchsize       = (22, 22),
    colgap          = 18,
    halign          = :center,
)

rowsize!(fig.layout, 1, Fixed(title_height))
rowsize!(fig.layout, 2, Fixed(subtitle_height))
rowsize!(fig.layout, 3, Fixed(square_side_px))
rowsize!(fig.layout, 4, Fixed(legend_height))
colsize!(fig.layout, 1, Fixed(square_side_px))
rowgap!(fig.layout, row_gap)

# --- Save ------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

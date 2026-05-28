# anyplot.ai
# pie-basic: Basic Pie Chart
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-05-28

using CairoMakie
using Colors
using Printf

const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

const ANYPLOT_PALETTE = [
    colorant"#009E73",
    colorant"#C475FD",
    colorant"#4467A3",
    colorant"#BD8233",
    colorant"#AE3030",
]

# Data — primary programming language (developer survey)
const categories = ["Python", "JavaScript", "Java", "C / C++", "TypeScript"]
const values     = [36.0, 29.5, 17.0, 11.5, 6.0]
const total      = sum(values)
const pct        = values ./ total .* 100

# Wedge angles: start at top (π/2), sweep clockwise
const fracs   = values ./ total
const cum     = cumsum(vcat(0.0, fracs))
const θ_start = [π / 2 - cum[i]     * 2π for i in 1:length(values)]
const θ_end   = [π / 2 - cum[i + 1] * 2π for i in 1:length(values)]

const explode_idx = argmax(values)  # Python — largest slice
const explode_r   = 0.07

const title_str = "Primary Programming Language · pie-basic · julia · makie · anyplot.ai"
const title_fs  = round(Int, 20 * min(1.0, 67.0 / length(title_str)))

fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = title_fs,
    titlecolor         = INK,
    aspect             = DataAspect(),
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinevisible   = false,
    bottomspinevisible = false,
    xgridvisible       = false,
    ygridvisible       = false,
    xticksvisible      = false,
    yticksvisible      = false,
    xticklabelsvisible = false,
    yticklabelsvisible = false,
)

for i in 1:length(values)
    θ_mid = (θ_start[i] + θ_end[i]) / 2
    dx = i == explode_idx ? explode_r * cos(θ_mid) : 0.0
    dy = i == explode_idx ? explode_r * sin(θ_mid) : 0.0

    θs = LinRange(θ_start[i], θ_end[i], 150)
    xs = vcat([dx], dx .+ cos.(θs))
    ys = vcat([dy], dy .+ sin.(θs))
    poly!(ax, Point2f.(xs, ys); color = ANYPLOT_PALETTE[i], strokecolor = PAGE_BG, strokewidth = 3)

    lx = dx + 0.62 * cos(θ_mid)
    ly = dy + 0.62 * sin(θ_mid)
    text!(ax, lx, ly;
          text     = @sprintf("%.1f%%", pct[i]),
          align    = (:center, :center),
          fontsize = 14,
          color    = colorant"#FAF8F1",
    )
end

legend_entries = [PolyElement(color = ANYPLOT_PALETTE[i], strokecolor = :transparent) for i in 1:length(categories)]
legend_labels  = [@sprintf("%s  %.1f%%", categories[i], pct[i]) for i in 1:length(categories)]

Legend(
    fig[1, 2],
    legend_entries,
    legend_labels;
    framevisible    = false,
    backgroundcolor = ELEVATED_BG,
    labelcolor      = INK,
    labelsize       = 14,
    rowgap          = 12,
    halign          = :left,
    valign          = :center,
    padding         = (12, 12, 12, 12),
)

colsize!(fig.layout, 1, Relative(0.68))

save("plot-$(THEME).png", fig; px_per_unit = 2)

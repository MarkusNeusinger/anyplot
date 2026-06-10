# anyplot.ai
# recurrence-basic: Recurrence Plot for Nonlinear Time Series
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-06-10

using CairoMakie
using Colors
using ColorSchemes
using Random

Random.seed!(42)

# Theme tokens
const THEME = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# Data — Lorenz attractor x-component via Euler integration
dt = 0.01
sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
n_steps = 3000
lx, ly, lz = zeros(n_steps), zeros(n_steps), zeros(n_steps)
lx[1], ly[1], lz[1] = 1.0, 0.0, 0.0
for i in 2:n_steps
    lx[i] = lx[i-1] + dt * sigma * (ly[i-1] - lx[i-1])
    ly[i] = ly[i-1] + dt * (lx[i-1] * (rho - lz[i-1]) - ly[i-1])
    lz[i] = lz[i-1] + dt * (lx[i-1] * ly[i-1] - beta * lz[i-1])
end

# Extract 500 steps after transient; use all three state variables for embedding
ts_x = lx[1501:2000]
ts_y = ly[1501:2000]
ts_z = lz[1501:2000]
n = length(ts_x)

# Pairwise Euclidean distance in full 3D Lorenz state space
dist = zeros(Float32, n, n)
for i in 1:n
    for j in 1:n
        dist[i, j] = sqrt(
            (ts_x[i] - ts_x[j])^2 +
            (ts_y[i] - ts_y[j])^2 +
            (ts_z[i] - ts_z[j])^2
        )
    end
end

# Threshold at the 10th percentile → ~10% recurrence rate
sorted_dist = sort(vec(dist))
epsilon = sorted_dist[round(Int, 0.10 * length(sorted_dist))]
recurrence = Float32.(dist .<= epsilon)

# Colormap: non-recurrent → background, recurrent → Imprint brand green
cmap = cgrad([PAGE_BG, IMPRINT_PALETTE[1]])

# Plot — square canvas for symmetric recurrence matrix
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "recurrence-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Time Index",
    ylabel             = "Time Index",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridvisible       = false,
    aspect             = DataAspect(),
)

heatmap!(ax, 1:n, 1:n, recurrence; colormap = cmap, colorrange = (0.0f0, 1.0f0))

# Annotation: guide the viewer to the key structural insight
text!(ax, 10.0, 490.0;
    text = "Diagonal lines\n= determinism",
    color = INK_SOFT, fontsize = 11,
    align = (:left, :top))
arrows!(ax, [90.0], [450.0], [90.0], [-90.0];
    color = INK_SOFT, linewidth = 1.0, arrowsize = 10.0)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)

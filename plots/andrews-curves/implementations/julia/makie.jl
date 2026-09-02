# anyplot.ai
# andrews-curves: Andrews Curves for Multivariate Data
# Library: Makie.jl 0.21.9 | Julia 1.11.9
# Quality: pending | Created: 2026-09-02

using CairoMakie
using RDatasets
using DataFrames
using Statistics
using Random

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------
THEME = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
INK = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — 4-cylinder
    colorant"#C475FD",  # 2 — 6-cylinder
    colorant"#4467A3",  # 3 — 8-cylinder
]

# --- Data -----------------------------------------------------------------
# Motor Trend car specs: five performance/weight measurements per car,
# grouped by cylinder count to reveal how engine class separates in shape.
cars = RDatasets.dataset("datasets", "mtcars")
features = [:MPG, :Disp, :HP, :WT, :QSec]
X = Matrix{Float64}(cars[:, features])

# Normalize each variable to unit scale so no single measurement dominates
means = mean(X; dims = 1)
stds = std(X; dims = 1)
X_scaled = (X .- means) ./ stds

cylinder_groups = [4, 6, 8]
group_labels = ["4-cylinder", "6-cylinder", "8-cylinder"]
group_idx = [findfirst(==(c), cylinder_groups) for c in cars.Cyl]

# --- Andrews curve transform ------------------------------------------------
# f(t) = x1/sqrt(2) + x2*sin(t) + x3*cos(t) + x4*sin(2t) + x5*cos(2t) + ...
t = collect(range(-pi, pi; length = 200))
n_features = length(features)
basis = zeros(length(t), n_features)
basis[:, 1] .= 1 / sqrt(2)
for j in 2:n_features
    m = j - 1
    freq = ceil(Int, m / 2)
    basis[:, j] = isodd(m) ? sin.(freq .* t) : cos.(freq .* t)
end
curves = X_scaled * basis'  # (n_cars, length(t))

# --- Plot -------------------------------------------------------------------
fig = Figure(size = (1600, 900), fontsize = 14, backgroundcolor = PAGE_BG)

ax = Axis(
    fig[1, 1];
    title = "andrews-curves · julia · makie · anyplot.ai",
    titlesize = 20,
    titlecolor = INK,
    xlabel = "t (radians)",
    ylabel = "f(t)",
    xlabelsize = 14,
    ylabelsize = 14,
    xlabelcolor = INK,
    ylabelcolor = INK,
    xticklabelsize = 12,
    yticklabelsize = 12,
    xticklabelcolor = INK_SOFT,
    yticklabelcolor = INK_SOFT,
    xtickcolor = INK_SOFT,
    ytickcolor = INK_SOFT,
    backgroundcolor = PAGE_BG,
    topspinevisible = false,
    rightspinevisible = false,
    leftspinecolor = INK_SOFT,
    bottomspinecolor = INK_SOFT,
    xgridcolor = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible = false,
    yminorgridvisible = false,
    xticks = (
        [-pi, -pi / 2, 0, pi / 2, pi],
        ["-π", "-π/2", "0", "π/2", "π"],
    ),
)

for i in 1:size(curves, 1)
    lines!(
        ax, t, curves[i, :];
        color = IMPRINT_PALETTE[group_idx[i]],
        linewidth = 3.0,
        alpha = 0.55,
    )
end

# Legend proxies — one representative line per cylinder class
for (idx, label) in enumerate(group_labels)
    lines!(ax, [NaN], [NaN]; color = IMPRINT_PALETTE[idx], linewidth = 4, label = label)
end
axislegend(
    ax, "Cylinders";
    position = :rt,
    backgroundcolor = ELEVATED_BG,
    framecolor = INK_SOFT,
    labelcolor = INK_SOFT,
    titlecolor = INK_SOFT,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

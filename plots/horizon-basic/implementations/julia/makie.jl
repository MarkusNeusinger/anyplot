# anyplot.ai
# horizon-basic: Horizon Chart
# Library: Makie.jl 0.21 | Julia 1.11
# Quality: pending | Created: 2026-08-18

using CairoMakie
using Colors
using ColorSchemes
using Random
using Statistics

Random.seed!(42)

# --- Theme tokens -------------------------------------------------------
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint diverging colormap (red -> midpoint -> blue). Horizon bands use its
# two endpoints: blue for positive deviation, red for negative deviation.
midpoint   = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
ANYPLOT_DIV = cgrad([colorant"#AE3030", midpoint, colorant"#4467A3"])
POS_COLOR  = get(ANYPLOT_DIV, 1.0)
NEG_COLOR  = get(ANYPLOT_DIV, 0.0)

# --- Data -----------------------------------------------------------------
# Simulated CPU-load deviation (percentage points from a 50% baseline) for a
# small fleet of servers, sampled hourly.
servers = ["web-1", "web-2", "web-3", "api-1", "api-2", "api-3",
           "db-1", "db-2", "cache-1", "cache-2", "queue-1", "lb-1"]
n_series = length(servers)
n_points = 200
hours = collect(0:(n_points - 1))

deviations = Matrix{Float64}(undef, n_points, n_series)
for j in 1:n_series
    scale = 5.0 + 4.0 * rand()
    walk = cumsum(randn(n_points) .* scale .* 0.18)
    walk .-= mean(walk)
    deviations[:, j] = clamp.(walk, -45.0, 45.0)
end

n_bands   = 3
max_abs   = maximum(abs.(deviations))
band_step = max_abs / n_bands
band_alphas = [0.35, 0.65, 1.0]

row_pitch = 1.0
row_h     = 0.78

# --- Plot -------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

Label(
    fig[1, 1],
    "Server CPU-load deviation from baseline · 3 intensity bands per polarity — darker = larger swing";
    fontsize = 13,
    color    = INK_SOFT,
    halign   = :left,
    tellwidth = false,
)

ax = Axis(
    fig[2, 1];
    title              = "horizon-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Time (hours)",
    xlabelcolor        = INK,
    xlabelsize         = 14,
    xticklabelcolor    = INK_SOFT,
    xticklabelsize     = 12,
    yticklabelcolor    = INK_SOFT,
    yticklabelsize     = 12,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinevisible   = false,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridvisible       = false,
    yticksvisible      = false,
    xtickcolor         = INK_SOFT,
)

for i in 1:n_series
    row_index = n_series - i + 1
    row_base  = (row_index - 1) * row_pitch
    v = deviations[:, i]

    for b in 1:n_bands
        lower = (b - 1) * band_step
        upper = b * band_step

        pos_frac = (clamp.(v, lower, upper) .- lower) ./ band_step
        y_top    = row_base .+ pos_frac .* row_h
        y_bottom = fill(row_base, n_points)
        band!(ax, hours, y_bottom, y_top; color = (POS_COLOR, band_alphas[b]))

        neg_frac  = (clamp.(.-v, lower, upper) .- lower) ./ band_step
        y_bottom2 = row_base .+ row_h .- neg_frac .* row_h
        y_top2    = fill(row_base + row_h, n_points)
        band!(ax, hours, y_bottom2, y_top2; color = (NEG_COLOR, band_alphas[b]))
    end
end

for i in 0:n_series
    y = i * row_pitch
    hlines!(ax, [y]; color = RGBAf(INK.r, INK.g, INK.b, 0.12), linewidth = 1)
end

row_centers = [(n_series - i) * row_pitch + row_h / 2 for i in 1:n_series]
ax.yticks = (row_centers, servers)

xlims!(ax, 0, n_points - 1)
ylims!(ax, 0, n_series * row_pitch)

rowsize!(fig.layout, 1, Auto(false, 0.05))

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

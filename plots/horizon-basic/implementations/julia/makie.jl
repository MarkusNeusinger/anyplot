# anyplot.ai
# horizon-basic: Horizon Chart
# Library: Makie.jl 0.21 | Julia 1.11
# Quality: pending | Created: 2026-08-20

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const POS_COLOR = IMPRINT_PALETTE[1]  # brand green — above-baseline deviation
const NEG_COLOR = IMPRINT_PALETTE[5]  # matte red — below-baseline deviation

# --- Data ---------------------------------------------------------------
# Ten server CPU-load deviations (percentage points) from a 24h rolling
# baseline, sampled every 10 minutes — a typical horizon-chart dashboard use.
const N_POINTS = 145
const N_BANDS  = 3

server_names = [
    "api-gateway", "auth-service", "web-frontend", "payments-svc",
    "search-index", "cache-redis", "db-primary", "db-replica",
    "worker-queue", "load-balancer",
]
n_series = length(server_names)

t = collect(range(0.0, 24.0; length = N_POINTS))

series_values = Vector{Vector{Float64}}(undef, n_series)
for i in 1:n_series
    walk = cumsum(randn(N_POINTS) .* 0.9)
    trend = range(walk[1], walk[end]; length = N_POINTS)
    series_values[i] = walk .- collect(trend)
end

band_height = maximum(maximum(abs.(v)) for v in series_values) / N_BANDS
band_alphas = range(0.35, 1.0; length = N_BANDS)

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

Label(
    fig[1, 1], "horizon-basic · julia · makie · anyplot.ai";
    fontsize = 22, color = INK, font = :bold, halign = :left,
)
Label(
    fig[2, 1],
    "CPU load deviation from 24h baseline, folded into $(N_BANDS) color bands per server — darker fill marks larger deviation";
    fontsize = 13, color = INK_SOFT, halign = :left,
)

zero_line = zeros(N_POINTS)
for (i, name) in enumerate(server_names)
    row = 2 + i
    ax = Axis(
        fig[row, 1];
        ylabel              = name,
        ylabelsize          = 13,
        ylabelcolor         = INK,
        ylabelrotation      = 0,
        backgroundcolor     = PAGE_BG,
        xgridvisible        = false,
        ygridvisible        = false,
        topspinevisible     = false,
        rightspinevisible   = false,
        leftspinevisible    = false,
        bottomspinevisible  = (i == n_series),
        bottomspinecolor    = INK_SOFT,
    )

    values = series_values[i]
    for b in 1:N_BANDS
        folded_pos = clamp.(values .- (b - 1) * band_height, 0.0, band_height)
        band!(ax, t, zero_line, folded_pos; color = (POS_COLOR, band_alphas[b]))

        folded_neg = clamp.(.-values .- (b - 1) * band_height, 0.0, band_height)
        band!(ax, t, zero_line, folded_neg; color = (NEG_COLOR, band_alphas[b]))
    end

    limits!(ax, (0.0, 24.0), (0.0, band_height))
    hideydecorations!(ax; label = false)

    if i == n_series
        ax.xlabel = "Time (hours)"
        ax.xlabelsize = 14
        ax.xlabelcolor = INK
        ax.xticklabelsize = 12
        ax.xticklabelcolor = INK_SOFT
        ax.xtickcolor = INK_SOFT
    else
        hidexdecorations!(ax)
    end
end

rowgap!(fig.layout, 4)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

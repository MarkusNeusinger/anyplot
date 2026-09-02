# anyplot.ai
# sn-curve-basic: S-N Curve (Wöhler Curve)
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 91/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Random
using Statistics

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

# --- Data: fatigue test coupons across 8 stress levels, 4 specimens each ---
stress_levels = [550.0, 500.0, 450.0, 400.0, 350.0, 300.0, 275.0, 260.0]
specimens_per_level = 4
sigma_f_prime = 900.0   # Basquin fatigue strength coefficient (MPa)
basquin_b = -0.09       # Basquin fatigue strength exponent

stress = Float64[]
cycles = Float64[]
for s in stress_levels
    mean_n = 0.5 * (s / sigma_f_prime)^(1 / basquin_b)
    for _ in 1:specimens_per_level
        n_i = mean_n * 10^(0.09 * randn())
        push!(stress, s)
        push!(cycles, n_i)
    end
end

# Basquin power-law fit (least squares in log-log space)
log_n = log10.(cycles)
log_s = log10.(stress)
slope = sum((log_n .- mean(log_n)) .* (log_s .- mean(log_s))) / sum((log_n .- mean(log_n)) .^ 2)
intercept = mean(log_s) - slope * mean(log_n)

fit_cycles = exp10.(range(log10(50.0), log10(1.5e6); length = 200))
fit_stress = exp10.(intercept .+ slope .* log10.(fit_cycles))

ultimate_strength = 600.0
yield_strength = 450.0
endurance_limit = 250.0

# Fatigue-region boundaries: low-cycle/high-cycle split at the conventional
# 10^3-cycle mark; high-cycle/infinite-life split at the cycle count where the
# Basquin fit crosses the endurance limit.
xlim_lo, xlim_hi = 50.0, 1.5e6
low_cycle_boundary = 1.0e3
infinite_life_boundary = clamp(
    exp10((log10(endurance_limit) - intercept) / slope),
    low_cycle_boundary * 1.5,
    xlim_hi * 0.98,
)

# --- Plot --------------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title             = "sn-curve-basic · julia · makie · anyplot.ai",
    titlesize         = 20,
    titlecolor        = INK,
    xlabel            = "Cycles to Failure, N",
    ylabel            = "Stress Amplitude (MPa)",
    xlabelsize        = 14,
    ylabelsize        = 14,
    xlabelcolor       = INK,
    ylabelcolor       = INK,
    xticklabelsize    = 12,
    yticklabelsize    = 12,
    xticklabelcolor   = INK_SOFT,
    yticklabelcolor   = INK_SOFT,
    xtickcolor        = INK_SOFT,
    ytickcolor        = INK_SOFT,
    xscale            = log10,
    yscale            = log10,
    yticks            = [200, 250, 300, 400, 500, 600, 700],
    ytickformat       = ys -> string.(round.(Int, ys)),
    backgroundcolor   = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

xlims!(ax, xlim_lo, xlim_hi)
ylims!(ax, 200.0, 700.0)

# Fatigue-region demarcation: subtle dotted separators + bottom-edge labels,
# called out per the spec's low-cycle / high-cycle / infinite-life regions.
vlines!(ax, [low_cycle_boundary, infinite_life_boundary];
        color = RGBAf(INK_SOFT.r, INK_SOFT.g, INK_SOFT.b, 0.4),
        linestyle = :dot, linewidth = 1.5)

region_label_y = 207.0
mid_low  = exp10(0.5 * (log10(xlim_lo) + log10(low_cycle_boundary)))
mid_high = exp10(0.5 * (log10(low_cycle_boundary) + log10(infinite_life_boundary)))
mid_inf  = exp10(0.5 * (log10(infinite_life_boundary) + log10(xlim_hi)))
text!(ax, mid_low, region_label_y; text = "Low-Cycle", fontsize = 11,
      color = INK_SOFT, align = (:center, :bottom))
text!(ax, mid_high, region_label_y; text = "High-Cycle", fontsize = 11,
      color = INK_SOFT, align = (:center, :bottom))
text!(ax, mid_inf, region_label_y; text = "Infinite Life", fontsize = 11,
      color = INK_SOFT, align = (:center, :bottom))

hlines!(ax, [ultimate_strength]; color = IMPRINT_PALETTE[2], linestyle = :dash,
        linewidth = 2.5, label = "Ultimate Strength")
hlines!(ax, [yield_strength]; color = IMPRINT_PALETTE[3], linestyle = :dash,
        linewidth = 2.5, label = "Yield Strength")
hlines!(ax, [endurance_limit]; color = IMPRINT_PALETTE[4], linestyle = :dash,
        linewidth = 2.5, label = "Endurance Limit")

lines!(ax, fit_cycles, fit_stress; color = INK_SOFT, linewidth = 3,
       label = "Basquin fit")

scatter!(ax, cycles, stress; color = IMPRINT_PALETTE[1], markersize = 16,
         strokewidth = 1.5, strokecolor = PAGE_BG, label = "Test specimens")

# Annotate where the Basquin fit crosses the endurance limit — the point
# beyond which infinite fatigue life is predicted.
n_label = infinite_life_boundary >= 1e6 ?
    string(round(infinite_life_boundary / 1e6; digits = 2), "M") :
    string(round(Int, infinite_life_boundary / 1e3), "k")
text!(ax, infinite_life_boundary * 0.97, endurance_limit * 1.1;
      text = "fit crosses endurance limit\nN ≈ $(n_label)",
      fontsize = 11, color = INK_SOFT, align = (:right, :bottom))

axislegend(ax; position = :rt, labelcolor = INK_SOFT, framevisible = false,
           labelsize = 12)

# --- Save --------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

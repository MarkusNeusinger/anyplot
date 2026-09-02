# anyplot.ai
# sn-curve-basic: S-N Curve (Wöhler Curve)
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-09-02

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
const ANYPLOT_AMBER = colorant"#DDCC77"

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

xlims!(ax, 50.0, 1.5e6)
ylims!(ax, 200.0, 700.0)

hlines!(ax, [ultimate_strength]; color = IMPRINT_PALETTE[3], linestyle = :dash,
        linewidth = 2.5, label = "Ultimate Strength")
hlines!(ax, [yield_strength]; color = IMPRINT_PALETTE[4], linestyle = :dash,
        linewidth = 2.5, label = "Yield Strength")
hlines!(ax, [endurance_limit]; color = ANYPLOT_AMBER, linestyle = :dash,
        linewidth = 2.5, label = "Endurance Limit")

lines!(ax, fit_cycles, fit_stress; color = INK_SOFT, linewidth = 3,
       label = "Basquin fit")

scatter!(ax, cycles, stress; color = IMPRINT_PALETTE[1], markersize = 16,
         strokewidth = 1.5, strokecolor = PAGE_BG, label = "Test specimens")

axislegend(ax; position = :rt, labelcolor = INK_SOFT, framevisible = false,
           labelsize = 12)

# --- Save --------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

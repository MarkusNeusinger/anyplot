# anyplot.ai
# bland-altman-basic: Bland-Altman Agreement Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-08-11

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
const BRAND = IMPRINT_PALETTE[1]
const BIAS_COLOR = INK  # neutral anchor — reference/baseline lines read as part of the chart's structural layer

# --- Data ---------------------------------------------------------------
# Paired systolic blood pressure readings (mmHg) from two sphygmomanometers
# on the same 90 subjects: a new automated cuff vs. a mercury reference device.
n_subjects = 90
true_pressure = rand(105:180, n_subjects)
reference_device = true_pressure .+ randn(n_subjects) .* 3.0
new_device = true_pressure .+ 4.0 .+ randn(n_subjects) .* 4.5

mean_pressure = (reference_device .+ new_device) ./ 2
pressure_diff = new_device .- reference_device

bias = mean(pressure_diff)
sd_diff = std(pressure_diff)
upper_loa = bias + 1.96 * sd_diff
lower_loa = bias - 1.96 * sd_diff

# --- Plot -----------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "bland-altman-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Mean of Two Devices (mmHg)",
    ylabel             = "Difference: New − Reference (mmHg)",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticks             = LinearTicks(7),
    yticks             = LinearTicks(7),
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
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

x_min = minimum(mean_pressure)
x_max = maximum(mean_pressure)

# Shaded limits-of-agreement band gives the acceptable-range region its own
# visual weight instead of relying on the two dashed lines alone.
band!(ax, [x_min, x_max], [lower_loa, lower_loa], [upper_loa, upper_loa];
    color = (BIAS_COLOR, 0.08))

scatter!(ax, mean_pressure, pressure_diff;
    color = BRAND, markersize = 14, strokewidth = 1, strokecolor = PAGE_BG,
    alpha = 0.65)

hlines!(ax, [bias]; color = BIAS_COLOR, linewidth = 2.5)
hlines!(ax, [upper_loa, lower_loa]; color = BIAS_COLOR, linewidth = 2, linestyle = :dash)

text!(ax, x_max, bias;
    text = "Bias = $(round(bias, digits = 1))",
    align = (:right, :bottom), fontsize = 13, color = BIAS_COLOR, offset = (0, 4))
text!(ax, x_max, upper_loa;
    text = "+1.96 SD = $(round(upper_loa, digits = 1))",
    align = (:right, :bottom), fontsize = 13, color = BIAS_COLOR, offset = (0, 4))
text!(ax, x_max, lower_loa;
    text = "−1.96 SD = $(round(lower_loa, digits = 1))",
    align = (:right, :top), fontsize = 13, color = BIAS_COLOR, offset = (0, -4))

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

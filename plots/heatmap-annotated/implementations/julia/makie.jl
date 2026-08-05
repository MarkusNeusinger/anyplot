# anyplot.ai
# heatmap-annotated: Annotated Heatmap
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 87/100 | Created: 2026-08-05

using CairoMakie
using Colors
using Random
using Statistics
using Printf

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const MIDPOINT = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"

# Imprint diverging colormap — correlations have a meaningful zero midpoint
const ANYPLOT_DIV = cgrad([colorant"#AE3030", MIDPOINT, colorant"#4467A3"])

# Cell-annotation contrast colors — chosen per cell from the fill's own
# luminance, so text stays legible whether the cell lands on the saturated
# red/blue ends or the near-background midpoint of the diverging scale.
const DARK_TEXT  = colorant"#1A1A17"
const LIGHT_TEXT = colorant"#F0EFE8"

# --- Data ---------------------------------------------------------------
variables = [
    "Temperature", "Humidity", "Wind Speed", "Pressure",
    "Rainfall", "Solar Radiation", "Cloud Cover", "Visibility",
]
n_vars = length(variables)
n_samples = 200

cloud_cover = randn(n_samples) .* 15 .+ 50
temperature = randn(n_samples) .* 5 .+ 20
humidity = -0.6 .* temperature .+ randn(n_samples) .* 8 .+ 70
wind_speed = randn(n_samples) .* 3 .+ 15
pressure = -0.4 .* temperature .+ randn(n_samples) .* 5 .+ 1013
rainfall = 0.5 .* humidity .+ randn(n_samples) .* 10
solar_radiation = 0.7 .* temperature .- 0.4 .* cloud_cover .+ randn(n_samples) .* 10 .+ 200
visibility = -0.5 .* humidity .- 0.3 .* cloud_cover .+ randn(n_samples) .* 5 .+ 20

measurements = hcat(
    temperature, humidity, wind_speed, pressure,
    rainfall, solar_radiation, cloud_cover, visibility,
)
corr_matrix = cor(measurements)

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution = (1200, 1200),
    fontsize = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title = "heatmap-annotated · julia · makie · anyplot.ai",
    titlesize = 20,
    titlecolor = INK,
    xticks = (1:n_vars, variables),
    yticks = (1:n_vars, variables),
    xticklabelrotation = pi / 4,
    xticklabelcolor = INK_SOFT,
    yticklabelcolor = INK_SOFT,
    xticklabelsize = 13,
    yticklabelsize = 13,
    backgroundcolor = PAGE_BG,
    topspinevisible = false,
    rightspinevisible = false,
    leftspinevisible = false,
    bottomspinevisible = false,
    xgridvisible = false,
    ygridvisible = false,
    aspect = DataAspect(),
    yreversed = true,
)

hm = heatmap!(
    ax, 1:n_vars, 1:n_vars, corr_matrix;
    colormap = ANYPLOT_DIV, colorrange = (-1, 1),
)

for i in 1:n_vars, j in 1:n_vars
    value = corr_matrix[i, j]
    fill_color = ANYPLOT_DIV[(value + 1) / 2]
    luminance = 0.299 * red(fill_color) + 0.587 * green(fill_color) + 0.114 * blue(fill_color)
    text_color = luminance > 0.5 ? DARK_TEXT : LIGHT_TEXT
    text!(
        ax, i, j;
        text = @sprintf("%.2f", value),
        align = (:center, :center),
        fontsize = 16,
        color = text_color,
    )
end

Colorbar(
    fig[1, 2], hm;
    label = "Correlation",
    labelsize = 14,
    labelcolor = INK,
    ticklabelsize = 12,
    ticklabelcolor = INK_SOFT,
    tickcolor = INK_SOFT,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

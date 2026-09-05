# anyplot.ai
# polar-scatter: Polar Scatter Plot
# Library: Makie.jl 0.21 | Julia 1.11
# Quality: pending | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
INK = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
GRID = THEME == "light" ? RGBAf(0.102, 0.102, 0.090, 0.15) : RGBAf(0.941, 0.937, 0.910, 0.15)

# Imprint palette (see prompts/default-style-guide.md "Categorical Palette") — first 4 positions
IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green — ALWAYS first series
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
]

# Data — wind observations: bearing (compass direction the wind blows FROM) and speed,
# clustered around a southwesterly prevailing direction, split by time of day
time_of_day = ["Morning", "Afternoon", "Evening", "Night"]
n_per_period = 30
prevailing_bearing = 225.0

wind_bearing_deg = Float64[]
wind_speed = Float64[]
period_index = Int[]
for (i, period) in enumerate(time_of_day)
    spread = 35.0 + 10.0 * i
    bearings = mod.(prevailing_bearing .+ spread .* randn(n_per_period), 360.0)
    speeds = abs.(4.0 .+ 3.0 .* randn(n_per_period)) .+ 1.5 * i
    append!(wind_bearing_deg, bearings)
    append!(wind_speed, speeds)
    append!(period_index, fill(i, n_per_period))
end
wind_bearing_rad = deg2rad.(wind_bearing_deg)

# Plot
fig = Figure(size = (1600, 900), fontsize = 14, backgroundcolor = PAGE_BG)

ax = PolarAxis(
    fig[1, 1];
    title = "polar-scatter · julia · makie · anyplot.ai",
    titlesize = 20,
    titlecolor = INK,
    theta_0 = -pi / 2,
    direction = -1,
    thetaticks = ((0:45:315) .* pi / 180, ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
    thetaticklabelsize = 12,
    thetaticklabelcolor = INK_SOFT,
    rticks = 0:5:15,
    rticklabelsize = 12,
    rticklabelcolor = INK_SOFT,
    rtickformat = values -> ["$(round(Int, v)) m/s" for v in values],
    spinecolor = INK_SOFT,
    rgridcolor = GRID,
    thetagridcolor = GRID,
    backgroundcolor = PAGE_BG,
)

series_plots = []
for (i, period) in enumerate(time_of_day)
    mask = period_index .== i
    p = scatter!(
        ax, wind_bearing_rad[mask], wind_speed[mask];
        color = IMPRINT_PALETTE[i], markersize = 14, alpha = 0.85,
        strokewidth = 1, strokecolor = PAGE_BG, label = period,
    )
    push!(series_plots, p)
end

Legend(
    fig[1, 2], series_plots, time_of_day;
    labelcolor = INK_SOFT, labelsize = 12,
    backgroundcolor = ELEVATED_BG, framevisible = false,
)
colsize!(fig.layout, 1, Relative(0.85))

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)

# anyplot.ai
# scatter-connected-temporal: Connected Scatter Plot with Temporal Path
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 85/100 | Created: 2026-06-09

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens — Imprint palette
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# Imprint sequential colormap — early (green) → late (blue) encodes temporal direction
const ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])

# Data — synthetic annual CO₂ concentration vs global temperature anomaly (1980–2022)
years = collect(1980:2022)
n     = length(years)

co2  = 338.0 .+ (years .- 1980) .* 1.9  .+ randn(n) .* 0.6
temp = 0.10  .+ (years .- 1980) .* 0.018 .+ randn(n) .* 0.06

# Temporal position [0, 1] for colormap
t_norm = (years .- years[1]) ./ (years[end] - years[1])

# Key year annotations (1-based: 1980, 1990, 2000, 2010, 2022)
key_idx = [1, 11, 21, 31, 43]

# Title — descriptive prefix added; scale fontsize to avoid overflow
title_str = "CO₂ vs Temperature · scatter-connected-temporal · julia · makie · anyplot.ai"
title_n   = length(title_str)
title_sz  = max(14, round(Int, 20 * 67 / title_n))

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = title_str,
    titlesize          = title_sz,
    titlecolor         = INK,
    xlabel             = "Atmospheric CO₂ (ppm)",
    ylabel             = "Temperature Anomaly (°C)",
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
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.12),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

# Temporal path — one segment per year pair, colored by midpoint time position
for i in 1:(n - 1)
    mid_t = (t_norm[i] + t_norm[i + 1]) / 2
    lines!(ax, [co2[i], co2[i + 1]], [temp[i], temp[i + 1]];
        color     = ANYPLOT_SEQ[mid_t],
        linewidth = 2.5,
    )
end

# Scatter points — colored by temporal position via Imprint sequential colormap
sc = scatter!(ax, co2, temp;
    color       = t_norm,
    colormap    = ANYPLOT_SEQ,
    markersize  = 11,
    strokewidth = 1.0,
    strokecolor = PAGE_BG,
)

# Key year labels at notable positions
for ki in key_idx
    text!(ax, co2[ki], temp[ki];
        text     = string(years[ki]),
        fontsize = 11,
        color    = INK,
        align    = (:center, :bottom),
        offset   = (0, 8),
    )
end

# Colorbar — shows year range encoded by the temporal gradient
Colorbar(fig[1, 2];
    colormap       = ANYPLOT_SEQ,
    limits         = (Float64(years[1]), Float64(years[end])),
    label          = "Year",
    labelcolor     = INK,
    ticklabelcolor = INK_SOFT,
    tickcolor      = INK_SOFT,
    ticklabelsize  = 11,
    labelsize      = 13,
    width          = 18,
)

colgap!(fig.layout, 1, 10)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)

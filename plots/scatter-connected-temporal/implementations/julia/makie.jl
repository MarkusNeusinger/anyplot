# anyplot.ai
# scatter-connected-temporal: Connected Scatter Plot with Temporal Path
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 91/100 | Created: 2026-06-09

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

# Data — synthetic daily closing price vs trading volume over 40 sessions
n    = 40
days = collect(1:n)

ret    = 0.004 .+ randn(n) .* 0.012
price  = 82.0 .* cumprod(1 .+ ret)
volume = 11.0 .+ 90.0 .* abs.(ret) .+ randn(n) .* 0.8

# Temporal position [0, 1] for colormap
t_norm = (days .- days[1]) ./ (days[end] - days[1])

# Key session annotations (first, every ~10th, last)
key_idx = [1, 10, 20, 30, 40]

title_str = "Price vs Volume · scatter-connected-temporal · julia · makie · anyplot.ai"
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
    xlabel             = "Trading Volume (million shares)",
    ylabel             = "Closing Price (USD)",
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

# Temporal path — one segment per session pair, colored by midpoint time position
for i in 1:(n - 1)
    mid_t = (t_norm[i] + t_norm[i + 1]) / 2
    lines!(ax, [volume[i], volume[i + 1]], [price[i], price[i + 1]];
        color     = ANYPLOT_SEQ[mid_t],
        linewidth = 2.5,
    )
end

# Scatter points — colored by temporal position via Imprint sequential colormap
sc = scatter!(ax, volume, price;
    color       = t_norm,
    colormap    = ANYPLOT_SEQ,
    markersize  = 14,
    strokewidth = 1.0,
    strokecolor = PAGE_BG,
)

# Directional arrow at temporal start — scaled to 6% of each axis span for visibility
let
    volume_span  = maximum(volume) - minimum(volume)
    price_span = maximum(price) - minimum(price)
    dx = volume[2] - volume[1]
    dy = price[2] - price[1]
    nx = dx / volume_span
    ny = dy / price_span
    len = sqrt(nx^2 + ny^2)
    scale = 0.06
    arrows!(ax, [volume[1]], [price[1]], [nx / len * scale * volume_span], [ny / len * scale * price_span];
        arrowsize = 16,
        color     = ANYPLOT_SEQ[0.0],
        linewidth = 2.0,
    )
end

# Key session labels at notable positions
for ki in key_idx
    text!(ax, volume[ki], price[ki];
        text     = "Day " * string(days[ki]),
        fontsize = 14,
        color    = INK,
        align    = (:center, :bottom),
        offset   = (0, 8),
    )
end

# Colorbar — shows trading-day range encoded by the temporal gradient
Colorbar(fig[1, 2];
    colormap       = ANYPLOT_SEQ,
    limits         = (Float64(days[1]), Float64(days[end])),
    label          = "Trading day",
    labelcolor     = INK,
    ticklabelcolor = INK_SOFT,
    tickcolor      = INK_SOFT,
    ticklabelsize  = 11,
    labelsize      = 13,
    width          = 18,
)

colgap!(fig.layout, 1, 20)

# Save
save("plot-$(THEME).png", fig; px_per_unit = 2)

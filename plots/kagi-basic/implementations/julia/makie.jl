# anyplot.ai
# kagi-basic: Basic Kagi Chart
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 84/100 | Created: 2026-09-02

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens ------------------------------------------------------------
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

YANG_COLOR = colorant"#009E73"  # Imprint position 1 — brand green, bullish
YIN_COLOR  = colorant"#AE3030"  # Imprint position 5 — semantic red, bearish

# --- Data: synthetic daily closing prices for a mid-cap stock ---------------
n_days = 240
daily_returns = randn(n_days) .* 0.012 .+ 0.0004
closes = 68.0 .* cumprod(1 .+ daily_returns)

# --- Kagi construction (4% reversal threshold) ------------------------------
reversal = 0.04

turn_x = Int[0]
turn_y = Float64[closes[1]]
direction = 0  # 0 = undetermined, 1 = up (yang), -1 = down (yin)

for price in closes[2:end]
    global direction
    last_y = turn_y[end]
    if direction == 0
        if price >= last_y * (1 + reversal)
            direction = 1
            turn_y[end] = price
        elseif price <= last_y * (1 - reversal)
            direction = -1
            turn_y[end] = price
        end
    elseif direction == 1
        if price > last_y
            turn_y[end] = price
        elseif price <= last_y * (1 - reversal)
            push!(turn_x, turn_x[end] + 1)
            push!(turn_y, price)
            direction = -1
        end
    else
        if price < last_y
            turn_y[end] = price
        elseif price >= last_y * (1 + reversal)
            push!(turn_x, turn_x[end] + 1)
            push!(turn_y, price)
            direction = 1
        end
    end
end

# --- Plot ---------------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "kagi-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Line Index",
    ylabel             = "Price (USD)",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible     = false,
    rightspinevisible   = false,
    leftspinecolor      = INK_SOFT,
    bottomspinecolor    = INK_SOFT,
    xgridvisible        = false,
    ygridcolor          = RGBAf(INK.r, INK.g, INK.b, 0.15),
    yticks              = Makie.LinearTicks(7),
)

# Each leg of the staircase is drawn with Makie's native stairs! step-plot
# recipe (shoulder/waist geometry via step = :post); color and thickness
# encode the leg's direction.
for i in 1:(length(turn_x) - 1)
    is_up = turn_y[i + 1] > turn_y[i]
    seg_color = is_up ? YANG_COLOR : YIN_COLOR
    seg_width = is_up ? 5.0 : 2.0
    stairs!(
        ax,
        [turn_x[i], turn_x[i + 1]],
        [turn_y[i], turn_y[i + 1]];
        step = :post,
        color = seg_color,
        linewidth = seg_width,
    )
end

# Small markers at each reversal (shoulder/waist) point sharpen the
# data-storytelling focal point beyond the raw staircase geometry.
scatter!(
    ax,
    turn_x[2:(end - 1)],
    turn_y[2:(end - 1)];
    color = PAGE_BG,
    strokecolor = INK_SOFT,
    strokewidth = 1.5,
    markersize = 7,
)

lines!(ax, [NaN, NaN], [NaN, NaN]; color = YANG_COLOR, linewidth = 5.0, label = "Yang (bullish)")
lines!(ax, [NaN, NaN], [NaN, NaN]; color = YIN_COLOR, linewidth = 2.0, label = "Yin (bearish)")
axislegend(ax; position = :rb, framevisible = false, labelcolor = INK_SOFT)

# --- Save ----------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

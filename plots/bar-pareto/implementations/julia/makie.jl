# anyplot.ai
# bar-pareto: Pareto Chart with Cumulative Line
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-06-20

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green (first series)
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red (semantic: threshold / error)
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

# Data — e-commerce support ticket categories, sorted descending by volume
categories = ["Billing Issues", "Login Problems", "Delivery Delays",
              "Product Damage", "Wrong Item", "App Crashes", "Other"]
counts     = [342, 289, 213, 178, 145, 98, 65]

n       = length(categories)
total   = sum(counts)
cum_pct = cumsum(counts) ./ total .* 100
xs      = collect(1:n)

# --- Figure ------------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

# Primary axis: bars (left y = ticket counts)
ax1 = Axis(
    fig[1, 1];
    title              = "bar-pareto · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Issue Category",
    ylabel             = "Ticket Count",
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    topspinevisible    = false,
    rightspinevisible  = false,
    backgroundcolor    = PAGE_BG,
    xticks             = (xs, categories),
    xticklabelrotation = π / 4,
    xticklabelalign    = (:right, :top),
    xticklabelsize     = 11,
    yticklabelsize     = 12,
    xlabelsize         = 14,
    ylabelsize         = 14,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15f0),
    yminorgridvisible  = false,
    xminorgridvisible  = false,
)

# Secondary axis: cumulative % line (right y = 0–100%)
ax2 = Axis(
    fig[1, 1];
    yaxisposition      = :right,
    ylabel             = "Cumulative %",
    ylabelcolor        = INK,
    yticklabelcolor    = INK_SOFT,
    ytickcolor         = INK_SOFT,
    rightspinecolor    = INK_SOFT,
    topspinevisible    = false,
    leftspinevisible   = false,
    bottomspinevisible = false,
    backgroundcolor    = :transparent,
    yticks             = (collect(0:20:100), ["0%", "20%", "40%", "60%", "80%", "100%"]),
    yticklabelsize     = 12,
    ylabelsize         = 14,
    xgridvisible       = false,
    ygridvisible       = false,
)
hidexdecorations!(ax2)
linkxaxes!(ax1, ax2)
ylims!(ax2, 0, 110)

# --- Bars (descending order, Imprint brand green) ----------------------------
barplot!(ax1, xs, counts;
    color       = IMPRINT_PALETTE[1],
    strokecolor = PAGE_BG,
    strokewidth = 1,
    gap         = 0.15,
)

# --- 80% threshold line (matte red dashed — semantic anchor for threshold) ---
hlines!(ax2, [80.0];
    color     = IMPRINT_PALETTE[5],
    linestyle = :dash,
    linewidth = 1.8,
)

# --- Cumulative % line with markers at bar centers ---------------------------
lines!(ax2, xs, cum_pct;
    color     = IMPRINT_PALETTE[3],
    linewidth = 2.5,
)
scatter!(ax2, xs, cum_pct;
    color        = IMPRINT_PALETTE[3],
    markersize   = 10,
    strokewidth  = 1.0,
    strokecolor  = PAGE_BG,
)

# --- Legend ------------------------------------------------------------------
Legend(
    fig[1, 2],
    [
        PolyElement(color = IMPRINT_PALETTE[1], strokecolor = PAGE_BG, strokewidth = 1),
        LineElement(color = IMPRINT_PALETTE[3], linewidth = 2.5),
        LineElement(color = IMPRINT_PALETTE[5], linestyle = :dash, linewidth = 1.8),
    ],
    ["Ticket Count", "Cumulative %", "80% Threshold"],
    framecolor       = INK_SOFT,
    backgroundcolor  = ELEVATED_BG,
    labelcolor  = INK,
    labelsize   = 11,
    patchsize   = (24, 10),
    margin      = (8, 8, 8, 8),
)

# --- Save --------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

# anyplot.ai
# box-notched: Notched Box Plot
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-08-18

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint categorical palette — 8 hues, theme-independent, hybrid-v3 sort
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green, ALWAYS first series
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red
]

# --- Data ---------------------------------------------------------------
# Reaction times (ms) across five cue conditions in a cognitive science
# experiment. Sample sizes and spreads vary slightly, as they would in real
# collected data, so some notches overlap (no significant median shift)
# while others clearly separate.
conditions = ["Baseline", "Visual Cue", "Auditory Cue", "Combined Cue", "Distraction"]
means       = [450.0, 410.0, 440.0, 390.0, 480.0]
stds        = [40.0, 35.0, 45.0, 30.0, 50.0]
sample_size = 50

group_index = Int[]
reaction_ms = Float64[]
point_color = RGB{Float64}[]
for (i, (mu, sigma)) in enumerate(zip(means, stds))
    append!(group_index, fill(i, sample_size))
    append!(reaction_ms, randn(sample_size) .* sigma .+ mu)
    append!(point_color, fill(IMPRINT_PALETTE[i], sample_size))
end

# --- Plot -----------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "box-notched · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Condition",
    ylabel             = "Reaction Time (ms)",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticks             = (1:length(conditions), conditions),
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
)

boxplot!(
    ax, group_index, reaction_ms;
    color               = point_color,
    width               = 0.6,
    show_notch          = true,
    notchwidth          = 0.5,
    strokecolor         = INK,
    strokewidth         = 1.5,
    mediancolor         = INK,
    medianlinewidth     = 2.5,
    whiskerwidth        = 0.4,
    whiskercolor        = INK_SOFT,
    whiskerlinewidth    = 2.0,
    markersize          = 10,
    outlierstrokecolor  = INK,
    outlierstrokewidth  = 1.0,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

# anyplot.ai
# column-stratigraphic: Stratigraphic Column with Lithology Patterns
# Library: Makie.jl | Julia 1.11
# Quality: pending | Created: 2026-06-17

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens (Imprint palette, theme-adaptive chrome) ------------------
const THEME       = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
const INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const INK_MUTED   = THEME == "light" ? colorant"#6B6A63" : colorant"#A8A79F"

# Imprint categorical palette — first series is always brand green
const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
    colorant"#BD8233",  # 4 — ochre
    colorant"#AE3030",  # 5 — matte red (deferred semantic anchor — skipped here)
    colorant"#2ABCCD",  # 6 — cyan
    colorant"#954477",  # 7 — rose
    colorant"#99B314",  # 8 — lime
]

const FILL_ALPHA = THEME == "light" ? 0.42 : 0.52
pattern_ink = RGBAf(INK.r, INK.g, INK.b, 0.82)

# --- Synthetic borehole section (depth increases downward, metres) ----------
tops       = [0.0, 24.0, 58.0, 82.0, 120.0, 140.0, 176.0, 200.0, 214.0]
bottoms    = [24.0, 58.0, 82.0, 120.0, 140.0, 176.0, 200.0, 214.0, 232.0]
lithology  = ["Sandstone", "Shale", "Limestone", "Siltstone", "Conglomerate",
              "Dolostone", "Sandstone", "Coal", "Shale"]
formation  = ["Aeolian Sand Mbr", "Marl Bay Shale", "Reefal Limestone",
              "Prodelta Siltstone", "Basal Conglomerate", "Tidal Dolostone",
              "Fluvial Sandstone", "Cyclothem Coal", "Black Basinal Shale"]
age        = ["Neogene", "Paleogene", "Late Cretaceous", "Early Cretaceous",
              "Jurassic", "Triassic", "Permian", "Pennsylvanian", "Mississippian"]

# Lithology → fill colour (canonical Imprint order; coal reads as semantic black)
lith_order = ["Sandstone", "Shale", "Limestone", "Siltstone",
              "Conglomerate", "Dolostone", "Coal"]
lith_color = Dict(
    "Sandstone"    => IMPRINT_PALETTE[1],
    "Shale"        => IMPRINT_PALETTE[2],
    "Limestone"    => IMPRINT_PALETTE[3],
    "Siltstone"    => IMPRINT_PALETTE[4],
    "Conglomerate" => IMPRINT_PALETTE[6],
    "Dolostone"    => IMPRINT_PALETTE[7],
    "Coal"         => INK,
)

# Depth of the unconformity (drawn as a wavy boundary instead of a straight rule)
const UNCONFORMITY = 120.0

# --- Lithology pattern painter ----------------------------------------------
# Draws an FGDC/USGS-style texture clipped to the rectangle [x0,x1]×[ytop,ybot].
# Reused for the column blocks and the legend swatches.
function add_pattern!(ax, lith, x0, x1, ytop, ybot; ink, page)
    w  = x1 - x0
    h  = ybot - ytop
    px = w * 0.05

    if lith == "Sandstone"
        # stipple dots
        n = clamp(round(Int, w * h * 0.55), 12, 360)
        xs = x0 .+ px .+ rand(n) .* (w - 2px)
        ys = ytop .+ rand(n) .* h
        scatter!(ax, xs, ys; marker = :circle, markersize = 2.6,
                 color = ink, strokewidth = 0)

    elseif lith == "Shale"
        # fine continuous laminae
        segs = Point2f[]
        yy = ytop + 4.0
        while yy < ybot - 0.5
            push!(segs, Point2f(x0 + px, yy), Point2f(x1 - px, yy))
            yy += 4.6
        end
        linesegments!(ax, segs; color = ink, linewidth = 0.8)

    elseif lith == "Limestone"
        # brick: horizontal courses + staggered vertical joints
        bh = 7.5
        bw = (x1 - x0) / 4
        segs = Point2f[]
        yy = ytop
        row = 0
        while yy <= ybot + 0.01
            yclip = min(yy, ybot)
            push!(segs, Point2f(x0, yclip), Point2f(x1, yclip))
            yy += bh
            row += 1
        end
        yy = ytop
        row = 0
        while yy < ybot - 0.5
            off = isodd(row) ? bw / 2 : 0.0
            xx = x0 + off
            while xx <= x1 + 0.01
                if xx >= x0 && xx <= x1
                    push!(segs, Point2f(xx, yy), Point2f(xx, min(yy + bh, ybot)))
                end
                xx += bw
            end
            yy += bh
            row += 1
        end
        linesegments!(ax, segs; color = ink, linewidth = 0.9)

    elseif lith == "Siltstone"
        # broken, staggered dashes
        dyl = 6.0
        dl  = w / 6
        gap = dl * 0.7
        segs = Point2f[]
        yy = ytop + dyl
        row = 0
        while yy < ybot - 0.5
            off = isodd(row) ? (dl + gap) / 2 : 0.0
            xx = x0 + px + off
            while xx < x1 - px
                push!(segs, Point2f(xx, yy), Point2f(min(xx + dl, x1 - px), yy))
                xx += dl + gap
            end
            yy += dyl
            row += 1
        end
        linesegments!(ax, segs; color = ink, linewidth = 1.0)

    elseif lith == "Conglomerate"
        # scattered clasts (open circles of varying size) over a faint matrix
        n = clamp(round(Int, w * h * 0.10), 5, 70)
        cx = x0 .+ 1.5px .+ rand(n) .* (w - 3px)
        cy = ytop .+ 0.06h .+ rand(n) .* (h * 0.88)
        sz = 8.0 .+ rand(n) .* 12.0
        scatter!(ax, cx, cy; marker = :circle, markersize = sz,
                 color = RGBAf(0, 0, 0, 0), strokecolor = ink, strokewidth = 1.2)
        nm = clamp(round(Int, w * h * 0.18), 8, 120)
        scatter!(ax, x0 .+ px .+ rand(nm) .* (w - 2px), ytop .+ rand(nm) .* h;
                 marker = :circle, markersize = 1.4, color = ink, strokewidth = 0)

    elseif lith == "Dolostone"
        # rhombic texture: staggered open diamonds
        dx = w / 4
        dy = 9.0
        cx = Float64[]
        cy = Float64[]
        yy = ytop + dy / 2
        row = 0
        while yy < ybot - dy / 4
            off = isodd(row) ? dx / 2 : 0.0
            xx = x0 + dx / 2 + off
            while xx < x1 + 0.01
                if xx >= x0 && xx <= x1
                    push!(cx, xx)
                    push!(cy, yy)
                end
                xx += dx
            end
            yy += dy
            row += 1
        end
        scatter!(ax, cx, cy; marker = :diamond, markersize = 11,
                 color = RGBAf(0, 0, 0, 0), strokecolor = ink, strokewidth = 1.0)

    elseif lith == "Coal"
        # solid block already filled; add a few light cleat partings
        segs = Point2f[]
        for f in (0.3, 0.55, 0.78)
            yy = ytop + f * h
            push!(segs, Point2f(x0 + px, yy), Point2f(x1 - px, yy))
        end
        linesegments!(ax, segs; color = RGBAf(page.r, page.g, page.b, 0.7), linewidth = 1.2)
    end
end

# --- Figure -----------------------------------------------------------------
title_str = "column-stratigraphic · julia · makie · anyplot.ai"
title_sz  = round(Int, 20 * min(1.0, 67 / length(title_str)))

fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    backgroundcolor   = PAGE_BG,
    title             = title_str,
    titlesize         = title_sz,
    titlecolor        = INK,
    titlegap          = 14,
    ylabel            = "Depth (m)",
    ylabelsize        = 15,
    ylabelcolor       = INK,
    yticks            = 0:40:240,
    yticklabelsize    = 13,
    yticklabelcolor   = INK_SOFT,
    ytickcolor        = INK_SOFT,
    leftspinecolor    = INK_SOFT,
    topspinevisible   = false,
    rightspinevisible = false,
    bottomspinevisible = false,
    xgridvisible      = false,
    ygridvisible      = false,
)

hidexdecorations!(ax)
xlims!(ax, 0.0, 14.0)
ylims!(ax, 240.0, -24.0)   # inverted y: 0 m at top, deepest layer at the bottom

# Column geometry
const X0 = 2.3
const X1 = 4.7
const X_AGE  = 2.05   # age labels — right-aligned, to the left of the column
const X_FORM = 5.0    # formation labels — left-aligned, to the right of the column

# --- Layers: tinted fill + lithology pattern --------------------------------
for i in eachindex(tops)
    ytop = tops[i]
    ybot = bottoms[i]
    lith = lithology[i]
    c    = lith_color[lith]
    fillc = lith == "Coal" ? RGBAf(c.r, c.g, c.b, 1.0) :
            RGBAf(c.r, c.g, c.b, FILL_ALPHA)

    poly!(ax, Rect2f(X0, ytop, X1 - X0, ybot - ytop);
          color = fillc, strokewidth = 0)
    add_pattern!(ax, lith, X0, X1, ytop, ybot; ink = pattern_ink, page = PAGE_BG)
end

# --- Layer boundaries (solid) + one wavy unconformity -----------------------
boundary_segs = Point2f[]
for d in unique(vcat(tops, bottoms[end]))
    d == UNCONFORMITY && continue
    push!(boundary_segs, Point2f(X0, d), Point2f(X1, d))
end
linesegments!(ax, boundary_segs; color = INK_SOFT, linewidth = 1.6)

# Wavy unconformity line
wx = range(X0, X1, length = 90)
wy = UNCONFORMITY .+ 2.6 .* sin.((wx .- X0) .* (2π * 3 / (X1 - X0)))
lines!(ax, collect(wx), collect(wy); color = INK_SOFT, linewidth = 2.4)

# Column outline (left/right edges)
lines!(ax, [X0, X0], [tops[1], bottoms[end]]; color = INK_SOFT, linewidth = 1.6)
lines!(ax, [X1, X1], [tops[1], bottoms[end]]; color = INK_SOFT, linewidth = 1.6)

# --- Age (left) and formation (right) labels --------------------------------
for i in eachindex(tops)
    ymid = (tops[i] + bottoms[i]) / 2

    text!(ax, X_AGE, ymid; text = age[i],
          align = (:right, :center), color = INK_SOFT, fontsize = 12.5)

    label = string(formation[i], "\n", Int(tops[i]), "–", Int(bottoms[i]), " m")
    text!(ax, X_FORM, ymid; text = label,
          align = (:left, :center), color = INK, fontsize = 13)
end

# Unconformity annotation
text!(ax, X1 + 0.06, UNCONFORMITY; text = "⌇ unconformity",
      align = (:left, :center), color = INK_MUTED, fontsize = 11.5)

# --- Lithology legend (pattern key, upper right) ----------------------------
text!(ax, 10.2, -14.0; text = "Lithology", align = (:left, :center),
      color = INK, fontsize = 14)

sw_x0 = 10.2
sw_x1 = 11.3
sw_h  = 17.0
for (k, lith) in enumerate(lith_order)
    yc = 6.0 + (k - 1) * 29.0
    yt = yc - sw_h / 2
    yb = yc + sw_h / 2
    c  = lith_color[lith]
    fillc = lith == "Coal" ? RGBAf(c.r, c.g, c.b, 1.0) :
            RGBAf(c.r, c.g, c.b, FILL_ALPHA)

    poly!(ax, Rect2f(sw_x0, yt, sw_x1 - sw_x0, sw_h);
          color = fillc, strokecolor = INK_SOFT, strokewidth = 1.2)
    add_pattern!(ax, lith, sw_x0, sw_x1, yt, yb; ink = pattern_ink, page = PAGE_BG)

    text!(ax, sw_x1 + 0.15, yc; text = lith,
          align = (:left, :center), color = INK_SOFT, fontsize = 13)
end

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)

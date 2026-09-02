# anyplot.ai
# network-transport-static: Static Transport Network Diagram
# Library: Makie.jl 0.22 | Julia 1.11
# Quality: pending | Created: 2026-09-02

using CairoMakie
using Colors

# Theme tokens — Imprint palette
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

const IMPRINT_PALETTE = [
    colorant"#009E73",  # 1 — brand green
    colorant"#C475FD",  # 2 — lavender
    colorant"#4467A3",  # 3 — blue
]
const KIND_COLOR = Dict(
    :express  => IMPRINT_PALETTE[1],
    :regional => IMPRINT_PALETTE[2],
    :local    => IMPRINT_PALETTE[3],
)

# Data — regional rail network: 12 stations, 22 timetabled services.
# Layout is a hand-placed schematic (x, y are fixed coordinates, not a
# force-directed layout): one express trunk (Westbrook–Eastport), one
# regional line crossing it at Central (Highlands–Lakeside), and three local
# spurs branching off single interchanges — so no station carries more than
# 4 lines and every junction's spokes sit well apart in angle. r is the
# node's inset radius in data units (edges stop at the node boundary, not
# its center) and ms is the marker's on-screen point size.
const stations = [
    (id = :central,    label = "Central",    x = 0.0,   y = 0.0,  r = 1.00, ldx = -0.95, ldy = 0.95,  halign = :right,  valign = :bottom, ms = 54),
    (id = :westfield,  label = "Westfield",  x = -5.0,  y = 0.0,  r = 0.65, ldx = 0.0,   ldy = 1.05,  halign = :center, valign = :bottom, ms = 36),
    (id = :westbrook,  label = "Westbrook",  x = -11.0, y = 0.0,  r = 0.65, ldx = 0.0,   ldy = 1.05,  halign = :center, valign = :bottom, ms = 36),
    (id = :harbor,     label = "Harbor",     x = 5.0,   y = 0.0,  r = 0.65, ldx = 0.0,   ldy = -1.05, halign = :center, valign = :top,    ms = 36),
    (id = :eastport,   label = "Eastport",   x = 11.0,  y = 0.0,  r = 0.65, ldx = 0.0,   ldy = 1.05,  halign = :center, valign = :bottom, ms = 36),
    (id = :northgate,  label = "Northgate",  x = 0.0,   y = 4.0,  r = 0.65, ldx = 1.05,  ldy = 0.0,   halign = :left,   valign = :center, ms = 36),
    (id = :highlands,  label = "Highlands",  x = 0.0,   y = 7.5,  r = 0.65, ldx = 1.05,  ldy = 0.0,   halign = :left,   valign = :center, ms = 36),
    (id = :riverside,  label = "Riverside",  x = 0.0,   y = -4.0, r = 0.65, ldx = -1.05, ldy = 0.0,   halign = :right,  valign = :center, ms = 36),
    (id = :lakeside,   label = "Lakeside",   x = 0.0,   y = -7.5, r = 0.65, ldx = 1.05,  ldy = 0.0,   halign = :left,   valign = :center, ms = 36),
    (id = :hillcrest,  label = "Hillcrest",  x = 7.5,   y = 3.2,  r = 0.65, ldx = 1.00,  ldy = 0.70,  halign = :left,   valign = :bottom, ms = 36),
    (id = :southgate,  label = "Southgate",  x = 3.5,   y = -6.5, r = 0.65, ldx = 1.00,  ldy = -0.70, halign = :left,   valign = :top,    ms = 36),
    (id = :meadowvale, label = "Meadowvale", x = -7.5,  y = -3.2, r = 0.65, ldx = -1.00, ldy = -0.70, halign = :right,  valign = :top,    ms = 36),
]

# Directed services: (source, target, route_id, departure, arrival, kind).
# Every line segment (trunk, regional, and each local spur) runs in both
# directions — the resulting pairs get an offset (parallel) pair of lines
# per the spec's "curved or offset edges" guidance for multi-edges.
const routes = [
    (source = :westbrook,  target = :westfield,  route_id = "EX 1", dep = "08:00", arr = "08:14", kind = :express),
    (source = :westfield,  target = :westbrook,  route_id = "EX 2", dep = "08:20", arr = "08:34", kind = :express),
    (source = :westfield,  target = :central,    route_id = "EX 3", dep = "08:14", arr = "08:26", kind = :express),
    (source = :central,    target = :westfield,  route_id = "EX 4", dep = "08:34", arr = "08:46", kind = :express),
    (source = :central,    target = :harbor,     route_id = "EX 5", dep = "08:26", arr = "08:38", kind = :express),
    (source = :harbor,     target = :central,    route_id = "EX 6", dep = "08:46", arr = "08:58", kind = :express),
    (source = :harbor,     target = :eastport,   route_id = "EX 7", dep = "08:38", arr = "08:52", kind = :express),
    (source = :eastport,   target = :harbor,     route_id = "EX 8", dep = "08:58", arr = "09:12", kind = :express),
    (source = :northgate,  target = :central,    route_id = "RE 1", dep = "08:05", arr = "08:20", kind = :regional),
    (source = :central,    target = :northgate,  route_id = "RE 2", dep = "08:25", arr = "08:40", kind = :regional),
    (source = :central,    target = :riverside,  route_id = "RE 3", dep = "08:10", arr = "08:25", kind = :regional),
    (source = :riverside,  target = :central,    route_id = "RE 4", dep = "08:30", arr = "08:45", kind = :regional),
    (source = :highlands,  target = :northgate,  route_id = "RE 5", dep = "07:45", arr = "08:05", kind = :regional),
    (source = :northgate,  target = :highlands,  route_id = "RE 6", dep = "08:40", arr = "09:00", kind = :regional),
    (source = :riverside,  target = :lakeside,   route_id = "RE 7", dep = "08:45", arr = "09:05", kind = :regional),
    (source = :lakeside,   target = :riverside,  route_id = "RE 8", dep = "07:40", arr = "08:00", kind = :regional),
    (source = :harbor,     target = :hillcrest,  route_id = "LO 1", dep = "08:40", arr = "08:55", kind = :local),
    (source = :hillcrest,  target = :harbor,     route_id = "LO 2", dep = "09:00", arr = "09:15", kind = :local),
    (source = :riverside,  target = :southgate,  route_id = "LO 3", dep = "08:48", arr = "09:02", kind = :local),
    (source = :southgate,  target = :riverside,  route_id = "LO 4", dep = "07:50", arr = "08:04", kind = :local),
    (source = :westfield,  target = :meadowvale, route_id = "LO 5", dep = "08:16", arr = "08:30", kind = :local),
    (source = :meadowvale, target = :westfield,  route_id = "LO 6", dep = "08:50", arr = "09:04", kind = :local),
]

const pos       = Dict(s.id => (s.x, s.y) for s in stations)
const inset     = Dict(s.id => s.r for s in stations)
const pair_seen = Set((r.source, r.target) for r in routes)
const degree    = Dict(s.id => length(Set(r.target for r in routes if r.source == s.id)) for s in stations)

# Title — mandated token plus a short descriptive prefix; fontsize scales
# down when the full string runs past the ~67-char baseline.
title_str  = "Regional Rail Network · network-transport-static · julia · makie · anyplot.ai"
title_size = round(Int, max(14, 20 * min(1.0, 67 / length(title_str))))

# Figure
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

Label(fig[0, 1:2], title_str; fontsize = title_size, color = INK, halign = :center)
rowsize!(fig.layout, 0, Fixed(70))

ax = Axis(
    fig[1, 1];
    backgroundcolor    = PAGE_BG,
    aspect             = DataAspect(),
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinevisible   = false,
    bottomspinevisible = false,
    xgridvisible       = false,
    ygridvisible       = false,
    xticksvisible      = false,
    yticksvisible      = false,
    xticklabelsvisible = false,
    yticklabelsvisible = false,
)
xlims!(ax, -12.3, 12.3)
ylims!(ax, -8.8, 8.8)

# Edges — offset parallel lines distinguish each bidirectional pair; every
# edge ends with a direction arrowhead and a rotated route/time label.
for r in routes
    sx, sy = pos[r.source]
    tx, ty = pos[r.target]
    dx, dy = tx - sx, ty - sy
    dist   = sqrt(dx^2 + dy^2)
    ux, uy = dx / dist, dy / dist
    px, py = -uy, ux

    # The offset side must be anchored to the *pair* (station A, station B),
    # not to this route's own direction — a reverse route's (ux, uy) already
    # points the opposite way, so using its own perpendicular here would flip
    # sign together with dirsign and cancel out, landing both directions on
    # the same line. Anchor px/py to the alphabetically-smaller-first vector
    # instead, which is identical for both directions of a pair.
    forward       = string(r.source) < string(r.target)
    dirsign       = forward ? 1.0 : -1.0
    canon_ux, canon_uy = forward ? (ux, uy) : (-ux, -uy)
    canon_px, canon_py = -canon_uy, canon_ux
    has_pair = (r.target, r.source) in pair_seen
    line_off = has_pair ? 0.80 * dirsign : 0.0
    ox, oy   = canon_px * line_off, canon_py * line_off

    r_src, r_tgt = inset[r.source], inset[r.target]
    x0, y0 = sx + ox + ux * r_src, sy + oy + uy * r_src
    x1, y1 = tx + ox - ux * r_tgt, ty + oy - uy * r_tgt

    col = KIND_COLOR[r.kind]
    lines!(ax, [x0, x1], [y0, y1]; color = col, linewidth = 2.4)
    arrows!(ax, [x1], [y1], [ux * 0.001], [uy * 0.001];
            arrowsize = 15, color = col, linewidth = 0)

    # Label sits near whichever endpoint has fewer other lines converging on
    # it, not at the midpoint — a busy interchange has every spoke close
    # together, but a quiet terminus has open space for the route/time text.
    label_off = abs(line_off) + 0.75
    lt = degree[r.target] <= degree[r.source] ? 0.70 : 0.30
    mx = x0 * (1 - lt) + x1 * lt + canon_px * label_off * dirsign
    my = y0 * (1 - lt) + y1 * lt + canon_py * label_off * dirsign

    ang = atan(dy, dx)
    if ang > pi / 2
        ang -= pi
    elseif ang < -pi / 2
        ang += pi
    end

    text!(ax, mx, my;
          text = "$(r.route_id) | $(r.dep) → $(r.arr)",
          fontsize = 13, color = INK_SOFT, align = (:center, :center), rotation = ang)
end

# Nodes — hollow rings so crossing edges stay visible through the station
# marker; Central is enlarged as the interchange hub (size, not text, carries
# the emphasis).
for s in stations
    scatter!(ax, [s.x], [s.y];
             markersize = s.ms, color = PAGE_BG, strokecolor = INK, strokewidth = 2.5)
    text!(ax, s.x + s.ldx, s.y + s.ldy;
          text = s.label, fontsize = 15, color = INK, align = (s.halign, s.valign))
end

# Legend — route type color key
leg_elements = [LineElement(color = KIND_COLOR[k], linewidth = 3.5) for k in (:express, :regional, :local)]
Legend(
    fig[1, 2],
    leg_elements,
    ["Express", "Regional", "Local"];
    title           = "Route type",
    titlesize       = 14,
    labelsize       = 13,
    titlecolor      = INK,
    labelcolor      = INK_SOFT,
    framevisible    = false,
    backgroundcolor = PAGE_BG,
    tellheight      = false,
    patchsize       = (26, 10),
)

colsize!(fig.layout, 1, Relative(0.85))
colsize!(fig.layout, 2, Relative(0.15))

save("plot-$(THEME).png", fig; px_per_unit = 2)

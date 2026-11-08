// anyplot.ai
// venn-labeled-items: Chartgeist-Style Venn Diagram with Labeled Items
// Library: muix 7.29.1 | JavaScript 22.22.3
// Quality: pending | Created: 2026-06-25

import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const SEPARATOR = " ∩ "; // joins the circle names of an overlap zone
const OUTSIDE = "outside"; // the zone for items in none of the circles
const CENTER_DIST = 1.18; // distance between circle centres, in radii (symmetric layout)
const NAME_BAND = 0.22; // room above and below the circles for the category names, in radii
const FILL_OPACITY = 0.2;
const ITEM_FONT = 16;
const NAME_FONT = 22;
const CHAR_W = 0.55; // average glyph width as a share of the font size
const LABEL_PAD = 5; // px kept free around each item label
const GRID_STEP = 6; // px between candidate label positions
const SEP_ENOUGH = 18; // px gap between labels of one zone beyond which centrality wins
const TITLE = "venn-labeled-items · javascript · muix · anyplot.ai";
const TITLE_H = 90;
const MARGIN = { top: 8, right: 24, bottom: 16, left: 24 };

// Columns: set these to your data's column names
const ITEM = "Beverage"; // role: label
const ZONE = "Zone"; // role: zone (one circle name, several joined by the separator, or "outside")

// Data: replace this block with your own records, one object per row
const data = [
  { [ITEM]: "Kombucha", [ZONE]: "Pretentious" },
  { [ITEM]: "Matcha Latte", [ZONE]: "Pretentious" },
  { [ITEM]: "Oat Milk Latte", [ZONE]: "Pretentious ∩ Delicious" },
  { [ITEM]: "Cold Brew", [ZONE]: "Pretentious ∩ Delicious" },
  { [ITEM]: "Flat White", [ZONE]: "Pretentious ∩ Delicious" },
  { [ITEM]: "Sparkling Water", [ZONE]: "Pretentious ∩ Affordable" },
  { [ITEM]: "Energy Drink", [ZONE]: "Pretentious ∩ Affordable" },
  { [ITEM]: "Espresso", [ZONE]: "Delicious" },
  { [ITEM]: "Cappuccino", [ZONE]: "Delicious" },
  { [ITEM]: "Diner Coffee", [ZONE]: "Delicious ∩ Affordable" },
  { [ITEM]: "Green Tea", [ZONE]: "Delicious ∩ Affordable" },
  { [ITEM]: "Orange Juice", [ZONE]: "Delicious ∩ Affordable" },
  { [ITEM]: "Tap Water", [ZONE]: "Affordable" },
  { [ITEM]: "Herbal Tea", [ZONE]: "Affordable" },
  { [ITEM]: "Chai", [ZONE]: "Pretentious ∩ Delicious ∩ Affordable" },
];

// Plot: reads only data and the constants above
const rows = data.filter((d) => d[ITEM] != null);
const zoneMembers = rows.map((d) =>
  d[ZONE] == null || String(d[ZONE]).trim() === OUTSIDE ? [] : String(d[ZONE]).split(SEPARATOR.trim()).map((s) => s.trim()),
);
const circles = [...new Set(zoneMembers.flat())];
const zoneMask = zoneMembers.map((members) => members.reduce((m, s) => m | (1 << circles.indexOf(s)), 0));

// Symmetric three-circle layout in px of the drawing area: equal radii, the
// centres on an equilateral triangle, the whole figure centred
const PLOT_W = window.ANYPLOT_SIZE.width - MARGIN.left - MARGIN.right;
const PLOT_H = window.ANYPLOT_SIZE.height - TITLE_H - MARGIN.top - MARGIN.bottom;
const R = PLOT_H / (2 + (CENTER_DIST * Math.sqrt(3)) / 2 + 2 * NAME_BAND);
const triangle = [
  { x: 0, y: (-CENTER_DIST * R) / Math.sqrt(3) },
  { x: (-CENTER_DIST * R) / 2, y: (CENTER_DIST * R) / (2 * Math.sqrt(3)) },
  { x: (CENTER_DIST * R) / 2, y: (CENTER_DIST * R) / (2 * Math.sqrt(3)) },
];
const yShift = PLOT_H / 2 - (triangle[0].y - R + triangle[1].y + R) / 2;
const centers = circles.map((_, i) => ({ x: PLOT_W / 2 + triangle[i].x, y: triangle[i].y + yShift }));
const figureCenter = { x: PLOT_W / 2, y: centers.reduce((s, c) => s + c.y, 0) / Math.max(1, centers.length) };

// Category names on each circle's outer side, pointing away from the centre
const nameBoxes = circles.map((name, i) => {
  const dx = centers[i].x - figureCenter.x;
  const dy = centers[i].y - figureCenter.y;
  const len = Math.hypot(dx, dy) || 1;
  const [ux, uy] = [dx / len, dy / len];
  const w = name.length * NAME_FONT * CHAR_W;
  const reach = R + 28 + (w / 2) * Math.abs(ux) + (NAME_FONT / 2) * Math.abs(uy);
  return { name, x: centers[i].x + ux * reach, y: centers[i].y + uy * reach, w: w + 2 * LABEL_PAD, h: NAME_FONT + 2 * LABEL_PAD };
});

// Candidate label positions: a px grid, each point with its zone (bit mask of
// the circles containing it) and its distance to the nearest circle edge
const candidates = [];
for (let x = 0; x <= PLOT_W; x += GRID_STEP) {
  for (let y = 0; y <= PLOT_H; y += GRID_STEP) {
    const dists = centers.map((c) => Math.hypot(x - c.x, y - c.y));
    candidates.push({
      x,
      y,
      mask: dists.reduce((m, d, i) => (d < R ? m | (1 << i) : m), 0),
      clearance: Math.min(...dists.map((d) => Math.abs(d - R))),
    });
  }
}

// Greedy placement, item by item: the label box must lie wholly inside its
// zone; among those spots it keeps clear of the labels already in that zone
// (and of the category names, for outside items), then prefers the zone's interior.
const placed = [];
rows.forEach((row, k) => {
  const mask = zoneMask[k];
  const w = String(row[ITEM]).length * ITEM_FONT * CHAR_W + 2 * LABEL_PAD;
  const h = ITEM_FONT + 2 * LABEL_PAD;
  const rivals = [...placed.filter((p) => p.mask === mask), ...(mask === 0 ? nameBoxes : [])];
  let best = null;
  candidates.forEach((c) => {
    if (c.mask !== mask || c.x - w / 2 < 0 || c.x + w / 2 > PLOT_W || c.y - h / 2 < 0 || c.y + h / 2 > PLOT_H) return;
    const probes = [[-w / 2, -h / 2], [w / 2, -h / 2], [-w / 2, h / 2], [w / 2, h / 2], [0, -h / 2], [0, h / 2], [-w / 2, 0], [w / 2, 0]];
    const fits = probes.every(([ox, oy]) =>
      centers.every((ctr, i) => Math.hypot(c.x + ox - ctr.x, c.y + oy - ctr.y) < R === Boolean(mask & (1 << i))),
    );
    if (!fits) return;
    const gap = Math.min(
      Infinity,
      ...rivals.map((p) => Math.max(Math.abs(p.x - c.x) - (p.w + w) / 2, Math.abs(p.y - c.y) - (p.h + h) / 2)),
    );
    const score = Math.min(gap, SEP_ENOUGH) * 1000 + c.clearance;
    if (best == null || score > best.score) best = { x: c.x, y: c.y, score };
  });
  const fallback = candidates.filter((c) => c.mask === mask).sort((a, b) => b.clearance - a.clearance)[0] ?? { x: PLOT_W / 2, y: PLOT_H / 2 };
  placed.push({ label: row[ITEM], mask, w, h, ...(best ?? fallback) });
});

// Item ink: the zone's fill seen through the translucent circles over the
// page, then dark or light text by that blend's luminance
const [pageRgb, ...paletteRgb] = [t.pageBg, ...t.palette].map((hex) => [16, 8, 0].map((s) => (parseInt(hex.slice(1), 16) >> s) & 255));
const zoneInk = new Map(
  [...new Set(zoneMask)].map((m) => {
    const blend = circles.reduce(
      (acc, _, i) => (m & (1 << i) ? acc.map((v, c) => v + (paletteRgb[i][c] - v) * FILL_OPACITY) : acc),
      pageRgb,
    );
    const [r, g, b] = blend.map((v) => v / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
    return [m, 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.2 ? "#1A1A17" : "#FAF8F1"];
  }),
);

const zoneCount = new Set(zoneMask).size;
const SUBTITLE = `A taxonomy of ${rows.length} ${ITEM.toLowerCase()}s across ${circles.length} traits and ${zoneCount} zones`;

// The community package has no Venn chart: a custom layer draws circles,
// category names and item labels through the container's px-unit scales.
function LabeledVenn() {
  const xScale = useXScale();
  const yScale = useYScale();

  return (
    <g>
      {circles.map((name, i) => (
        <circle
          key={`circle-${name}`}
          cx={xScale(centers[i].x)}
          cy={yScale(centers[i].y)}
          r={xScale(R) - xScale(0)}
          fill={t.palette[i]}
          fillOpacity={FILL_OPACITY}
          stroke={t.palette[i]}
          strokeWidth={2.5}
        />
      ))}
      {nameBoxes.map((box) => (
        <text
          key={`name-${box.name}`}
          x={xScale(box.x)}
          y={yScale(box.y)}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize={NAME_FONT}
          fontWeight={700}
          letterSpacing={1}
          fill={t.ink}
        >
          {box.name.toUpperCase()}
        </text>
      ))}
      {placed.map((p) => (
        <text
          key={`item-${p.label}`}
          x={xScale(p.x)}
          y={yScale(p.y)}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={ITEM_FONT}
          fill={zoneInk.get(p.mask)}
        >
          {p.label}
        </text>
      ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, padding: "18px 36px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 20, fontStyle: "italic", fontFamily: "Georgia, 'Times New Roman', serif", color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>
          {SUBTITLE}
        </div>
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H}
        series={[]}
        skipAnimation
        margin={MARGIN}
        xAxis={[{ id: "px-x", scaleType: "linear", min: 0, max: PLOT_W, position: "none" }]}
        yAxis={[{ id: "px-y", scaleType: "linear", min: 0, max: PLOT_H, reverse: true, position: "none" }]}
      >
        <LabeledVenn />
      </ChartsContainer>
    </div>
  );
}

// anyplot.ai
// venn-basic: Venn Diagram
// Library: muix 9.17.0 | JavaScript 22.23.4
// Quality: 89/100 | Updated: 2026-11-08
//# anyplot-orientation: square
import { ChartsContainer } from "@mui/x-charts/ChartsContainer";
import { useXScale, useYScale } from "@mui/x-charts/hooks";

const t = window.ANYPLOT_TOKENS;

// Constants
const SEPARATOR = " ∩ "; // joins the set labels of a combination
const FILL_OPACITY = 0.45;
const DOMAIN_PAD = 0.12; // share of the circles' extent left free around them for the set names
const SAMPLES = 260; // grid steps per side when searching each region's label spot
const TITLE = "venn-basic · javascript · muix · anyplot.ai";
const TITLE_H = 84;
const MARGIN = { top: 16, right: 24, bottom: 24, left: 24 };
const NAME_FONT = 22;
const COUNT_FONT = 24;

// Columns: set these to your data's column names
const SETS = "Skills"; // role: set_labels (one set, or several joined by the separator)
const COUNT = "Team members"; // role: set_sizes (inclusive: a pair counts its triple too)

// Data: replace this block with your own records, one object per row
// Skill overlap across a 200-person data team: one row per set with its size
// and one per pairwise and triple intersection with its inclusive size.
const data = [
  { [SETS]: "Python", [COUNT]: 120 },
  { [SETS]: "SQL", [COUNT]: 95 },
  { [SETS]: "Statistics", [COUNT]: 80 },
  { [SETS]: "Python ∩ SQL", [COUNT]: 45 },
  { [SETS]: "Python ∩ Statistics", [COUNT]: 38 },
  { [SETS]: "SQL ∩ Statistics", [COUNT]: 30 },
  { [SETS]: "Python ∩ SQL ∩ Statistics", [COUNT]: 18 },
];

// Plot: reads only data and the constants above
const combos = data
  .filter((d) => d[SETS] != null && d[COUNT] != null)
  .map((d) => ({ members: String(d[SETS]).split(SEPARATOR.trim()).map((s) => s.trim()), size: d[COUNT] }));
const sets = [...new Set(combos.flatMap((c) => c.members))];
// A region or combination is a bit mask over the sets (bit i = set i)
const inclusive = new Map(combos.map((c) => [c.members.reduce((m, s) => m | (1 << sets.indexOf(s)), 0), c.size]));
const masks = Array.from({ length: (1 << sets.length) - 1 }, (_, i) => i + 1);

// Exclusive count of each region by inclusion-exclusion over the inclusive sizes
const exclusive = new Map(
  masks.map((m) => [
    m,
    masks
      .filter((sup) => (sup & m) === m)
      .reduce((sum, sup) => {
        const extra = sup.toString(2).split("1").length - m.toString(2).split("1").length;
        return sum + (extra % 2 === 0 ? 1 : -1) * (inclusive.get(sup) ?? 0);
      }, 0),
  ]),
);
const unionTotal = [...exclusive.values()].reduce((a, b) => a + b, 0);

// Area-proportional layout: radius from the set size; each pair's centre
// distance is solved by bisection so the lens area matches its shared count.
const radii = sets.map((_, i) => Math.sqrt((inclusive.get(1 << i) ?? 0) / Math.PI));
const distance = sets.map(() => sets.map(() => 0));
sets.forEach((_, i) => {
  sets.forEach((__, j) => {
    if (j <= i) return;
    const [r1, r2] = [radii[i], radii[j]];
    const target = inclusive.get((1 << i) | (1 << j)) ?? 0;
    let lo = Math.abs(r1 - r2);
    let hi = r1 + r2;
    for (let k = 0; k < 60; k += 1) {
      const d = (lo + hi) / 2;
      const a1 = Math.acos(Math.min(1, Math.max(-1, (d * d + r1 * r1 - r2 * r2) / (2 * d * r1))));
      const a2 = Math.acos(Math.min(1, Math.max(-1, (d * d + r2 * r2 - r1 * r1) / (2 * d * r2))));
      const lens = r1 * r1 * a1 + r2 * r2 * a2 - 0.5 * Math.sqrt(Math.max(0, (-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2)));
      if (lens > target) lo = d;
      else hi = d;
    }
    distance[i][j] = distance[j][i] = (lo + hi) / 2;
  });
});
const centers = sets.map((_, i) => {
  if (i === 0) return { x: 0, y: 0 };
  if (i === 1) return { x: distance[0][1], y: 0 };
  const x = (distance[0][1] ** 2 + distance[0][i] ** 2 - distance[1][i] ** 2) / (2 * distance[0][1]);
  return { x, y: Math.sqrt(Math.max(0, distance[0][i] ** 2 - x * x)) };
});

// Equal px per unit on both axes: pad the circles' extent, then widen the
// shorter side to the drawing area's aspect ratio
const PLOT_W = window.ANYPLOT_SIZE.width - MARGIN.left - MARGIN.right;
const PLOT_H = window.ANYPLOT_SIZE.height - TITLE_H - MARGIN.top - MARGIN.bottom;
const bounds = {
  x0: Math.min(...centers.map((c, i) => c.x - radii[i])),
  x1: Math.max(...centers.map((c, i) => c.x + radii[i])),
  y0: Math.min(...centers.map((c, i) => c.y - radii[i])),
  y1: Math.max(...centers.map((c, i) => c.y + radii[i])),
};
const span = Math.max((bounds.x1 - bounds.x0) / PLOT_W, (bounds.y1 - bounds.y0) / PLOT_H) * (1 + 2 * DOMAIN_PAD);
const mid = { x: (bounds.x0 + bounds.x1) / 2, y: (bounds.y0 + bounds.y1) / 2 };
const xDomain = [mid.x - (span * PLOT_W) / 2, mid.x + (span * PLOT_W) / 2];
const yDomain = [mid.y - (span * PLOT_H) / 2, mid.y + (span * PLOT_H) / 2];

// Label spot of each region: the sampled point inside it farthest from any circle edge
const spots = new Map();
for (let gx = 0; gx <= SAMPLES; gx += 1) {
  for (let gy = 0; gy <= SAMPLES; gy += 1) {
    const x = bounds.x0 + ((bounds.x1 - bounds.x0) * gx) / SAMPLES;
    const y = bounds.y0 + ((bounds.y1 - bounds.y0) * gy) / SAMPLES;
    const dists = centers.map((c) => Math.hypot(x - c.x, y - c.y));
    const mask = dists.reduce((m, d, i) => (d < radii[i] ? m | (1 << i) : m), 0);
    if (mask === 0) continue;
    const clearance = Math.min(...dists.map((d, i) => Math.abs(d - radii[i])));
    if (!spots.has(mask) || clearance > spots.get(mask).clearance) spots.set(mask, { x, y, clearance });
  }
}

// Region ink: the fill seen through the translucent circles over the page,
// then dark or light text by that blend's luminance
const [pageRgb, ...paletteRgb] = [t.pageBg, ...t.palette].map((hex) => [16, 8, 0].map((s) => (parseInt(hex.slice(1), 16) >> s) & 255));
const regionInk = new Map(
  masks.map((m) => {
    const blend = sets.reduce(
      (acc, _, i) => (m & (1 << i) ? acc.map((v, c) => v + (paletteRgb[i][c] - v) * FILL_OPACITY) : acc),
      pageRgb,
    );
    const [r, g, b] = blend.map((v) => v / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
    return [m, 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.2 ? "#1A1A17" : "#FAF8F1"];
  }),
);

// Set names sit just outside their circle, away from the diagram's centre
const centroid = { x: centers.reduce((s, c) => s + c.x, 0) / sets.length, y: centers.reduce((s, c) => s + c.y, 0) / sets.length };
const SUBTITLE = `${unionTotal} ${COUNT.toLowerCase()} in ${sets.length} sets · circle areas ∝ set size, overlaps ∝ shared count · numbers count each region exclusively`;

// The community package has no Venn chart: a custom layer draws the circles
// and labels through the container's equal-scale linear axes.
function VennDiagram() {
  const xScale = useXScale();
  const yScale = useYScale();
  const pxPerUnit = Math.abs(xScale(1) - xScale(0));

  return (
    <g>
      {sets.map((s, i) => (
        <circle
          key={`circle-${s}`}
          cx={xScale(centers[i].x)}
          cy={yScale(centers[i].y)}
          r={radii[i] * pxPerUnit}
          fill={t.palette[i]}
          fillOpacity={FILL_OPACITY}
          stroke={t.palette[i]}
          strokeWidth={2.5}
        />
      ))}
      {sets.map((s, i) => {
        const dx = centers[i].x - centroid.x;
        const dy = centers[i].y - centroid.y;
        const len = Math.hypot(dx, dy) || 1;
        const [ux, uy] = sets.length === 1 ? [0, 1] : [dx / len, dy / len];
        const halfW = (s.length * NAME_FONT * 0.56) / 2;
        const reach = radii[i] * pxPerUnit + 14 + halfW * Math.abs(ux) + (NAME_FONT / 2) * Math.abs(uy);
        return (
          <text
            key={`name-${s}`}
            x={xScale(centers[i].x) + ux * reach}
            y={yScale(centers[i].y) - uy * reach}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={NAME_FONT}
            fontWeight={600}
            fill={t.ink}
          >
            {s}
          </text>
        );
      })}
      {masks
        .filter((m) => spots.has(m))
        .map((m) => (
          <text
            key={`count-${m}`}
            x={xScale(spots.get(m).x)}
            y={yScale(spots.get(m).y)}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={COUNT_FONT}
            fontWeight={700}
            fill={regionInk.get(m)}
          >
            {exclusive.get(m)}
          </text>
        ))}
    </g>
  );
}

export default function Chart() {
  const { width, height } = window.ANYPLOT_SIZE;

  return (
    <div style={{ width, height, background: t.pageBg, display: "flex", flexDirection: "column" }}>
      <div style={{ height: TITLE_H, padding: "20px 36px 0", boxSizing: "border-box" }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: t.ink, lineHeight: 1.2 }}>{TITLE}</div>
        <div style={{ fontSize: 15, color: t.inkSoft, lineHeight: 1.2, marginTop: 8 }}>{SUBTITLE}</div>
      </div>
      <ChartsContainer
        width={width}
        height={height - TITLE_H}
        series={[]}
        skipAnimation
        margin={MARGIN}
        xAxis={[{ id: "x", scaleType: "linear", min: xDomain[0], max: xDomain[1], position: "none" }]}
        yAxis={[{ id: "y", scaleType: "linear", min: yDomain[0], max: yDomain[1], position: "none" }]}
      >
        <VennDiagram />
      </ChartsContainer>
    </div>
  );
}

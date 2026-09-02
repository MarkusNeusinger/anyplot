// anyplot.ai
// maze-circular: Circular Maze Puzzle
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02
//# anyplot-orientation: square
//
// ECharts has no native maze primitive, so the maze is built by hand: a graph
// of one center hub plus ring x sector cells, carved into a spanning tree via
// randomized DFS (recursive backtracker). A spanning tree connects every cell
// through exactly one path, which is what guarantees the maze has exactly one
// solution from the outer entry to the center goal -- no loops, no shortcuts.
// The walls are drawn as polylines (arcs approximated by sampled points) and
// straight radial segments inside a single hidden-axis custom series so the
// geometry maps 1:1 onto the mount's actual pixel scale via api.coord().

const t = window.ANYPLOT_TOKENS;

// --- Maze parameters (one concrete scenario: 7 rings, medium difficulty) ---
const RINGS = 7;
const SECTORS = 12;
const DIFFICULTY = "medium";
const SEED = 42;
const HUB_RADIUS = 0.12; // fraction of the outer radius reserved for the goal hub
const OUTER_RADIUS = 1.0;
const RING_WIDTH = (OUTER_RADIUS - HUB_RADIUS) / RINGS;
const ANGLE_STEP = (2 * Math.PI) / SECTORS;
const ANGLE_OFFSET = Math.PI / 2; // sector 0 starts at 12 o'clock

// --- Deterministic RNG (mulberry32) -----------------------------------------
let seedState = SEED >>> 0;
function rand() {
  seedState = (seedState + 0x6d2b79f5) >>> 0;
  let z = seedState;
  z = Math.imul(z ^ (z >>> 15), z | 1);
  z ^= z + Math.imul(z ^ (z >>> 7), z | 61);
  return ((z ^ (z >>> 14)) >>> 0) / 4294967296;
}

// --- Graph: "C" (center hub) plus one node per (ring, sector) cell ----------
function cellId(ring, sector) {
  return `${ring}_${sector}`;
}
function neighborsOf(node) {
  if (node === "C") {
    const out = [];
    for (let s = 0; s < SECTORS; s++) out.push(cellId(0, s));
    return out;
  }
  const [ringStr, sectorStr] = node.split("_");
  const ring = Number(ringStr);
  const sector = Number(sectorStr);
  const out = [
    cellId(ring, (sector + 1) % SECTORS),
    cellId(ring, (sector - 1 + SECTORS) % SECTORS),
  ];
  out.push(ring === 0 ? "C" : cellId(ring - 1, sector));
  if (ring < RINGS - 1) out.push(cellId(ring + 1, sector));
  return out;
}
function edgeKey(a, b) {
  return a < b ? `${a}|${b}` : `${b}|${a}`;
}

// Randomized DFS (recursive backtracker) -> spanning tree = exactly one path
// between any two cells, which is what guarantees a single maze solution.
const visited = new Set(["C"]);
const passages = new Set();
const stack = ["C"];
while (stack.length > 0) {
  const current = stack[stack.length - 1];
  const options = neighborsOf(current).filter((n) => !visited.has(n));
  if (options.length === 0) {
    stack.pop();
    continue;
  }
  const next = options[Math.floor(rand() * options.length)];
  passages.add(edgeKey(current, next));
  visited.add(next);
  stack.push(next);
}
const entrySector = Math.floor(rand() * SECTORS);

// --- Geometry helpers --------------------------------------------------------
function angleOf(sector) {
  return ANGLE_OFFSET + sector * ANGLE_STEP;
}
function ringRadius(ringBoundary) {
  return HUB_RADIUS + ringBoundary * RING_WIDTH;
}
function polar(radius, angle) {
  return [radius * Math.cos(angle), radius * Math.sin(angle)];
}
function arcPoints(radius, angleStart, angleEnd, steps) {
  const pts = [];
  for (let k = 0; k <= steps; k++) {
    pts.push(polar(radius, angleStart + ((angleEnd - angleStart) * k) / steps));
  }
  return pts;
}

// --- Wall segments (data-space points, mapped to pixels via api.coord) -----
const arcWalls = []; // circumferential walls, one polyline per drawn segment
const radialWalls = []; // radial walls, one [p1, p2] pair per drawn segment

for (let ringBoundary = 0; ringBoundary <= RINGS; ringBoundary++) {
  const radius = ringRadius(ringBoundary);
  for (let sector = 0; sector < SECTORS; sector++) {
    let present;
    if (ringBoundary === 0) {
      present = !passages.has(edgeKey("C", cellId(0, sector)));
    } else if (ringBoundary === RINGS) {
      present = sector !== entrySector; // outer boundary, minus the entry gap
    } else {
      present = !passages.has(
        edgeKey(cellId(ringBoundary - 1, sector), cellId(ringBoundary, sector)),
      );
    }
    if (present) {
      arcWalls.push(arcPoints(radius, angleOf(sector), angleOf(sector + 1), 6));
    }
  }
}
for (let ring = 0; ring < RINGS; ring++) {
  const innerRadius = ringRadius(ring);
  const outerRadius = ringRadius(ring + 1);
  for (let sector = 0; sector < SECTORS; sector++) {
    const prevSector = (sector - 1 + SECTORS) % SECTORS;
    const present = !passages.has(edgeKey(cellId(ring, prevSector), cellId(ring, sector)));
    if (present) {
      const angle = angleOf(sector);
      radialWalls.push([polar(innerRadius, angle), polar(outerRadius, angle)]);
    }
  }
}

// --- Entry marker: an inward-pointing arrow at the outer gap ---------------
const entryAngle = angleOf(entrySector) + ANGLE_STEP / 2;
const entryArrowOuter = polar(OUTER_RADIUS + 0.09, entryAngle);
const entryArrowInner = polar(OUTER_RADIUS + 0.015, entryAngle);
const entryLabelAt = polar(OUTER_RADIUS + 0.14, entryAngle);

// --- Init & render ------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

const AX = { type: "value", min: -1.3, max: 1.3, show: false };

const option = {
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "maze-circular · javascript · echarts · anyplot.ai",
    subtext: `${RINGS} rings · ${SECTORS} sectors · ${DIFFICULTY} difficulty · seed ${SEED}`,
    left: "center",
    top: 26,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: "bold" },
    subtextStyle: { color: t.inkSoft, fontSize: 15 },
  },
  grid: { left: 150, right: 150, top: 150, bottom: 150 },
  xAxis: AX,
  yAxis: AX,
  series: [
    {
      type: "custom",
      coordinateSystem: "cartesian2d",
      silent: true,
      data: [0],
      renderItem: (params, api) => {
        const children = [];

        for (const pts of arcWalls) {
          children.push({
            type: "polyline",
            shape: { points: pts.map((p) => api.coord(p)) },
            style: { stroke: t.ink, lineWidth: 5, fill: "none", lineCap: "round" },
          });
        }
        for (const [p1, p2] of radialWalls) {
          const a = api.coord(p1);
          const b = api.coord(p2);
          children.push({
            type: "line",
            shape: { x1: a[0], y1: a[1], x2: b[0], y2: b[1] },
            style: { stroke: t.ink, lineWidth: 5, lineCap: "round" },
          });
        }

        // Goal hub at the center
        const centerPx = api.coord([0, 0]);
        const hubRadiusPx = api.coord([HUB_RADIUS, 0])[0] - centerPx[0];
        children.push({
          type: "circle",
          shape: { cx: centerPx[0], cy: centerPx[1], r: hubRadiusPx },
          style: { fill: t.palette[0], stroke: t.pageBg, lineWidth: 3 },
        });
        children.push({
          type: "text",
          style: {
            text: "GOAL",
            x: centerPx[0],
            y: centerPx[1],
            fill: t.pageBg,
            fontSize: 15,
            fontWeight: "bold",
            align: "center",
            verticalAlign: "middle",
          },
        });

        // Entry arrow (points inward through the gap) + label
        const outerPx = api.coord(entryArrowOuter);
        const innerPx = api.coord(entryArrowInner);
        const dx = innerPx[0] - outerPx[0];
        const dy = innerPx[1] - outerPx[1];
        const len = Math.hypot(dx, dy) || 1;
        const perpX = (-dy / len) * 10;
        const perpY = (dx / len) * 10;
        children.push({
          type: "polygon",
          shape: {
            points: [
              [innerPx[0], innerPx[1]],
              [outerPx[0] + perpX, outerPx[1] + perpY],
              [outerPx[0] - perpX, outerPx[1] - perpY],
            ],
          },
          style: { fill: t.palette[0] },
        });
        const labelPx = api.coord(entryLabelAt);
        children.push({
          type: "text",
          style: {
            text: "START",
            x: labelPx[0],
            y: labelPx[1],
            fill: t.palette[0],
            fontSize: 15,
            fontWeight: "bold",
            align: "center",
            verticalAlign: "middle",
          },
        });

        return { type: "group", silent: true, children };
      },
    },
  ],
};

chart.setOption(option);

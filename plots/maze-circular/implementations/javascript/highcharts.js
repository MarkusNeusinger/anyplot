// anyplot.ai
// maze-circular: Circular Maze Puzzle
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 88/100 | Created: 2026-09-02

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;
const size = window.ANYPLOT_SIZE;

// --- Deterministic PRNG (LCG, no seeded Math.random in the browser) --------
let seed = 42;
function rand() {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
}

// --- Maze topology: concentric rings subdivided into sectors ---------------
// Ring 0 is a single hub cell at the center; each outer ring roughly doubles
// its sector count whenever cells would otherwise grow too wide relative to
// the ring's radial thickness, keeping cells close to square (Theta-maze
// layout, after Jamis Buck's "circular maze" construction).
const NUM_RINGS = 7;
const rowHeight = 1 / NUM_RINGS;
const rows = [[{ i: 0 }]];
for (let r = 1; r < NUM_RINGS; r++) {
  const radius = r / NUM_RINGS;
  const circumference = 2 * Math.PI * radius;
  const prevCount = rows[r - 1].length;
  const cellWidth = circumference / prevCount;
  const ratio = Math.max(1, Math.round(cellWidth / rowHeight));
  const cellCount = prevCount * ratio;
  rows.push(Array.from({ length: cellCount }, (_, i) => ({ i })));
}

function cellKey(r, i) {
  return r + '-' + i;
}
function edgeKey(r1, i1, r2, i2) {
  const a = cellKey(r1, i1);
  const b = cellKey(r2, i2);
  return a < b ? a + '|' + b : b + '|' + a;
}

// Every cell's clockwise and inward neighbor (its counter-clockwise and
// outward neighbors are the same edges seen from the other side).
function neighbors(r, i) {
  const list = [];
  const count = rows[r].length;
  list.push({ r, i: (i + 1) % count });
  list.push({ r, i: (i - 1 + count) % count });
  if (r > 0) {
    const ratio = count / rows[r - 1].length;
    list.push({ r: r - 1, i: Math.floor(i / ratio) });
  }
  if (r < NUM_RINGS - 1) {
    const ratio = rows[r + 1].length / count;
    for (let k = 0; k < ratio; k++) {
      list.push({ r: r + 1, i: i * ratio + k });
    }
  }
  return list;
}

// --- Carve a perfect maze: randomized recursive backtracker ----------------
// A spanning tree over every cell guarantees exactly one path between the
// entry and the goal, satisfying the "exactly one solvable path" contract.
const visited = new Set([cellKey(0, 0)]);
const passages = new Set();
const stack = [{ r: 0, i: 0 }];
while (stack.length) {
  const cur = stack[stack.length - 1];
  const open = neighbors(cur.r, cur.i).filter((n) => !visited.has(cellKey(n.r, n.i)));
  if (open.length === 0) {
    stack.pop();
    continue;
  }
  const next = open[Math.floor(rand() * open.length)];
  passages.add(edgeKey(cur.r, cur.i, next.r, next.i));
  visited.add(cellKey(next.r, next.i));
  stack.push(next);
}

// Entry sits on the outer ring at the top; the goal is the center hub.
const outerRow = NUM_RINGS - 1;
const entryIndex = 0;

// --- Geometry ----------------------------------------------------------------
const titleClearance = 90;
const cx = size.width / 2;
const cy = titleClearance + (size.height - titleClearance) / 2;
const maxRadius = Math.min(size.width, size.height - titleClearance) / 2 - 60;
const wallWidth = 3.5;

function point(radius, angle) {
  return [cx + radius * Math.cos(angle), cy + radius * Math.sin(angle)];
}
function cellAngles(r, i) {
  const count = rows[r].length;
  const start = (i / count) * 2 * Math.PI - Math.PI / 2;
  const end = ((i + 1) / count) * 2 * Math.PI - Math.PI / 2;
  return [start, end];
}
// A filled wedge (inner arc, outer arc, two radial edges) for the soft
// "first step" highlight behind the entry cell.
function wedgePath(rInner, rOuter, a0, a1) {
  const [ix1, iy1] = point(rInner, a0);
  const [ox1, oy1] = point(rOuter, a0);
  const [ox2, oy2] = point(rOuter, a1);
  const [ix2, iy2] = point(rInner, a1);
  return ['M', ix1, iy1, 'L', ox1, oy1, 'A', rOuter, rOuter, 0, 0, 1, ox2, oy2, 'L', ix2, iy2, 'A', rInner, rInner, 0, 0, 0, ix1, iy1, 'Z'];
}

const chart = Highcharts.chart('container', {
  chart: {
    backgroundColor: 'transparent',
    animation: false,
    style: { fontFamily: 'inherit' },
    events: {
      load: function () {
        const renderer = this.renderer;
        const wallStyle = { stroke: t.ink, 'stroke-width': wallWidth, fill: 'none', 'stroke-linecap': 'round' };
        const perimeterStyle = { stroke: t.ink, 'stroke-width': wallWidth + 1.5, fill: 'none', 'stroke-linecap': 'round' };

        // Soft "first step" highlight: a faint tint over the entry cell,
        // hinting at the route into the maze without giving the solution away.
        const [entryA0, entryA1] = cellAngles(outerRow, entryIndex);
        const entryInnerRadius = (outerRow / NUM_RINGS) * maxRadius;
        renderer
          .path(wedgePath(entryInnerRadius, maxRadius, entryA0, entryA1))
          .attr({ fill: t.palette[0], 'fill-opacity': 0.1, stroke: 'none' })
          .add();

        // Ring boundaries: one arc per fine-grained cell, skipped where a
        // passage (spanning-tree edge) crosses that boundary.
        for (let r = 1; r < NUM_RINGS; r++) {
          const radius = (r / NUM_RINGS) * maxRadius;
          for (let i = 0; i < rows[r].length; i++) {
            const ratio = rows[r].length / rows[r - 1].length;
            const parent = Math.floor(i / ratio);
            if (passages.has(edgeKey(r, i, r - 1, parent))) continue;
            const [a0, a1] = cellAngles(r, i);
            const [x1, y1] = point(radius, a0);
            const [x2, y2] = point(radius, a1);
            renderer
              .path(['M', x1, y1, 'A', radius, radius, 0, 0, 1, x2, y2])
              .attr(wallStyle)
              .add();
          }
        }

        // Outer perimeter: drawn heavier than the interior walls (a classic
        // maze-print convention that frames the puzzle), with one gap left
        // open for entry.
        for (let i = 0; i < rows[outerRow].length; i++) {
          if (i === entryIndex) continue;
          const [a0, a1] = cellAngles(outerRow, i);
          const [x1, y1] = point(maxRadius, a0);
          const [x2, y2] = point(maxRadius, a1);
          renderer
            .path(['M', x1, y1, 'A', maxRadius, maxRadius, 0, 0, 1, x2, y2])
            .attr(perimeterStyle)
            .add();
        }

        // Radial walls: the boundary between a cell and its clockwise
        // neighbor within the same ring, skipped where a passage crosses.
        for (let r = 1; r < NUM_RINGS; r++) {
          const innerR = (r / NUM_RINGS) * maxRadius;
          const outerR = ((r + 1) / NUM_RINGS) * maxRadius;
          const count = rows[r].length;
          for (let i = 0; i < count; i++) {
            const next = (i + 1) % count;
            if (passages.has(edgeKey(r, i, r, next))) continue;
            const angle = (next / count) * 2 * Math.PI - Math.PI / 2;
            const [x1, y1] = point(innerR, angle);
            const [x2, y2] = point(outerR, angle);
            renderer.path(['M', x1, y1, 'L', x2, y2]).attr(wallStyle).add();
          }
        }

        // Goal marker at the center hub: a radial gradient (via Highcharts'
        // native Color/gradient API) gives the hub a subtle raised depth
        // instead of a flat fill.
        const goalFill = {
          radialGradient: { cx: 0.35, cy: 0.35, r: 0.75 },
          stops: [
            [0, Highcharts.color(t.palette[1]).brighten(0.35).get()],
            [1, t.palette[1]],
          ],
        };
        renderer.circle(cx, cy, 16).attr({ fill: goalFill, stroke: t.pageBg, 'stroke-width': 3 }).add();
        renderer
          .text('GOAL', cx, cy - 28)
          .attr({ align: 'center', zIndex: 5 })
          .css({ color: t.ink, fontSize: '15px', fontWeight: '600' })
          .add();

        // Entry marker just outside the perimeter gap.
        const [ea0, ea1] = cellAngles(outerRow, entryIndex);
        const entryAngle = (ea0 + ea1) / 2;
        const [ex1, ey1] = point(maxRadius - 4, entryAngle);
        const [ex2, ey2] = point(maxRadius + 34, entryAngle);
        renderer
          .path(['M', ex1, ey1, 'L', ex2, ey2])
          .attr({ stroke: t.palette[0], 'stroke-width': 5, 'stroke-linecap': 'round' })
          .add();
        renderer
          .text('START', ex2, ey2 - 12)
          .attr({ align: 'center', zIndex: 5 })
          .css({ color: t.palette[0], fontSize: '15px', fontWeight: '600' })
          .add();
      },
    },
  },
  title: {
    text: 'maze-circular · javascript · highcharts · anyplot.ai',
    style: { color: t.ink, fontSize: '27px', fontWeight: '600' },
  },
  credits: { enabled: false },
  series: [],
});

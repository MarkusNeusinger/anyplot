// anyplot.ai
// maze-printable: Printable Maze Puzzle
// Library: chartjs 4.4.7 | JavaScript 22
// Quality: pending | Created: 2026-09-05

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Maze generation: recursive-backtracker DFS on a grid graph ------------
// A DFS spanning tree over the cell graph guarantees exactly one path
// between any two cells (a "perfect" maze) — no loops, no isolated pockets.
const COLS = 20;
const ROWS = 20;

// Tiny fixed-seed LCG — the browser has no seeded RNG.
function makeRng(seed) {
  let state = seed >>> 0;
  return function () {
    state = (Math.imul(state, 1103515245) + 12345) >>> 0;
    return state / 4294967296;
  };
}
const rng = makeRng(42);

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

const cellIndex = (col, row) => row * COLS + col;
const visited = new Array(COLS * ROWS).fill(false);
const walls = Array.from({ length: COLS * ROWS }, () => ({
  N: true,
  S: true,
  E: true,
  W: true,
}));

const stack = [[0, 0]];
visited[cellIndex(0, 0)] = true;
while (stack.length > 0) {
  const [col, row] = stack[stack.length - 1];
  const candidates = shuffle([
    [col, row - 1, "N", "S"],
    [col, row + 1, "S", "N"],
    [col - 1, row, "W", "E"],
    [col + 1, row, "E", "W"],
  ]).filter(
    ([nc, nr]) => nc >= 0 && nc < COLS && nr >= 0 && nr < ROWS && !visited[cellIndex(nc, nr)],
  );

  if (candidates.length === 0) {
    stack.pop();
    continue;
  }
  const [nextCol, nextRow, dir, opposite] = candidates[0];
  walls[cellIndex(col, row)][dir] = false;
  walls[cellIndex(nextCol, nextRow)][opposite] = false;
  visited[cellIndex(nextCol, nextRow)] = true;
  stack.push([nextCol, nextRow]);
}

// --- Wall segments: convert remaining walls into line-chart coordinates ----
// Cell (col, row) occupies x in [col, col+1], y in [ROWS-row-1, ROWS-row] so
// row 0 (the start row) renders at the top of the chart.
const wallSegments = [];
function addWall(x1, y1, x2, y2) {
  wallSegments.push({ x: x1, y: y1 }, { x: x2, y: y2 }, { x: null, y: null });
}

for (let row = 0; row < ROWS; row++) {
  for (let col = 0; col < COLS; col++) {
    const cell = walls[cellIndex(col, row)];
    if (cell.N) addWall(col, ROWS - row, col + 1, ROWS - row);
    if (cell.W) addWall(col, ROWS - row - 1, col, ROWS - row);
  }
}
for (let col = 0; col < COLS; col++) {
  if (walls[cellIndex(col, ROWS - 1)].S) addWall(col, 0, col + 1, 0);
}
for (let row = 0; row < ROWS; row++) {
  if (walls[cellIndex(COLS - 1, row)].E) addWall(COLS, ROWS - row - 1, COLS, ROWS - row);
}

// Start (top-left cell) and goal (bottom-right cell), at cell centers.
const startPoint = [{ x: 0.5, y: ROWS - 0.5 }];
const goalPoint = [{ x: COLS - 0.5, y: 0.5 }];

// --- Mount -------------------------------------------------------------
const canvas = document.createElement("canvas");
document.getElementById("container").appendChild(canvas);

// --- Chart -----------------------------------------------------------------
const title = "maze-printable · javascript · chartjs · anyplot.ai";

new Chart(canvas, {
  type: "line",
  data: {
    datasets: [
      {
        label: "Walls",
        data: wallSegments,
        borderColor: t.ink,
        borderWidth: 9,
        borderCapStyle: "square",
        borderJoinStyle: "miter",
        pointRadius: 0,
        showLine: true,
        spanGaps: false,
        fill: false,
        tension: 0,
      },
      {
        label: "Start",
        data: startPoint,
        showLine: false,
        pointStyle: "triangle",
        pointRadius: 26,
        backgroundColor: t.palette[0],
        borderColor: t.palette[0],
      },
      {
        label: "Goal",
        data: goalPoint,
        showLine: false,
        pointStyle: "star",
        pointRadius: 30,
        backgroundColor: t.palette[1],
        borderColor: t.palette[1],
      },
    ],
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    layout: { padding: 24 },
    plugins: {
      title: { display: true, text: title, color: t.ink, font: { size: 22 } },
      legend: {
        display: true,
        position: "bottom",
        labels: {
          color: t.ink,
          font: { size: 16 },
          usePointStyle: true,
          filter: (item) => item.text !== "Walls",
        },
      },
    },
    scales: {
      x: { type: "linear", min: 0, max: COLS, display: false },
      y: { type: "linear", min: 0, max: ROWS, display: false },
    },
  },
});

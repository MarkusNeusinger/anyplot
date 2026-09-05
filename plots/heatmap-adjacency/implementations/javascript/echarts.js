// anyplot.ai
// heatmap-adjacency: Network Adjacency Matrix Heatmap
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-05

//# anyplot-orientation: square
const t = window.ANYPLOT_TOKENS;

// --- Data: employee collaboration network, grouped by department -----------
// Node order is fixed by department membership so the matrix exposes
// block-diagonal structure (dense intra-department collaboration) without
// any extra clustering step.
const departments = [
  { name: "Engineering", size: 12 },
  { name: "Design", size: 8 },
  { name: "Marketing", size: 10 },
];

const nodeNames = [];
const nodeDept = [];
departments.forEach((dept, deptIndex) => {
  for (let i = 1; i <= dept.size; i++) {
    nodeNames.push(`${dept.name.slice(0, 3).toUpperCase()}-${i}`);
    nodeDept.push(deptIndex);
  }
});
const n = nodeNames.length;

// Boundary label: show the department name once, centered under its block.
const boundaryLabel = {};
let cursor = 0;
departments.forEach((dept) => {
  boundaryLabel[cursor + Math.floor((dept.size - 1) / 2)] = dept.name;
  cursor += dept.size;
});
const axisLabelFormatter = (value, index) => boundaryLabel[index] ?? "";

// Fixed-seed LCG so the matrix is reproducible without a browser RNG.
const makeRng = (seed) => {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
};
const rng = makeRng(42);

// Symmetric weight matrix: dense within a department, sparse across.
const weights = Array.from({ length: n }, () => new Array(n).fill(0));
for (let i = 0; i < n; i++) {
  for (let j = i + 1; j < n; j++) {
    const sameDept = nodeDept[i] === nodeDept[j];
    let w = 0;
    if (sameDept && rng() > 0.12) {
      w = 0.35 + rng() * 0.6;
    } else if (!sameDept && rng() > 0.75) {
      w = 0.05 + rng() * 0.3;
    }
    w = Math.round(w * 100) / 100;
    weights[i][j] = w;
    weights[j][i] = w;
  }
}

// Heatmap cells: [colIndex, rowIndex, weight]. The diagonal (self) is
// omitted entirely; absent edges (weight 0) get an explicit near-background
// fill so they read as "no connection" rather than the low end of the scale.
const cells = [];
for (let row = 0; row < n; row++) {
  for (let col = 0; col < n; col++) {
    if (row === col) continue;
    const w = weights[row][col];
    cells.push({
      value: [col, row, w],
      itemStyle:
        w === 0
          ? { color: t.elevatedBg, borderColor: t.pageBg, borderWidth: 1 }
          : { borderColor: t.pageBg, borderWidth: 1 },
    });
  }
}

// --- Init -------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "Employee Collaboration Network · heatmap-adjacency · javascript · echarts · anyplot.ai",
    left: "center",
    top: 16,
    textStyle: { color: t.ink, fontSize: 17 },
  },
  tooltip: {
    formatter: (p) =>
      p.value[2] > 0
        ? `${nodeNames[p.value[1]]} ↔ ${nodeNames[p.value[0]]}<br/>strength: ${p.value[2].toFixed(2)}`
        : `${nodeNames[p.value[1]]} ↔ ${nodeNames[p.value[0]]}<br/>no connection`,
  },
  grid: { left: 110, right: 170, top: 110, bottom: 90 },
  xAxis: {
    type: "category",
    data: nodeNames,
    position: "bottom",
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { show: false },
    axisLabel: { color: t.inkSoft, fontSize: 14, interval: 0, formatter: axisLabelFormatter },
  },
  yAxis: {
    type: "category",
    data: nodeNames,
    inverse: true,
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { show: false },
    axisLabel: { color: t.inkSoft, fontSize: 14, interval: 0, formatter: axisLabelFormatter },
  },
  visualMap: {
    type: "continuous",
    min: 0.05,
    max: 1,
    calculable: false,
    orient: "vertical",
    right: 16,
    top: "middle",
    itemWidth: 22,
    itemHeight: 260,
    text: ["Strong", "Weak"],
    textStyle: { color: t.inkSoft, fontSize: 14 },
    inRange: { color: t.seq },
  },
  series: [
    {
      type: "heatmap",
      data: cells,
      itemStyle: { color: t.elevatedBg },
    },
  ],
});

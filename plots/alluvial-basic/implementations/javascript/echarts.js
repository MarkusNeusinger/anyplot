// anyplot.ai
// alluvial-basic: Basic Alluvial Diagram
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Student performance tracks followed across four semesters. Each time point
// is a strict column; every link only connects a category to its immediate
// successor column, which keeps the ECharts sankey layout aligned into a
// classic alluvial column structure (no cross-generation links).
const timePoints = ["Semester 1", "Semester 2", "Semester 3", "Semester 4"];
const categories = ["Advanced", "Proficient", "Developing", "Needs Support"];
const categoryColors = [t.palette[0], t.palette[1], t.palette[2], t.palette[3]];

// Transition matrices: transitions[k][from][to] = students moving from
// categories[from] at timePoints[k] to categories[to] at timePoints[k + 1].
const transitions = [
  [
    [45, 15, 0, 0],
    [20, 50, 20, 0],
    [0, 25, 45, 20],
    [0, 0, 25, 35],
  ],
  [
    [50, 15, 0, 0],
    [25, 45, 20, 0],
    [0, 30, 40, 20],
    [0, 0, 20, 35],
  ],
  [
    [60, 15, 0, 0],
    [30, 45, 15, 0],
    [0, 25, 40, 15],
    [0, 0, 15, 40],
  ],
];

const nodeName = (timeIdx, catIdx) => `${timeIdx}|${catIdx}`;

const nodes = timePoints.flatMap((_, timeIdx) =>
  categories.map((_, catIdx) => ({
    name: nodeName(timeIdx, catIdx),
    itemStyle: { color: categoryColors[catIdx] },
  }))
);

const links = transitions.flatMap((matrix, k) =>
  matrix.flatMap((row, fromIdx) =>
    row
      .map((value, toIdx) => ({ value, fromIdx, toIdx }))
      .filter((link) => link.value > 0)
      .map((link) => ({
        source: nodeName(k, link.fromIdx),
        target: nodeName(k + 1, link.toIdx),
        value: link.value,
      }))
  )
);

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Column headers (time points) ----------------------------------------
// Centers approximate the sankey's four justified column x-positions for the
// 1600px landscape mount (left: 60, right: 60, nodeWidth: 24).
const columnCenters = [72, 557, 1043, 1528];
const headerGraphics = timePoints.map((label, i) => ({
  type: "text",
  position: [columnCenters[i], 108],
  style: {
    text: label,
    textAlign: "center",
    fill: t.ink,
    fontSize: 16,
    fontWeight: "bold",
  },
}));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  color: t.palette,
  backgroundColor: "transparent",
  title: {
    text: "alluvial-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 30,
    textStyle: { color: t.ink, fontSize: 22 },
  },
  graphic: { elements: headerGraphics },
  series: [
    {
      type: "sankey",
      left: 60,
      right: 60,
      top: 160,
      bottom: 70,
      nodeWidth: 24,
      nodeGap: 14,
      nodeAlign: "justify",
      layoutIterations: 64,
      emphasis: { focus: "adjacency" },
      label: {
        position: "top",
        color: t.ink,
        fontSize: 14,
        formatter: (params) => categories[Number(params.name.split("|")[1])],
      },
      lineStyle: { color: "source", opacity: 0.45, curveness: 0.5 },
      data: nodes,
      links,
    },
  ],
});

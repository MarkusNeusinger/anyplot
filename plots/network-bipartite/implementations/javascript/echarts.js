// anyplot.ai
// network-bipartite: Bipartite Network Graph
// Library: echarts 5.5.1 | JavaScript 22
// Quality: pending | Created: 2026-09-05

const theme = window.ANYPLOT_THEME;
const t = window.ANYPLOT_TOKENS;
const muted = theme === "dark" ? "#A8A79F" : "#6B6A63";

// --- Data (in-memory, deterministic) ----------------------------------------
// Author-paper affiliation network: which researchers contributed to which
// publications. Edge weight = number of shared authorship credits.
const researchers = [
  "A. Chen", "B. Diallo", "C. Kowalski", "D. Nakamura", "E. Osei",
  "F. Petrova", "G. Reyes", "H. Singh", "I. Tanaka", "J. Volkov",
];
const papers = [
  "Graph Embeddings", "Federated Learning", "Attention Mechanisms",
  "Robotic Grasping", "Climate Modeling", "Protein Folding",
  "Speech Synthesis", "Autonomous Driving", "Drug Discovery",
  "Quantum Computing", "Computer Vision", "Natural Language",
  "Recommender Systems", "Time Series Forecasting",
];

// [researcherIndex, paperIndex, weight]
const links = [
  [0, 0, 3], [0, 1, 2], [0, 3, 4], [0, 5, 1], [0, 13, 1],
  [1, 0, 2], [1, 2, 3],
  [2, 1, 4], [2, 4, 2], [2, 6, 3],
  [3, 3, 1], [3, 7, 2], [3, 8, 3], [3, 9, 1],
  [4, 2, 2], [4, 5, 3],
  [5, 6, 4], [5, 10, 2], [5, 11, 1],
  [6, 4, 3], [6, 9, 2],
  [7, 8, 2], [7, 10, 3], [7, 12, 1],
  [8, 7, 1], [8, 13, 4],
  [9, 11, 2], [9, 12, 3], [9, 13, 2],
];

// --- Layout: two fixed columns, degree-weighted node size -------------------
const researcherDegree = researchers.map(
  (_, i) => links.filter((l) => l[0] === i).length,
);
const paperDegree = papers.map(
  (_, j) => links.filter((l) => l[1] === j).length,
);

const yFor = (i, n) => (n === 1 ? 0.5 : i / (n - 1));
const sizeFor = (degree) => 16 + degree * 6;

const nodes = [
  ...researchers.map((name, i) => ({
    id: `r${i}`,
    name,
    category: 0,
    x: 0,
    y: yFor(i, researchers.length),
    symbolSize: sizeFor(researcherDegree[i]),
    label: { position: "left" },
  })),
  ...papers.map((name, j) => ({
    id: `p${j}`,
    name,
    category: 1,
    x: 1,
    y: yFor(j, papers.length),
    symbolSize: sizeFor(paperDegree[j]),
    label: { position: "right" },
  })),
];

const maxWeight = Math.max(...links.map((l) => l[2]));
const edges = links.map(([r, p, weight]) => ({
  source: `r${r}`,
  target: `p${p}`,
  lineStyle: {
    color: muted,
    width: 1 + (weight / maxWeight) * 4,
    opacity: 0.2 + (weight / maxWeight) * 0.35,
    curveness: 0.08,
  },
}));

// --- Init ---------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option ---------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "network-bipartite · javascript · echarts · anyplot.ai",
    left: "center",
    top: 24,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    data: ["Researchers", "Papers"],
    top: 78,
    left: "center",
    itemGap: 32,
    textStyle: { color: t.inkSoft, fontSize: 15 },
  },
  series: [
    {
      type: "graph",
      layout: "none",
      preserveAspect: "contain",
      roam: false,
      left: "16%",
      right: "16%",
      top: "16%",
      bottom: "8%",
      symbol: "circle",
      categories: [
        { name: "Researchers", itemStyle: { color: t.palette[0] } },
        { name: "Papers", itemStyle: { color: t.palette[1] } },
      ],
      label: {
        show: true,
        color: t.inkSoft,
        fontSize: 14,
        distance: 10,
      },
      itemStyle: { borderColor: t.pageBg, borderWidth: 2 },
      emphasis: { disabled: true },
      data: nodes,
      links: edges,
    },
  ],
});

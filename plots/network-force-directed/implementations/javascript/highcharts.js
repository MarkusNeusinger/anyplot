// anyplot.ai
// network-force-directed: Force-Directed Graph
// Library: highcharts 12.6.0 | JavaScript 22.23.0
// Quality: 87/100 | Created: 2026-07-01
//# anyplot-orientation: landscape
// anyplot.ai
// network-force-directed: Force-Directed Graph
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-07-01

const t = window.ANYPLOT_TOKENS;

// Deterministic 32-bit LCG for reproducible layout
let seed = 42;
function rand() {
  seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
  return seed / 4294967296;
}

// Five module communities — Imprint palette positions 0-4
const COMMUNITIES = [
  { label: 'Frontend', color: t.palette[0] },  // #009E73 brand green
  { label: 'Backend',  color: t.palette[1] },  // #C475FD lavender
  { label: 'Data',     color: t.palette[2] },  // #4467A3 blue
  { label: 'Infra',    color: t.palette[3] },  // #BD8233 ochre
  { label: 'Shared',   color: t.palette[4] },  // #AE3030 red
];

// Software module dependency network — 26 nodes
const nodes = [
  { id:  0, label: 'ui-kit',     group: 0 },
  { id:  1, label: 'router',     group: 0 },
  { id:  2, label: 'state',      group: 0 },
  { id:  3, label: 'forms',      group: 0 },
  { id:  4, label: 'charts',     group: 0 },
  { id:  5, label: 'i18n',       group: 0 },
  { id:  6, label: 'api',        group: 1 },
  { id:  7, label: 'auth',       group: 1 },
  { id:  8, label: 'db',         group: 1 },
  { id:  9, label: 'cache',      group: 1 },
  { id: 10, label: 'queue',      group: 1 },
  { id: 11, label: 'search',     group: 1 },
  { id: 12, label: 'analytics',  group: 2 },
  { id: 13, label: 'ml-train',   group: 2 },
  { id: 14, label: 'data-lake',  group: 2 },
  { id: 15, label: 'etl',        group: 2 },
  { id: 16, label: 'reports',    group: 2 },
  { id: 17, label: 'deploy',     group: 3 },
  { id: 18, label: 'monitor',    group: 3 },
  { id: 19, label: 'logging',    group: 3 },
  { id: 20, label: 'security',   group: 3 },
  { id: 21, label: 'ci-cd',      group: 3 },
  { id: 22, label: 'utils',      group: 4 },
  { id: 23, label: 'config',     group: 4 },
  { id: 24, label: 'validation', group: 4 },
  { id: 25, label: 'errors',     group: 4 },
];

// 52 dependency edges
const edges = [
  // Frontend internal
  [0, 1], [0, 2], [0, 3], [0, 4], [1, 2], [2, 3], [3, 5],
  // Backend internal
  [6, 7], [6, 8], [6, 9], [6, 10], [7, 8], [8, 9], [9, 10], [10, 11],
  // Data internal
  [12, 14], [13, 14], [14, 15], [12, 16], [15, 16],
  // Infra internal
  [17, 18], [17, 19], [18, 19], [17, 20], [19, 20], [17, 21], [21, 18],
  // Cross-community connections
  [0, 6], [2, 6], [4, 12], [6, 12], [6, 13], [8, 14], [6, 17], [7, 20], [12, 17],
  // Shared libraries used across communities
  [22, 0], [22, 6], [22, 12], [22, 17],
  [23, 0], [23, 6], [23, 12], [23, 17],
  [24, 3], [24, 7], [24, 6],
  [25, 6], [25, 7], [25, 19],
];

// Compute node degrees (number of connections per node)
const degrees = new Array(nodes.length).fill(0);
edges.forEach(([u, v]) => { degrees[u]++; degrees[v]++; });

// Fruchterman-Reingold force-directed layout in [5, 95]² coordinate space
const N = nodes.length;
const k = Math.sqrt((90 * 90) / N);
const pos = nodes.map(() => ({ x: 5 + rand() * 90, y: 5 + rand() * 90 }));

for (let iter = 0; iter < 500; iter++) {
  const temp = 15 * (1 - iter / 500) ** 2;
  const disp = Array.from({ length: N }, () => ({ x: 0, y: 0 }));

  // Repulsive forces between all node pairs
  for (let i = 0; i < N; i++) {
    for (let j = i + 1; j < N; j++) {
      const dx = pos[i].x - pos[j].x;
      const dy = pos[i].y - pos[j].y;
      const d = Math.sqrt(dx * dx + dy * dy) || 0.01;
      const f = k * k / d;
      disp[i].x += (dx / d) * f;
      disp[i].y += (dy / d) * f;
      disp[j].x -= (dx / d) * f;
      disp[j].y -= (dy / d) * f;
    }
  }

  // Attractive forces along edges
  edges.forEach(([u, v]) => {
    const dx = pos[u].x - pos[v].x;
    const dy = pos[u].y - pos[v].y;
    const d = Math.sqrt(dx * dx + dy * dy) || 0.01;
    const f = d * d / k;
    disp[u].x -= (dx / d) * f;
    disp[u].y -= (dy / d) * f;
    disp[v].x += (dx / d) * f;
    disp[v].y += (dy / d) * f;
  });

  // Apply displacements with temperature-based clamping and boundary enforcement
  for (let i = 0; i < N; i++) {
    const d = Math.sqrt(disp[i].x ** 2 + disp[i].y ** 2) || 0.01;
    const s = Math.min(d, temp) / d;
    pos[i].x = Math.max(5, Math.min(95, pos[i].x + disp[i].x * s));
    pos[i].y = Math.max(5, Math.min(95, pos[i].y + disp[i].y * s));
  }
}

// Theme-adaptive edge color (semi-transparent)
const edgeColor = window.ANYPLOT_THEME === 'light'
  ? 'rgba(74,74,68,0.28)'
  : 'rgba(184,183,176,0.28)';

// Degree lookup by label name for data label formatter
const degreeByName = {};
nodes.forEach(nd => { degreeByName[nd.label] = degrees[nd.id]; });

// Edges encoded as null-separated line segments (single series, rendered first/behind nodes)
const edgeData = edges.flatMap(([u, v]) => [
  { x: pos[u].x, y: pos[u].y },
  { x: pos[v].x, y: pos[v].y },
  null,
]);

// One scatter series per community — Imprint palette, nodes sized by degree
const nodeSeries = COMMUNITIES.map((comm, gi) => ({
  type: 'scatter',
  name: comm.label,
  color: comm.color,
  data: nodes
    .filter(nd => nd.group === gi)
    .map(nd => ({
      x: pos[nd.id].x,
      y: pos[nd.id].y,
      name: nd.label,
      marker: { radius: 4 + Math.min(degrees[nd.id], 9) },
    })),
  dataLabels: {
    enabled: true,
    formatter: function() {
      return (degreeByName[this.point.name] || 0) >= 4 ? this.point.name : null;
    },
    style: {
      color: t.inkSoft,
      fontSize: '11px',
      fontWeight: 'normal',
      textOutline: '2px ' + t.pageBg,
    },
    y: -24,
    verticalAlign: 'bottom',
    align: 'center',
  },
}));

Highcharts.chart('container', {
  chart: {
    type: 'scatter',
    backgroundColor: 'transparent',
    animation: false,
    style: { fontFamily: 'inherit' },
    plotBorderWidth: 0,
    margin: [72, 32, 64, 32],
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: 'network-force-directed · javascript · highcharts · anyplot.ai',
    style: { color: t.ink, fontSize: '22px', fontWeight: '600' },
    margin: 20,
  },
  xAxis: { min: 0, max: 100, visible: false, gridLineWidth: 0 },
  yAxis: {
    min: 0,
    max: 100,
    visible: false,
    gridLineWidth: 0,
    title: { text: null },
  },
  legend: {
    layout: 'horizontal',
    align: 'center',
    verticalAlign: 'bottom',
    itemStyle: { color: t.inkSoft, fontSize: '14px' },
    itemHoverStyle: { color: t.ink },
    symbolRadius: 6,
    symbolHeight: 12,
    symbolWidth: 12,
  },
  tooltip: {
    formatter: function() {
      return '<span style="color:' + this.color + '">●</span> <b>' + this.point.name + '</b>';
    },
    backgroundColor: t.elevatedBg,
    borderColor: t.grid,
    style: { color: t.ink, fontSize: '13px' },
  },
  plotOptions: {
    series: { animation: false },
    scatter: {
      marker: { symbol: 'circle' },
      states: { hover: { halo: { size: 0 } } },
    },
  },
  series: [
    // Edge layer drawn first so nodes render on top
    {
      type: 'line',
      name: 'Edges',
      showInLegend: false,
      enableMouseTracking: false,
      color: edgeColor,
      lineWidth: 1.5,
      marker: { enabled: false },
      data: edgeData,
    },
    ...nodeSeries,
  ],
});

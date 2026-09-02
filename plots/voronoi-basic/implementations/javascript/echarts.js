// anyplot.ai
// voronoi-basic: Voronoi Diagram for Spatial Partitioning
// Library: echarts 6.1.0 | JavaScript 22.23.2
// Quality: 90/100 | Created: 2026-09-02
//# anyplot-orientation: square
// anyplot.ai
// voronoi-basic: Voronoi Diagram for Spatial Partitioning
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data: retail store locations across a service region (km) -------------
function lcg(seed) {
  let state = seed;
  return () => {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);
const DOMAIN = 100;
const N_STORES = 14;
const stores = Array.from({ length: N_STORES }, () => ({
  x: 6 + rand() * (DOMAIN - 12),
  y: 6 + rand() * (DOMAIN - 12),
}));

// --- Voronoi cells: clip the bounding box against each pairwise bisector ---
function clipPolygon(poly, a, b, c) {
  const eps = 1e-9;
  const out = [];
  for (let i = 0; i < poly.length; i++) {
    const cur = poly[i];
    const nxt = poly[(i + 1) % poly.length];
    const fCur = a * cur[0] + b * cur[1] - c;
    const fNxt = a * nxt[0] + b * nxt[1] - c;
    const curIn = fCur <= eps;
    const nxtIn = fNxt <= eps;
    if (curIn) out.push(cur);
    if (curIn !== nxtIn) {
      const tt = fCur / (fCur - fNxt);
      out.push([cur[0] + tt * (nxt[0] - cur[0]), cur[1] + tt * (nxt[1] - cur[1])]);
    }
  }
  return out;
}

const BOUNDS = [
  [0, 0],
  [DOMAIN, 0],
  [DOMAIN, DOMAIN],
  [0, DOMAIN],
];
const cells = stores.map((p, i) => {
  let poly = BOUNDS;
  stores.forEach((q, j) => {
    if (i === j) return;
    const a = q.x - p.x;
    const b = q.y - p.y;
    const c = (q.x * q.x + q.y * q.y - p.x * p.x - p.y * p.y) / 2;
    poly = clipPolygon(poly, a, b, c);
  });
  return poly;
});

// --- Init ---------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Title (fontsize scaled to the descriptive-prefix length) --------------
const title = "Retail Store Service Areas · voronoi-basic · javascript · echarts · anyplot.ai";
const titleFontSize = Math.max(15, Math.round(22 * Math.min(1, 67 / title.length)));

// --- Option -----------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: title,
    left: "center",
    top: 36,
    textStyle: { color: t.ink, fontSize: titleFontSize, fontWeight: 500 },
  },
  grid: { left: 150, right: 150, top: 180, bottom: 120 },
  xAxis: {
    type: "value",
    min: 0,
    max: DOMAIN,
    name: "X coordinate (km)",
    nameLocation: "middle",
    nameGap: 46,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    min: 0,
    max: DOMAIN,
    name: "Y coordinate (km)",
    nameLocation: "middle",
    nameGap: 60,
    nameTextStyle: { color: t.ink, fontSize: 16 },
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    axisTick: { show: false },
    splitLine: { show: false },
  },
  series: [
    {
      type: "custom",
      coordinateSystem: "cartesian2d",
      silent: true,
      z: 1,
      renderItem: (params, api) => {
        const cell = cells[params.dataIndex];
        const points = cell.map((pt) => api.coord(pt));
        return {
          type: "polygon",
          shape: { points },
          style: {
            fill: t.palette[params.dataIndex % t.palette.length],
            opacity: 0.62,
            stroke: t.pageBg,
            lineWidth: 3,
          },
        };
      },
      data: stores.map((p) => [p.x, p.y]),
      encode: { x: 0, y: 1 },
    },
    {
      type: "scatter",
      data: stores.map((p) => [p.x, p.y]),
      symbolSize: 18,
      itemStyle: { color: t.ink, borderColor: t.pageBg, borderWidth: 2.5 },
      z: 3,
      silent: true,
    },
  ],
});

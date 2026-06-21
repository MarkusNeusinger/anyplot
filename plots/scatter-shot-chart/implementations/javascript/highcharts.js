// anyplot.ai
// scatter-shot-chart: Basketball Shot Chart
// Library: highcharts 12.6.0 | JavaScript 22.22.3
// Quality: 88/100 | Created: 2026-06-21

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// Fixed-seed LCG for deterministic data generation (no Math.random())
let _s = 42;
function rnd() {
  _s = (Math.imul(1664525, _s) + 1013904223) >>> 0;
  return _s / 4294967296;
}
function rn() { // standard normal via Box-Muller
  const u = rnd() || 1e-10;
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * rnd());
}

// --- Court geometry helper ---
function arc(cx, cy, r, a0, a1, steps) {
  const pts = [];
  for (let i = 0; i <= steps; i++) {
    const a = (a0 + (a1 - a0) * i / steps) * Math.PI / 180;
    pts.push([+(cx + r * Math.cos(a)).toFixed(3), +(cy + r * Math.sin(a)).toFixed(3)]);
  }
  return pts;
}

// --- NBA half-court dimensions (feet, basket at origin) ---
const BL = -4.75;                                    // baseline Y
const HC = 42.25;                                    // half-court line Y
const CY = Math.sqrt(23.75 * 23.75 - 22 * 22);      // three-point corner Y ≈ 8.95
const A0 = Math.atan2(CY,  22) * 180 / Math.PI;     // arc start angle ≈ 22.1°
const A1 = Math.atan2(CY, -22) * 180 / Math.PI;     // arc end angle  ≈ 157.9°

// Court line series template (neutral ink-soft colour so shots stand out)
const CL = {
  type: 'line',
  color: t.inkSoft,
  lineWidth: 2,
  marker: { enabled: false },
  enableMouseTracking: false,
  showInLegend: false,
  states: { hover: { enabled: false } },
};

const courtSeries = [
  // Outer half-court boundary
  { ...CL, data: [[-25, BL], [25, BL], [25, HC], [-25, HC], [-25, BL]] },
  // Three-point corners (straight segments)
  { ...CL, data: [[-22, BL], [-22, CY]] },
  { ...CL, data: [[22, BL],  [22, CY]] },
  // Three-point arc
  { ...CL, data: arc(0, 0, 23.75, A0, A1, 60) },
  // Paint / key rectangle (sides + free-throw end)
  { ...CL, data: [[-8, BL], [-8, 15], [8, 15], [8, BL]] },
  // Free-throw circle — upper half (solid, away from basket)
  { ...CL, data: arc(0, 15, 6, 0, 180, 40) },
  // Free-throw circle — lower half (dashed, toward basket)
  { ...CL, dashStyle: 'Dash', data: arc(0, 15, 6, 180, 360, 40) },
  // Restricted area (4 ft arc from basket)
  { ...CL, data: arc(0, 0, 4, 0, 180, 30) },
  // Backboard
  { ...CL, lineWidth: 3, data: [[-3, -1.5], [3, -1.5]] },
  // Basket rim (small circle)
  { ...CL, lineWidth: 2, data: arc(0, 0, 0.75, 0, 360, 36) },
];

// --- Shot data generation: type drives marker shape (● 2PT · △ 3PT · ■ FT) ---
const shots = { made2: [], missed2: [], made3: [], missed3: [], madeFT: [], missedFT: [] };

function addShots(n, cx, cy, sx, sy, pct, type) {
  for (let i = 0; i < n; i++) {
    const x = Math.max(-24, Math.min(24, cx + rn() * sx));
    const y = Math.max(BL + 0.5, Math.min(41, cy + rn() * sy));
    const key = (rnd() < pct ? 'made' : 'missed') + type;
    shots[key].push([+x.toFixed(2), +y.toFixed(2)]);
  }
}

addShots(80,  0,    3,    2.5, 2,   0.65, '2');  // under basket
addShots(45, -13,  12,   3,   3,   0.42, '2');  // left mid-range
addShots(45,  13,  12,   3,   3,   0.42, '2');  // right mid-range
addShots(30,  0,   17,   3.5, 2,   0.44, '2');  // top of key
addShots(40, -22,   4,   1.5, 2.5, 0.38, '3');  // left corner three
addShots(40,  22,   4,   1.5, 2.5, 0.38, '3');  // right corner three
addShots(35, -18,  22,   2,   2,   0.36, '3');  // left above-break three
addShots(35,  18,  22,   2,   2,   0.36, '3');  // right above-break three
addShots(35,  0,   24,   4,   2,   0.35, '3');  // top-of-arc three
addShots(22,  0,   15,   0.4, 0.3, 0.78, 'FT'); // free throws (~78% NBA avg)

// --- Chart ---
Highcharts.chart("container", {
  chart: {
    type: 'scatter',
    backgroundColor: 'transparent',
    animation: false,
    style: { fontFamily: 'inherit' },
    margin: [90, 30, 55, 30],
  },
  credits: { enabled: false },
  colors: t.palette,
  title: {
    text: 'scatter-shot-chart · javascript · highcharts · anyplot.ai',
    style: { color: t.ink, fontSize: '22px', fontWeight: '600' },
  },
  subtitle: {
    text: '● 2-pointer · △ 3-pointer · ■ free-throw',
    style: { color: t.inkSoft, fontSize: '13px' },
  },
  xAxis: {
    min: -26, max: 26,
    lineColor: 'transparent',
    tickColor: 'transparent',
    gridLineColor: 'transparent',
    labels: { enabled: false },
    title: { enabled: false },
  },
  yAxis: {
    min: -6, max: 46,
    lineColor: 'transparent',
    tickColor: 'transparent',
    gridLineColor: 'transparent',
    labels: { enabled: false },
    title: { text: null },
  },
  legend: {
    enabled: true,
    itemStyle: { color: t.inkSoft, fontSize: '14px', fontWeight: 'normal' },
    itemHoverStyle: { color: t.ink },
    symbolRadius: 4,
    verticalAlign: 'bottom',
    align: 'center',
  },
  tooltip: { enabled: false },
  plotOptions: {
    series: { animation: false },
    scatter: {
      marker: { radius: 5, lineWidth: 1, lineColor: t.pageBg },
    },
  },
  series: [
    ...courtSeries,
    // Made shots — brand green (#009E73); shape encodes shot type; only first shown in legend
    {
      type: 'scatter', name: 'Made', data: shots.made2,
      color: t.palette[0], opacity: 0.80,
      marker: { radius: 5, symbol: 'circle', lineWidth: 1, lineColor: t.pageBg },
    },
    {
      type: 'scatter', name: 'Made 3PT', data: shots.made3,
      color: t.palette[0], opacity: 0.80, showInLegend: false,
      marker: { radius: 5, symbol: 'triangle', lineWidth: 1, lineColor: t.pageBg },
    },
    {
      type: 'scatter', name: 'Made FT', data: shots.madeFT,
      color: t.palette[0], opacity: 0.80, showInLegend: false,
      marker: { radius: 5, symbol: 'square', lineWidth: 1, lineColor: t.pageBg },
    },
    // Missed shots — matte red (#AE3030); shape encodes shot type; only first shown in legend
    {
      type: 'scatter', name: 'Missed', data: shots.missed2,
      color: t.palette[4], opacity: 0.70,
      marker: { radius: 5, symbol: 'circle', lineWidth: 1, lineColor: t.pageBg },
    },
    {
      type: 'scatter', name: 'Missed 3PT', data: shots.missed3,
      color: t.palette[4], opacity: 0.70, showInLegend: false,
      marker: { radius: 5, symbol: 'triangle', lineWidth: 1, lineColor: t.pageBg },
    },
    {
      type: 'scatter', name: 'Missed FT', data: shots.missedFT,
      color: t.palette[4], opacity: 0.70, showInLegend: false,
      marker: { radius: 5, symbol: 'square', lineWidth: 1, lineColor: t.pageBg },
    },
  ],
});

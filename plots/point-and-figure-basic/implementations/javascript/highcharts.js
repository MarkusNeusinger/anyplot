// anyplot.ai
// point-and-figure-basic: Point and Figure Chart
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data: synthetic daily closes over ~1 trading year (deterministic LCG) -
function lcg(seed) {
  let state = seed;
  return function rand() {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(42);

// Short alternating-direction legs (strict sign flip each leg) so the box
// conversion below produces a genuine zigzag of many columns instead of one
// long trend per macro regime.
const NUM_LEGS = 20;
let dir = 1;
const segments = [];
for (let s = 0; s < NUM_LEGS; s++) {
  const days = 8 + Math.floor(rand() * 8); // 8-15 trading days per leg
  const magnitude = 0.7 + rand() * 0.9; // 0.7-1.6 drift per day
  segments.push({ days, drift: dir * magnitude, vol: 1.6 + rand() * 0.8 });
  dir *= -1;
}

let price = 148;
const closes = [];
segments.forEach(({ days, drift, vol }) => {
  for (let i = 0; i < days; i++) {
    price += drift + (rand() - 0.5) * vol;
    closes.push(Math.max(price, 5));
  }
});

// --- Point & figure box conversion (close-only, classic 1-box / 3-box rule) -
const BOX_SIZE = 2;
const REVERSAL_BOXES = 3;
const boxOf = (p) => Math.round(p / BOX_SIZE);

function buildColumns(prices) {
  const boxes = prices.map(boxOf);
  const columns = [];
  let direction = 0; // 0 undetermined, 1 = X column (rising), -1 = O column (falling)
  let currentBox = boxes[0];
  let column = { direction: 0, boxes: [currentBox] };

  for (let i = 1; i < boxes.length; i++) {
    const box = boxes[i];
    if (direction === 0) {
      if (box > currentBox) {
        for (let b = currentBox + 1; b <= box; b++) column.boxes.push(b);
        column.direction = 1;
        direction = 1;
        currentBox = box;
      } else if (box < currentBox) {
        for (let b = currentBox - 1; b >= box; b--) column.boxes.push(b);
        column.direction = -1;
        direction = -1;
        currentBox = box;
      }
    } else if (direction === 1) {
      if (box > currentBox) {
        for (let b = currentBox + 1; b <= box; b++) column.boxes.push(b);
        currentBox = box;
      } else if (box <= currentBox - REVERSAL_BOXES) {
        columns.push(column);
        column = { direction: -1, boxes: [] };
        for (let b = currentBox - 1; b >= box; b--) column.boxes.push(b);
        direction = -1;
        currentBox = box;
      }
    } else {
      if (box < currentBox) {
        for (let b = currentBox - 1; b >= box; b--) column.boxes.push(b);
        currentBox = box;
      } else if (box >= currentBox + REVERSAL_BOXES) {
        columns.push(column);
        column = { direction: 1, boxes: [] };
        for (let b = currentBox + 1; b <= box; b++) column.boxes.push(b);
        direction = 1;
        currentBox = box;
      }
    }
  }
  columns.push(column);
  return columns.filter((c) => c.boxes.length > 0);
}

const columns = buildColumns(closes);

// --- Series points: one scatter series per symbol; dataLabels ARE the glyph -
const xPoints = [];
const oPoints = [];
columns.forEach((col, colIndex) => {
  col.boxes.forEach((box) => {
    const point = [colIndex, box * BOX_SIZE];
    if (col.direction === 1) xPoints.push(point);
    else oPoints.push(point);
  });
});

// --- 45-degree support / resistance projections (1 box per column) ---------
let support = { col: 0, box: Infinity };
let resistance = { col: 0, box: -Infinity };
columns.forEach((col, colIndex) => {
  const low = Math.min(...col.boxes);
  const high = Math.max(...col.boxes);
  if (low < support.box) support = { col: colIndex, box: low };
  if (high > resistance.box) resistance = { col: colIndex, box: high };
});
const lastCol = columns.length - 1;
const span = Math.min(12, lastCol - Math.min(support.col, resistance.col));
const supportLine = Array.from({ length: span + 1 }, (_, i) => [support.col + i, (support.box + i) * BOX_SIZE]).filter(
  ([x]) => x <= lastCol,
);
const resistanceLine = Array.from({ length: span + 1 }, (_, i) => [
  resistance.col + i,
  (resistance.box - i) * BOX_SIZE,
]).filter(([x]) => x <= lastCol);

// --- Chart -------------------------------------------------------------------
// Semantic exception (default-style-guide.md): bullish/bearish reads as
// green/red to any trader, so X columns keep the brand green (palette
// position 1) and O columns use the matte-red semantic anchor rather than
// the next ordinal palette slot.
const RISING = t.palette[0];
const FALLING = "#AE3030";
const tickStep = Math.max(1, Math.ceil((lastCol + 1) / 15));

Highcharts.chart("container", {
  chart: {
    type: "scatter",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "point-and-figure-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: `Box size $${BOX_SIZE} · ${REVERSAL_BOXES}-box reversal`,
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: {
      text: "Column (price reversals — not time)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    min: -0.5,
    max: lastCol + 0.5,
    tickInterval: tickStep,
    gridLineWidth: 0,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  yAxis: {
    title: { text: "Price ($)", style: { color: t.inkSoft, fontSize: "16px" } },
    tickInterval: BOX_SIZE,
    gridLineColor: t.grid,
    lineColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    headerFormat: "",
    pointFormat: "Column {point.x} · ${point.y}",
  },
  plotOptions: {
    series: { animation: false },
    scatter: {
      marker: { enabled: false },
      dataLabels: {
        enabled: true,
        allowOverlap: true,
        verticalAlign: "middle",
        align: "center",
        y: 1,
        style: { fontWeight: "700", fontSize: "16px", textOutline: "none" },
      },
    },
  },
  series: [
    {
      name: "Rising (X)",
      type: "scatter",
      data: xPoints,
      color: RISING,
      dataLabels: { format: "X", style: { color: RISING } },
    },
    {
      name: "Falling (O)",
      type: "scatter",
      data: oPoints,
      color: FALLING,
      dataLabels: { format: "O", style: { color: FALLING } },
    },
    {
      name: "Support (45°)",
      type: "line",
      data: supportLine,
      color: t.inkSoft,
      dashStyle: "Dash",
      lineWidth: 2,
      marker: { enabled: false },
      enableMouseTracking: false,
      showInLegend: false,
    },
    {
      name: "Resistance (45°)",
      type: "line",
      data: resistanceLine,
      color: t.inkSoft,
      dashStyle: "Dash",
      lineWidth: 2,
      marker: { enabled: false },
      enableMouseTracking: false,
      showInLegend: false,
    },
  ],
});

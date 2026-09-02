// anyplot.ai
// kagi-basic: Basic Kagi Chart
// Library: echarts 6.1.0 | JavaScript 22
// Quality: pending | Created: 2026-09-02
//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Daily closing prices via a fixed-seed LCG random walk with mild upward drift.
const makeRng = (seed) => {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
};
const rand = makeRng(42);

const numObservations = 260;
const closePrices = [128.5];
for (let i = 1; i < numObservations; i++) {
  const u1 = Math.max(rand(), 1e-9);
  const u2 = rand();
  const z = Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  const drift = 0.0005;
  const volatility = 0.017;
  closePrices.push(closePrices[i - 1] * (1 + drift + volatility * z));
}

// --- Kagi construction: reversal-threshold swing filter ---------------------
// A new Kagi column only forms once price moves `reversalPct` against the
// current trend; small moves within the threshold are absorbed into the
// running high/low, filtering out time-based noise.
const reversalPct = 0.04;

const kagiColumns = [];
let columnBase = closePrices[0];
let direction = null;
let extreme = closePrices[0];
for (let i = 1; i < closePrices.length; i++) {
  const price = closePrices[i];
  if (direction === null) {
    if (price >= columnBase * (1 + reversalPct)) {
      direction = "up";
      extreme = price;
    } else if (price <= columnBase * (1 - reversalPct)) {
      direction = "down";
      extreme = price;
    }
    continue;
  }
  if (direction === "up") {
    if (price > extreme) {
      extreme = price;
    } else if (price <= extreme * (1 - reversalPct)) {
      kagiColumns.push({ dir: "up", from: columnBase, to: extreme });
      columnBase = extreme;
      direction = "down";
      extreme = price;
    }
  } else {
    if (price < extreme) {
      extreme = price;
    } else if (price >= extreme * (1 + reversalPct)) {
      kagiColumns.push({ dir: "down", from: columnBase, to: extreme });
      columnBase = extreme;
      direction = "up";
      extreme = price;
    }
  }
}
kagiColumns.push({ dir: direction || "up", from: columnBase, to: extreme });

// Flatten columns into drawable segments: one vertical bar per column (yang
// thick/green on up-swings, yin thin/red on down-swings) plus the horizontal
// shoulder/waist connecting each column to the next at the reversal price.
const segments = [];
for (let i = 0; i < kagiColumns.length; i++) {
  const y0 = i === 0 ? kagiColumns[0].from : kagiColumns[i - 1].to;
  const y1 = kagiColumns[i].to;
  segments.push({ kind: "v", x: i, y0, y1, dir: kagiColumns[i].dir });
  if (i < kagiColumns.length - 1) {
    segments.push({ kind: "h", x0: i, x1: i + 1, y: y1, dir: kagiColumns[i].dir });
  }
}

const allPrices = kagiColumns.flatMap((c) => [c.from, c.to]);
const priceMin = Math.min(...allPrices);
const priceMax = Math.max(...allPrices);
const pricePad = (priceMax - priceMin) * 0.08;

// --- Init --------------------------------------------------------------------
const chart = echarts.init(document.getElementById("container"));

// --- Option --------------------------------------------------------------------
chart.setOption({
  animation: false,
  backgroundColor: "transparent",
  title: {
    text: "kagi-basic · javascript · echarts · anyplot.ai",
    left: "center",
    top: 40,
    textStyle: { color: t.ink, fontSize: 22, fontWeight: 500 },
  },
  legend: {
    data: ["Yang (Uptrend)", "Yin (Downtrend)"],
    top: 95,
    left: "center",
    itemGap: 48,
    itemWidth: 26,
    itemHeight: 14,
    textStyle: { color: t.ink, fontSize: 16 },
  },
  grid: { left: 120, right: 70, top: 165, bottom: 100 },
  xAxis: {
    type: "value",
    name: "Kagi Line Index",
    nameLocation: "middle",
    nameGap: 45,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    min: -0.5,
    max: kagiColumns.length - 0.5,
    axisLabel: { color: t.inkSoft, fontSize: 14 },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { show: false },
  },
  yAxis: {
    type: "value",
    name: "Price ($)",
    nameLocation: "middle",
    nameGap: 70,
    nameTextStyle: { color: t.inkSoft, fontSize: 16 },
    min: priceMin - pricePad,
    max: priceMax + pricePad,
    axisLabel: { color: t.inkSoft, fontSize: 14, formatter: (v) => `$${v.toFixed(0)}` },
    axisLine: { lineStyle: { color: t.inkSoft } },
    splitLine: { lineStyle: { color: t.grid } },
  },
  series: [
    {
      name: "Yang (Uptrend)",
      type: "line",
      data: [],
      showSymbol: false,
      lineStyle: { color: t.palette[0], width: 7 },
      itemStyle: { color: t.palette[0] },
    },
    {
      name: "Yin (Downtrend)",
      type: "line",
      data: [],
      showSymbol: false,
      lineStyle: { color: t.palette[4], width: 2.5 },
      itemStyle: { color: t.palette[4] },
    },
    {
      name: "Kagi",
      type: "custom",
      encode: { x: 0, y: 1 },
      data: segments.map((s) =>
        s.kind === "v" ? [s.x, (s.y0 + s.y1) / 2] : [(s.x0 + s.x1) / 2, s.y]
      ),
      renderItem: (params, api) => {
        const seg = segments[params.dataIndex];
        const color = seg.dir === "up" ? t.palette[0] : t.palette[4];
        const lineWidth = seg.dir === "up" ? 7 : 2.5;
        const p0 = seg.kind === "v" ? api.coord([seg.x, seg.y0]) : api.coord([seg.x0, seg.y]);
        const p1 = seg.kind === "v" ? api.coord([seg.x, seg.y1]) : api.coord([seg.x1, seg.y]);
        return {
          type: "line",
          shape: { x1: p0[0], y1: p0[1], x2: p1[0], y2: p1[1] },
          style: { stroke: color, lineWidth },
        };
      },
    },
  ],
});

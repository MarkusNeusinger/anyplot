// anyplot.ai
// kagi-basic: Basic Kagi Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// Quality: 89/100 | Created: 2026-09-02

const t = window.ANYPLOT_TOKENS;

// --- Data: synthetic Brent crude oil daily close, USD/bbl (deterministic LCG) ---
function lcg(seed) {
  let state = seed;
  return function next() {
    state = (state * 1664525 + 1013904223) % 4294967296;
    return state / 4294967296;
  };
}
const rand = lcg(20260902);

const n = 260;
const closes = [];
let price = 74;
let momentum = 0;
for (let i = 0; i < n; i++) {
  momentum = momentum * 0.82 + (rand() - 0.5) * 2.6;
  price = Math.max(38, price + momentum);
  closes.push(Math.round(price * 100) / 100);
}

// --- Kagi construction: collapse the close series into turning-point vertices ---
const REVERSAL = 0.04; // 4% reversal threshold

const vertices = [closes[0]];
let dir = null; // "up" | "down"
let extreme = closes[0];
for (let i = 1; i < closes.length; i++) {
  const p = closes[i];
  if (dir === null) {
    if ((p - closes[0]) / closes[0] >= REVERSAL) {
      dir = "up";
      extreme = p;
    } else if ((closes[0] - p) / closes[0] >= REVERSAL) {
      dir = "down";
      extreme = p;
    }
    continue;
  }
  if (dir === "up") {
    if (p >= extreme) {
      extreme = p;
    } else if ((extreme - p) / extreme >= REVERSAL) {
      vertices.push(extreme);
      dir = "down";
      extreme = p;
    }
  } else {
    if (p <= extreme) {
      extreme = p;
    } else if ((p - extreme) / extreme >= REVERSAL) {
      vertices.push(extreme);
      dir = "up";
      extreme = p;
    }
  }
}
vertices.push(extreme);

// --- Yang/yin classification: thickness flips only when a column breaks the
// prior same-direction extreme (the last shoulder for up, the last waist for down) ---
let thick = null;
const segments = [];
for (let i = 1; i < vertices.length; i++) {
  const goingUp = vertices[i] > vertices[i - 1];
  if (i === 1) {
    thick = goingUp;
  } else {
    const priorExtreme = vertices[i - 2];
    if (goingUp && vertices[i] > priorExtreme) thick = true;
    else if (!goingUp && vertices[i] < priorExtreme) thick = false;
  }
  segments.push({
    data: [
      [i - 1, vertices[i - 1]],
      [i, vertices[i]],
    ],
    thick,
  });
}

const YANG = t.palette[0]; // "#009E73" brand green — uptrend breakout
const YIN = t.palette[4]; // "#AE3030" matte red — downtrend breakdown

// --- Standout-move callout: find the single largest vertex-to-vertex swing
// and shade its column with a plotBand tinted in its own yang/yin color, so
// the reader's eye lands on the move that matters most, not just the trend ---
let standout = segments[0];
let standoutDelta = 0;
for (const seg of segments) {
  const delta = Math.abs(seg.data[1][1] - seg.data[0][1]);
  if (delta > standoutDelta) {
    standoutDelta = delta;
    standout = seg;
  }
}
const standoutUp = standout.data[1][1] > standout.data[0][1];
const standoutLabel =
  "Standout " + (standoutUp ? "breakout: +$" : "breakdown: -$") + standoutDelta.toFixed(2);

// --- Chart ---------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "line",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "kagi-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Brent crude oil, synthetic daily close · 4% reversal threshold",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: { text: "Kagi Line Index", style: { color: t.inkSoft, fontSize: "16px" } },
    allowDecimals: false,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    plotBands: [
      {
        from: standout.data[0][0],
        to: standout.data[1][0],
        color: Highcharts.color(standoutUp ? YANG : YIN)
          .setOpacity(0.14)
          .get(),
        label: {
          text: standoutLabel,
          style: { color: t.ink, fontSize: "12px", fontWeight: "600" },
          align: "center",
          verticalAlign: "top",
          y: 14,
        },
      },
    ],
  },
  yAxis: {
    title: {
      text: "Brent Crude Oil Price (USD/bbl)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
  },
  legend: {
    enabled: true,
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: {
    enabled: true,
    formatter: function formatTooltip() {
      return "Line " + this.point.x + "<br>$" + this.point.y.toFixed(2);
    },
  },
  plotOptions: {
    series: { animation: false, marker: { enabled: false }, enableMouseTracking: true },
  },
  series: [
    ...segments.map((seg) => ({
      type: "line",
      step: "left",
      data: seg.data,
      color: seg.thick ? YANG : YIN,
      lineWidth: seg.thick ? 6 : 2,
      showInLegend: false,
    })),
    {
      name: "Yang (breaks prior high)",
      type: "line",
      color: YANG,
      lineWidth: 6,
      data: [],
      showInLegend: true,
      enableMouseTracking: false,
    },
    {
      name: "Yin (breaks prior low)",
      type: "line",
      color: YIN,
      lineWidth: 2,
      data: [],
      showInLegend: true,
      enableMouseTracking: false,
    },
  ],
});

//# anyplot-orientation: landscape
// anyplot.ai
// streamgraph-basic: Basic Stream Graph
// Library: Highcharts 12.6.0 | Node 22
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-05

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Monthly subscriber base (millions) for 5 streaming platforms over 3 years —
// some rise, some fade, one is flat, so the stack shows genuine hand-off
// between layers instead of everything drifting in the same direction.
const platforms = ["Streamly", "Wavecast", "Orbit", "Nimbus", "Pulse"];
const monthCount = 36;
const monthLabels = [];
for (let m = 0; m < monthCount; m++) {
  const year = 2022 + Math.floor(m / 12);
  const label = new Date(Date.UTC(year, m % 12, 1)).toLocaleString("en-US", {
    month: "short",
  });
  monthLabels.push(`${label} '${String(year).slice(2)}`);
}

// Small deterministic LCG so the wobble is reproducible without a real RNG.
let seed = 42;
function rand() {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return seed / 2147483648;
}

const platformParams = [
  { base: 28, trend: 0.75, amp: 6, phase: 0.3 }, // Streamly — steady grower
  { base: 20, trend: 1.05, amp: 5, phase: 1.6 }, // Wavecast — fast riser
  { base: 34, trend: -0.55, amp: 7, phase: 2.4 }, // Orbit — fading incumbent
  { base: 14, trend: 0.1, amp: 8, phase: 4.2 }, // Nimbus — seasonal, flat trend
  { base: 10, trend: 0.35, amp: 3, phase: 5.4 }, // Pulse — small, slow climb
];

const seriesData = platformParams.map((p) => []);
for (let m = 0; m < monthCount; m++) {
  platformParams.forEach((p, i) => {
    const seasonal = p.amp * Math.sin(m / 4.5 + p.phase);
    const noise = (rand() - 0.5) * 2.5;
    const value = Math.max(2, p.base + p.trend * m + seasonal + noise);
    seriesData[i].push(Math.round(value * 10) / 10);
  });
}

// Hidden baseline series shifts the whole stack down by half the per-month
// total. Core Highcharts has no built-in "stream" stacking offset (that shift
// lives in the streamgraph module, which isn't loaded — only the core bundle
// is vendored), so the symmetric center is faked with an invisible first
// stacked series: its band (0 → -total/2) is fully transparent, and the real
// platform bands stack on top of it from -total/2 up to +total/2.
const baselineData = [];
for (let m = 0; m < monthCount; m++) {
  let total = 0;
  for (let i = 0; i < seriesData.length; i++) total += seriesData[i][m];
  baselineData.push(-total / 2);
}

// --- Chart -------------------------------------------------------------------
Highcharts.chart("container", {
  chart: {
    type: "areaspline",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "streamgraph-basic · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Monthly subscriber base by streaming platform (millions)",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    categories: monthLabels,
    tickInterval: 3,
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    gridLineColor: "transparent",
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    title: {
      text: "Month (2022–2024)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
  },
  yAxis: {
    visible: false,
    startOnTick: false,
    endOnTick: false,
  },
  legend: {
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  tooltip: { shared: true, valueSuffix: "M subscribers" },
  plotOptions: {
    series: {
      animation: false,
      stacking: "normal",
      marker: { enabled: false },
      lineWidth: 1.5,
      lineColor: t.pageBg,
    },
    areaspline: { fillOpacity: 0.92 },
  },
  series: [
    {
      name: "baseline",
      data: baselineData,
      color: "transparent",
      fillOpacity: 0,
      lineWidth: 0,
      enableMouseTracking: false,
      showInLegend: false,
    },
    ...platforms.map((name, i) => ({
      name,
      data: seriesData[i],
      color: t.palette[i],
    })),
  ],
});

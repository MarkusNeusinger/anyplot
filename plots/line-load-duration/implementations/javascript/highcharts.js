// anyplot.ai
// line-load-duration: Load Duration Curve for Energy Systems
// Library: highcharts 12.6.0 | JavaScript 22.22.3
// Quality: 88/100 | Created: 2026-06-10

//# anyplot-orientation: landscape

const t = window.ANYPLOT_TOKENS;

// Deterministic LCG — browser has no seeded Math.random
let _seed = 42;
function rand() {
  _seed = (_seed * 1664525 + 1013904223) >>> 0;
  return _seed / 4294967296;
}

// Generate 8760 hourly loads (MW) with seasonal + morning/evening peak patterns
const rawLoads = Array.from({length: 8760}, (_, h) => {
  const dayOfYear = Math.floor(h / 24);
  const hourOfDay = h % 24;
  const seasonal = 200 * Math.cos(2 * Math.PI * dayOfYear / 365);
  const morning  = 250 * Math.exp(-0.5 * Math.pow((hourOfDay - 9) / 2, 2));
  const evening  = 220 * Math.exp(-0.5 * Math.pow((hourOfDay - 19) / 2, 2));
  const noise    = 60 * (rand() * 2 - 1);
  return 700 + seasonal + morning + evening + noise;
});

// Sort descending to form the load duration curve
rawLoads.sort((a, b) => b - a);

// Generation capacity thresholds (MW)
const BASE_CAP  = 600;
const INTER_CAP = 900;
const PEAK_CAP  = 1200;

// Find hour indices where load first drops below each threshold
const interHour = rawLoads.findIndex(v => v < INTER_CAP);
const baseHour  = rawLoads.findIndex(v => v < BASE_CAP);

// Stacked series data — each layer's sum equals the total load
const baseData  = rawLoads.map(v => Math.min(v, BASE_CAP));
const interData = rawLoads.map(v => Math.max(0, Math.min(v, INTER_CAP) - BASE_CAP));
const peakData  = rawLoads.map(v => Math.max(0, v - INTER_CAP));

// Total annual energy (sum of hourly MWh → TWh)
const totalTWh = rawLoads.reduce((s, v) => s + v, 0) / 1e6;

// Semantic colors: green = base (always-on), ochre = intermediate, red = peak (critical)
const GREEN = t.palette[0];  // #009E73
const OCHRE = t.palette[3];  // #BD8233
const RED   = t.palette[4];  // #AE3030

Highcharts.chart("container", {
  chart: {
    type: "area",
    backgroundColor: "transparent",
    animation: false,
    style: { fontFamily: "inherit" },
  },
  credits: { enabled: false },
  title: {
    text: "line-load-duration · javascript · highcharts · anyplot.ai",
    style: { color: t.ink, fontSize: "22px", fontWeight: "600" },
  },
  subtitle: {
    text: "Total annual energy consumption: " + totalTWh.toFixed(2) + " TWh",
    style: { color: t.inkSoft, fontSize: "14px" },
  },
  xAxis: {
    title: {
      text: "Hours of the Year (sorted by descending demand)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    lineColor: t.inkSoft,
    tickColor: t.inkSoft,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    // Vertical dashed dividers at region boundaries
    plotLines: [
      { value: interHour, color: t.inkSoft, dashStyle: "ShortDash", width: 1, zIndex: 3 },
      { value: baseHour,  color: t.inkSoft, dashStyle: "ShortDash", width: 1, zIndex: 3 },
    ],
    // Region labels — y offset positions label within its respective colored band
    plotBands: [
      {
        from: 0, to: interHour, color: "transparent",
        label: {
          text: "Peak Load",
          style: { color: RED, fontSize: "14px", fontWeight: "700" },
          align: "center", y: 180,
        },
      },
      {
        from: interHour, to: baseHour, color: "transparent",
        label: {
          text: "Intermediate Load",
          style: { color: OCHRE, fontSize: "14px", fontWeight: "700" },
          align: "center", x: -260, y: 360,
        },
      },
      {
        from: baseHour, to: 8760, color: "transparent",
        label: {
          text: "Base Load",
          style: { color: GREEN, fontSize: "14px", fontWeight: "700" },
          align: "center", y: 560,
        },
      },
    ],
  },
  yAxis: {
    min: 0,
    max: 1300,
    title: {
      text: "Power Demand (MW)",
      style: { color: t.inkSoft, fontSize: "16px" },
    },
    gridLineColor: t.grid,
    labels: { style: { color: t.inkSoft, fontSize: "14px" } },
    // Horizontal dashed lines at capacity tiers
    plotLines: [
      {
        value: BASE_CAP,
        color: GREEN,
        dashStyle: "Dash",
        width: 2,
        zIndex: 4,
        label: {
          text: "Base capacity — " + BASE_CAP + " MW",
          style: { color: GREEN, fontSize: "13px", fontWeight: "600" },
          align: "right",
          x: -5,
          y: -6,
        },
      },
      {
        value: INTER_CAP,
        color: OCHRE,
        dashStyle: "Dash",
        width: 2,
        zIndex: 4,
        label: {
          text: "Intermediate capacity — " + INTER_CAP + " MW",
          style: { color: OCHRE, fontSize: "13px", fontWeight: "600" },
          align: "right",
          x: -5,
          y: -6,
        },
      },
      {
        value: PEAK_CAP,
        color: RED,
        dashStyle: "Dash",
        width: 2,
        zIndex: 4,
        label: {
          text: "Peak capacity — " + PEAK_CAP + " MW",
          style: { color: RED, fontSize: "13px", fontWeight: "600" },
          align: "right",
          x: -5,
          y: -6,
        },
      },
    ],
  },
  legend: {
    enabled: true,
    itemStyle: { color: t.inkSoft, fontSize: "14px" },
    itemHoverStyle: { color: t.ink },
  },
  plotOptions: {
    series: { animation: false, turboThreshold: 0 },
    area: {
      stacking: "normal",
      lineWidth: 0,
      marker: { enabled: false },
      fillOpacity: 0.88,
    },
  },
  series: [
    {
      name: "Base Load",
      data: baseData,
      color: GREEN,
    },
    {
      name: "Intermediate Load",
      data: interData,
      color: OCHRE,
    },
    {
      name: "Peak Load",
      data: peakData,
      color: RED,
    },
    {
      type: "line",
      name: "Load Duration Curve",
      data: rawLoads,
      color: t.ink,
      lineWidth: 1.5,
      marker: { enabled: false },
      showInLegend: false,
      enableMouseTracking: false,
      zIndex: 10,
    },
  ],
});

// anyplot.ai
// spiral-timeseries: Spiral Time Series Chart
// Library: highcharts 12.6.0 | JavaScript 22.23.2
// License: Highcharts — commercial license, free for non-commercial use (highcharts.com/license)
// Quality: pending | Created: 2026-08-17

//# anyplot-orientation: square

const t = window.ANYPLOT_TOKENS;

// --- Data (in-memory, deterministic) ----------------------------------------
// Daily average temperature over 4 years, unrolled onto an Archimedean spiral
// — one full revolution per year — so the same season from different years
// lines up along the same spoke. The core Highcharts bundle has no polar-chart
// support (see prompts/library/highcharts.md: polar lives in highcharts-more,
// which isn't loaded), so the spiral geometry is computed by hand and plotted
// as a plain Cartesian scatter/line pair with the axes hidden.
let lcgState = 42;
function nextRandom() {
  lcgState = (lcgState * 1103515245 + 12345) % 2147483648;
  return lcgState / 2147483648;
}

const MONTH_LABELS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const MONTH_STARTS = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]; // day-of-year (non-leap)
const DAYS_PER_YEAR = 365;
const YEARS = 4;
const START_YEAR = 2021;

const BASE_RADIUS = 55; // center hole so the first days aren't crowded at a point
const RADIUS_PER_CYCLE = 135; // constant spacing between revolutions (Archimedean)

function monthOfDay(dayOfYear) {
  let month = 11;
  for (let i = 1; i < 12; i++) {
    if (dayOfYear < MONTH_STARTS[i]) {
      month = i - 1;
      break;
    }
  }
  return month;
}

const spiralPoints = [];
let minTemp = Infinity;
let maxTemp = -Infinity;

for (let cycle = 0; cycle < YEARS; cycle++) {
  for (let day = 0; day < DAYS_PER_YEAR; day++) {
    const cycleFrac = day / DAYS_PER_YEAR;
    const angleDeg = cycleFrac * 360;
    const radius = BASE_RADIUS + (cycle + cycleFrac) * RADIUS_PER_CYCLE;
    const angleRad = (angleDeg * Math.PI) / 180;

    const seasonal = 14 + 12.5 * Math.sin((2 * Math.PI * (day - 80)) / DAYS_PER_YEAR);
    const warming = cycle * 0.7; // slight multi-year warming trend, visible as outward color drift
    const noise = (nextRandom() - 0.5) * 3.2;
    const temperature = seasonal + warming + noise;
    minTemp = Math.min(minTemp, temperature);
    maxTemp = Math.max(maxTemp, temperature);

    const month = monthOfDay(day);
    const dayOfMonth = day - MONTH_STARTS[month] + 1;

    spiralPoints.push({
      x: radius * Math.sin(angleRad),
      y: radius * Math.cos(angleRad),
      temperature,
      label: `${MONTH_LABELS[month]} ${dayOfMonth}, ${START_YEAR + cycle}`,
    });
  }
}

// Core Highcharts has no colorAxis-to-point mapping (that composition ships in
// the heatmap/treemap modules, not core — see prompts/library/highcharts.md),
// so each marker's fill is computed by hand: a linear interpolation across the
// two-stop imprint_seq gradient, then assigned as a per-point `color`.
function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
const seqLow = hexToRgb(t.seq[0]);
const seqHigh = hexToRgb(t.seq[1]);
function valueToColor(value) {
  const frac = (value - minTemp) / (maxTemp - minTemp);
  const rgb = seqLow.map((c, i) => Math.round(c + (seqHigh[i] - c) * frac));
  return `rgb(${rgb[0]},${rgb[1]},${rgb[2]})`;
}
spiralPoints.forEach((p) => {
  p.color = valueToColor(p.temperature);
});

const backbone = spiralPoints.map((p) => [p.x, p.y]);

const cycleRadii = Array.from({ length: YEARS + 1 }, (_, k) => BASE_RADIUS + k * RADIUS_PER_CYCLE);
const monthAngles = MONTH_STARTS.map((d) => (d / DAYS_PER_YEAR) * 360);
const R_AXIS_MAX = cycleRadii[YEARS] * 1.15;

// Fixed margins so the plot area is exactly square inside the 1200x1200 CSS
// mount — required for the hand-drawn spiral to read as circular, not oval.
const MOUNT_SIZE = 1200;
const MARGIN_TOP = 100;
const MARGIN_BOTTOM = 140;
const MARGIN_SIDE = (MOUNT_SIZE - (MOUNT_SIZE - MARGIN_TOP - MARGIN_BOTTOM)) / 2;

// --- Chart -------------------------------------------------------------------
const title = "Daily Temperature 2021–2024 · spiral-timeseries · javascript · highcharts · anyplot.ai";

// Radial grid (month spokes + cycle-boundary rings), cycle-start labels, and
// the color legend bar — all drawn with the SVG renderer against the built
// chart, the idiom this codebase uses when core Highcharts has no built-in
// feature for it (see plots/heatmap-calendar/implementations/javascript/highcharts.js).
function drawSpiralGrid(chart) {
  const r = chart.renderer;
  const cx = chart.xAxis[0].toPixels(0, false);
  const cy = chart.yAxis[0].toPixels(0, false);
  const pxPerUnit = Math.abs(chart.xAxis[0].toPixels(1, false) - chart.xAxis[0].toPixels(0, false));
  const outerRingPx = cycleRadii[YEARS] * pxPerUnit;

  // Concentric rings — one per cycle boundary.
  cycleRadii.forEach((radius) => {
    r.circle(cx, cy, radius * pxPerUnit)
      .attr({ fill: "none", stroke: t.grid, "stroke-width": 1, zIndex: 1 })
      .add();
  });

  // Radial spokes + month labels — subdivisions within each cycle.
  monthAngles.forEach((angleDeg, i) => {
    const rad = (angleDeg * Math.PI) / 180;
    const sinA = Math.sin(rad);
    const cosA = Math.cos(rad);

    r.path(["M", cx, cy, "L", cx + outerRingPx * sinA, cy - outerRingPx * cosA])
      .attr({ stroke: t.grid, "stroke-width": 1, zIndex: 1 })
      .add();

    const labelPx = outerRingPx + 22;
    const align = sinA > 0.15 ? "left" : sinA < -0.15 ? "right" : "center";
    const dy = cosA > 0.5 ? -2 : cosA < -0.5 ? 12 : 5;
    r.text(MONTH_LABELS[i], cx + labelPx * sinA, cy - labelPx * cosA + dy)
      .attr({ align, zIndex: 2 })
      .css({ color: t.inkSoft, fontSize: "12px" })
      .add();
  });

  // Cycle-start markers — orient the viewer to where each revolution begins.
  for (let cycle = 0; cycle < YEARS; cycle++) {
    const ringPx = cycleRadii[cycle] * pxPerUnit;
    r.circle(cx, cy - ringPx, 4)
      .attr({ fill: t.ink, "stroke-width": 0, zIndex: 3 })
      .add();
    r.text(String(START_YEAR + cycle), cx + 9, cy - ringPx + 4)
      .attr({ align: "left", zIndex: 3 })
      .css({ color: t.ink, fontSize: "13px", fontWeight: "600" })
      .add();
  }

  // Color legend bar for the value-magnitude gradient.
  const barWidth = 220;
  const barHeight = 14;
  const x0 = chart.plotLeft + chart.plotWidth / 2 - barWidth / 2;
  const y0 = chart.plotTop + chart.plotHeight + 52;

  r.text("Daily Avg Temperature (°C)", x0 + barWidth / 2, y0 - 12)
    .attr({ align: "center" })
    .css({ color: t.inkSoft, fontSize: "14px", fontWeight: "600" })
    .add();
  r.rect(x0, y0, barWidth, barHeight, 3)
    .attr({
      fill: {
        linearGradient: { x1: 0, y1: 0, x2: 1, y2: 0 },
        stops: [
          [0, t.seq[0]],
          [1, t.seq[1]],
        ],
      },
      "stroke-width": 0,
    })
    .add();
  const fmtTemp = (value) => String(Math.round(value) || 0); // avoid a stray "-0"
  r.text(fmtTemp(minTemp), x0, y0 + barHeight + 16)
    .css({ color: t.inkSoft, fontSize: "12px" })
    .add();
  r.text(fmtTemp(maxTemp), x0 + barWidth, y0 + barHeight + 16)
    .attr({ align: "right" })
    .css({ color: t.inkSoft, fontSize: "12px" })
    .add();
}

Highcharts.chart(
  "container",
  {
    chart: {
      backgroundColor: "transparent",
      animation: false,
      style: { fontFamily: "inherit" },
      marginTop: MARGIN_TOP,
      marginBottom: MARGIN_BOTTOM,
      marginLeft: MARGIN_SIDE,
      marginRight: MARGIN_SIDE,
    },
    credits: { enabled: false },
    colors: t.palette,
    title: {
      text: title,
      style: { color: t.ink, fontSize: "17px", fontWeight: "600" },
    },
    xAxis: { min: -R_AXIS_MAX, max: R_AXIS_MAX, visible: false },
    yAxis: { min: -R_AXIS_MAX, max: R_AXIS_MAX, visible: false, title: { text: null } },
    legend: { enabled: false },
    tooltip: {
      backgroundColor: t.elevatedBg,
      borderColor: t.inkSoft,
      style: { color: t.ink, fontSize: "13px" },
      formatter() {
        return `<b>${this.point.label}</b><br/>${this.point.temperature.toFixed(1)}°C`;
      },
    },
    plotOptions: {
      series: { animation: false },
    },
    series: [
      {
        type: "line",
        name: "Spiral path",
        data: backbone,
        color: t.inkSoft,
        opacity: 0.35,
        lineWidth: 1.2,
        marker: { enabled: false },
        enableMouseTracking: false,
        showInLegend: false,
      },
      {
        type: "scatter",
        name: "Daily temperature",
        data: spiralPoints,
        marker: { radius: 2.6, states: { hover: { radiusPlus: 2.5 } } },
        showInLegend: false,
      },
    ],
  },
  function (chart) {
    drawSpiralGrid(chart);
  }
);
